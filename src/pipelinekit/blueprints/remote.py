"""Remote Blueprint Registry — search and install blueprints from a catalog.

ADR-019 / SPEC-016. A blueprint is **validated before it is written to disk**:
download → extract to a temp dir → schema-validate ``blueprint.json`` → verify the
required assets (Smell 15, lenient layout) → only then copy into ``blueprints/``.
If validation fails nothing is written (``PK-REGISTRY-002``).

Network access uses the standard library (``urllib``) — no new dependency. All
network calls go through ``_http_get`` so tests can mock them. Offline, a cached
catalog is used when present; with no cache the registry is unreachable
(``PK-REGISTRY-001``).
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pipelinekit.blueprints.validator import BlueprintValidator
from pipelinekit.core.errors import BlueprintError, RegistryError

REGISTRY_BASE_URL = "https://registry.pipelinekit.dev/v1"
CATALOG_URL = f"{REGISTRY_BASE_URL}/catalog.json"
CATALOG_CACHE_TTL_HOURS = 24

# Required blueprint assets (Smell 15), lenient layout: each entry passes if ANY
# of its candidate paths exists, so the standard (postgres/salesforce) and the
# AI-proposed (stripe: dbt/, root RUNBOOK.md, dbt/tests) layouts both validate.
_REQUIRED_ASSETS: list[tuple[str, list[str]]] = [
    ("blueprint.json", ["blueprint.json"]),
    ("ingestion", ["ingestion"]),
    ("transform", ["transform", "dbt"]),
    ("contracts", ["contracts"]),
    ("quality", ["quality", "dbt/tests"]),
    ("alerts", ["alerts"]),
    ("readme", ["docs/README.md", "README.md"]),
    ("runbook", ["docs/runbook.md", "RUNBOOK.md", "docs/RUNBOOK.md"]),
]


@dataclass
class CatalogEntry:
    """One blueprint as advertised in the registry catalog."""

    name: str
    version: str
    description: str
    source: str
    destination: str
    verified: bool
    verified_at: Optional[str]
    verified_by: Optional[str]
    downloads: int
    tags: list[str]
    url: str

    @classmethod
    def from_dict(cls, data: dict) -> "CatalogEntry":
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            source=data.get("source", ""),
            destination=data.get("destination", ""),
            verified=bool(data.get("verified", False)),
            verified_at=data.get("verified_at"),
            verified_by=data.get("verified_by"),
            downloads=int(data.get("downloads", 0)),
            tags=list(data.get("tags", [])),
            url=data.get("url", ""),
        )


@dataclass
class BlueprintCatalog:
    """The full registry catalog."""

    version: str
    updated_at: str
    blueprints: list[CatalogEntry] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "BlueprintCatalog":
        return cls(
            version=data.get("version", ""),
            updated_at=data.get("updated_at", ""),
            blueprints=[CatalogEntry.from_dict(b) for b in data.get("blueprints", [])],
        )

    def search(self, query: str) -> list[CatalogEntry]:
        """Return entries matching ``query`` by name, source, destination, or tag."""
        q = query.strip().lower()
        if not q:
            return list(self.blueprints)
        matches: list[CatalogEntry] = []
        for entry in self.blueprints:
            haystack = [
                entry.name.lower(),
                entry.source.lower(),
                entry.destination.lower(),
                *[t.lower() for t in entry.tags],
            ]
            if any(q in field_value for field_value in haystack):
                matches.append(entry)
        return matches

    def get(self, name: str, version: str | None = None) -> Optional[CatalogEntry]:
        """Return a specific blueprint by name and optional version."""
        candidates = [b for b in self.blueprints if b.name == name]
        if not candidates:
            return None
        if version is None:
            return candidates[0]
        for entry in candidates:
            if entry.version == version:
                return entry
        return None


class RemoteRegistry:
    """Fetches, caches, and installs blueprints from the remote catalog."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or (Path.home() / ".pipelinekit" / "cache")
        self.validator = BlueprintValidator()

    # -- catalog -------------------------------------------------------------

    def fetch_catalog(self, force_refresh: bool = False) -> BlueprintCatalog:
        """Return the catalog, using a fresh cache when available.

        Offline: falls back to any cached catalog (with a warning); raises
        ``RegistryError(PK-REGISTRY-001)`` only when there is no cache at all.
        """
        if not force_refresh:
            fresh = self._check_cache(CATALOG_CACHE_TTL_HOURS)
            if fresh is not None:
                return fresh
        try:
            raw = self._http_get(CATALOG_URL)
        except RegistryError:
            stale = self._read_cache()
            if stale is not None:
                print(
                    "⚠ Registry unreachable — using cached catalog.",
                    file=sys.stderr,
                )
                return stale[0]
            raise
        catalog = BlueprintCatalog.from_dict(json.loads(raw.decode("utf-8")))
        self._write_cache(catalog)
        return catalog

    def search(self, query: str) -> list[CatalogEntry]:
        """Search the catalog. Returns an empty list when nothing matches."""
        return self.fetch_catalog().search(query)

    # -- install -------------------------------------------------------------

    def install(
        self,
        name: str,
        version: str | None = None,
        cwd: Path | None = None,
        force: bool = False,
    ) -> str:
        """Download, validate, and write a blueprint. Returns the installed version.

        Raises:
            RegistryError: ``PK-REGISTRY-004`` if the blueprint is not in the
                catalog, ``PK-REGISTRY-005`` if the requested version is missing,
                ``PK-REGISTRY-003`` if already installed (without ``force``),
                ``PK-REGISTRY-002`` if the downloaded blueprint fails validation.
        """
        catalog = self.fetch_catalog()
        if not any(b.name == name for b in catalog.blueprints):
            raise RegistryError(
                "PK-REGISTRY-004", f"Blueprint not found in catalog: {name}", {}
            )
        entry = catalog.get(name, version)
        if entry is None:
            raise RegistryError(
                "PK-REGISTRY-005",
                f"Version not found for {name}: {version}",
                {"name": name, "version": version},
            )

        base = (cwd if cwd is not None else Path.cwd()) / "blueprints"
        target = base / name
        if target.exists() and not force:
            raise RegistryError(
                "PK-REGISTRY-003",
                f"Blueprint already installed: {name}. Use --force to overwrite.",
                {"name": name},
            )

        archive = self._download_archive(entry.url)
        with tempfile.TemporaryDirectory() as tmp:
            extract_dir = Path(tmp)
            self._extract(archive, extract_dir)
            root = self._find_blueprint_root(extract_dir)
            self._validate_blueprint(root)  # raises PK-REGISTRY-002 on failure
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(root, target)
        return entry.version

    # -- internals (mock seams) ---------------------------------------------

    def _http_get(self, url: str) -> bytes:
        """Fetch ``url`` and return the raw bytes. The network seam for tests."""
        try:
            with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
                return bytes(response.read())
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise RegistryError(
                "PK-REGISTRY-001",
                f"Registry unreachable: {url} ({exc})",
                {"url": url},
            ) from exc

    def _download_archive(self, url: str) -> bytes:
        """Download a blueprint zip archive."""
        return self._http_get(url)

    @staticmethod
    def _extract(archive: bytes, extract_dir: Path) -> None:
        """Extract a zip archive's bytes into ``extract_dir``."""
        import io

        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            zf.extractall(extract_dir)

    @staticmethod
    def _find_blueprint_root(extract_dir: Path) -> Path:
        """Return the directory containing ``blueprint.json`` within the archive."""
        if (extract_dir / "blueprint.json").is_file():
            return extract_dir
        for candidate in sorted(extract_dir.rglob("blueprint.json")):
            return candidate.parent
        # No blueprint.json anywhere — let validation surface PK-REGISTRY-002.
        return extract_dir

    def _validate_blueprint(self, root: Path) -> None:
        """Validate the extracted blueprint before any write (ADR-019).

        Raises ``RegistryError(PK-REGISTRY-002)`` if ``blueprint.json`` fails
        schema validation or any required asset is missing.
        """
        try:
            self.validator.validate(root)
        except BlueprintError as exc:
            raise RegistryError(
                "PK-REGISTRY-002",
                f"Blueprint validation failed: {exc.message}",
                {"detail": exc.message},
            ) from exc

        missing = [
            label
            for label, candidates in _REQUIRED_ASSETS
            if not any((root / c).exists() for c in candidates)
        ]
        if missing:
            raise RegistryError(
                "PK-REGISTRY-002",
                f"Blueprint is missing required assets: {', '.join(missing)}",
                {"missing": missing},
            )

    # -- cache ---------------------------------------------------------------

    def _cache_path(self) -> Path:
        return self.cache_dir / "catalog.json"

    def _check_cache(self, ttl_hours: int) -> Optional[BlueprintCatalog]:
        """Return the cached catalog if it is younger than ``ttl_hours``."""
        cached = self._read_cache()
        if cached is None:
            return None
        catalog, fetched_at = cached
        age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
        return catalog if age_hours < ttl_hours else None

    def _read_cache(self) -> Optional[tuple[BlueprintCatalog, datetime]]:
        """Return ``(catalog, fetched_at)`` from the cache file, or None."""
        path = self._cache_path()
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            fetched_at = datetime.strptime(
                data["_fetched_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
        except (OSError, ValueError, KeyError):
            return None
        return BlueprintCatalog.from_dict(data), fetched_at

    def _write_cache(self, catalog: BlueprintCatalog) -> None:
        """Persist the catalog with a fetch timestamp."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": catalog.version,
            "updated_at": catalog.updated_at,
            "blueprints": [vars(b) for b in catalog.blueprints],
            "_fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        self._cache_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")
