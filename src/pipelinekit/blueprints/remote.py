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
from pipelinekit.state import db

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
    changelog: dict = field(default_factory=dict)

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
            changelog=dict(data.get("changelog", {})),
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

    # -- version management (SPEC-018) --------------------------------------

    def version_status(self, cwd: Path | None = None) -> list[dict]:
        """Compare every installed blueprint against the registry catalog.

        Returns one dict per installed blueprint:
        ``{name, installed_version, registry_version, outdated}``. A blueprint
        absent from the catalog has ``registry_version=None`` and
        ``outdated=False``. Uses the cached catalog (24h TTL).
        """
        installed = db.get_installed_blueprints(cwd=cwd)
        by_name = {e.name: e for e in self.fetch_catalog().blueprints}
        statuses: list[dict] = []
        for row in installed:
            entry = by_name.get(row["name"])
            registry_version = entry.version if entry else None
            outdated = bool(
                registry_version and self._is_newer(registry_version, row["version"])
            )
            statuses.append(
                {
                    "name": row["name"],
                    "installed_version": row["version"],
                    "registry_version": registry_version,
                    "outdated": outdated,
                }
            )
        return statuses

    def outdated(self, cwd: Path | None = None) -> list[dict]:
        """Return only the installed blueprints with a newer registry version.

        Empty list when everything is current (SPEC-018).
        """
        return [s for s in self.version_status(cwd=cwd) if s["outdated"]]

    def upgrade(
        self,
        name: str,
        dry_run: bool = False,
        yes: bool = False,
        cwd: Path | None = None,
    ) -> str:
        """Upgrade a blueprint to the latest registry version. Returns it.

        Backs up the existing blueprint to
        ``.pipelinekit/backups/<name>-<version>/`` before writing the new one,
        validates the download (schema + required assets) before any write, and
        records the change in ``blueprint_versions``. ``yes`` is accepted for API
        symmetry; the confirmation prompt is the CLI's responsibility so the core
        stays non-interactive and testable.

        Raises:
            RegistryError: ``PK-REGISTRY-004`` if the blueprint is not in the
                catalog, ``PK-REGISTRY-006`` if already at the latest version,
                ``PK-REGISTRY-002`` if the download fails validation.
        """
        base = cwd if cwd is not None else Path.cwd()
        entry = self.fetch_catalog().get(name)
        if entry is None:
            raise RegistryError(
                "PK-REGISTRY-004",
                f"Blueprint not found in catalog: {name}",
                {"name": name},
            )

        current = self._installed_version(name, cwd)
        if current is not None and not self._is_newer(entry.version, current):
            raise RegistryError(
                "PK-REGISTRY-006",
                f"{name} is already at the latest version ({current}).",
                {"name": name, "version": current},
            )

        if dry_run:
            return entry.version

        target = base / "blueprints" / name
        backup_path: Path | None = None
        if target.exists():
            backup_path = self._backup_dir(base) / f"{name}-{current or 'unknown'}"
            if backup_path.exists():
                shutil.rmtree(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(target, backup_path)

        archive = self._download_archive(entry.url)
        with tempfile.TemporaryDirectory() as tmp:
            extract_dir = Path(tmp)
            self._extract(archive, extract_dir)
            root = self._find_blueprint_root(extract_dir)
            self._validate_blueprint(root)  # raises PK-REGISTRY-002 on failure
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(root, target)

        db.insert_installed_blueprint(
            entry.name,
            entry.version,
            entry.source,
            entry.destination,
            entry.verified,
            entry.url,
            cwd=cwd,
        )
        db.insert_blueprint_version(
            name,
            current,
            entry.version,
            "upgrade",
            str(backup_path) if backup_path else None,
            cwd=cwd,
        )
        return entry.version

    def rollback(
        self,
        name: str,
        version: str | None = None,
        cwd: Path | None = None,
    ) -> str:
        """Restore a blueprint from a local backup. Returns the restored version.

        With no ``version``, restores the most recent backup for ``name``.

        Raises:
            RegistryError: ``PK-REGISTRY-007`` if no matching backup exists.
        """
        base = cwd if cwd is not None else Path.cwd()
        backups = self._backup_dir(base)

        backup_path: Path | None = None
        if version is not None:
            candidate = backups / f"{name}-{version}"
            backup_path = candidate if candidate.is_dir() else None
        elif backups.is_dir():
            matches = sorted(p for p in backups.glob(f"{name}-*") if p.is_dir())
            backup_path = matches[-1] if matches else None

        if backup_path is None:
            raise RegistryError(
                "PK-REGISTRY-007",
                f"No backup found for {name}"
                + (f" v{version}" if version else "")
                + ". Upgrade creates a backup you can roll back to.",
                {"name": name, "version": version},
            )

        restored_version = (
            self._read_version(backup_path) or backup_path.name[len(name) + 1 :]
        )
        target = base / "blueprints" / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(backup_path, target)

        db.insert_blueprint_version(
            name,
            None,
            restored_version,
            "rollback",
            str(backup_path),
            cwd=cwd,
        )
        return restored_version

    # -- version helpers -----------------------------------------------------

    @staticmethod
    def _version_key(version: str) -> tuple[int, ...]:
        """Parse a dotted version into an int tuple for deterministic compare."""
        parts: list[int] = []
        for piece in str(version).split("."):
            digits = "".join(ch for ch in piece if ch.isdigit())
            parts.append(int(digits) if digits else 0)
        return tuple(parts)

    @classmethod
    def _is_newer(cls, candidate: str, current: str) -> bool:
        """Return True if ``candidate`` is a newer version than ``current``."""
        return cls._version_key(candidate) > cls._version_key(current)

    def _installed_version(self, name: str, cwd: Path | None) -> Optional[str]:
        """Resolve the installed version from state, falling back to disk."""
        for row in db.get_installed_blueprints(cwd=cwd):
            if row["name"] == name:
                return str(row["version"])
        base = cwd if cwd is not None else Path.cwd()
        return self._read_version(base / "blueprints" / name)

    @staticmethod
    def _read_version(blueprint_dir: Path) -> Optional[str]:
        """Return the ``version`` from a blueprint dir's ``blueprint.json``."""
        meta = blueprint_dir / "blueprint.json"
        if not meta.is_file():
            return None
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        version = data.get("version")
        return str(version) if version is not None else None

    @staticmethod
    def _backup_dir(base: Path) -> Path:
        """Return the project's blueprint backup directory."""
        return base / ".pipelinekit" / "backups"

    # -- internals (mock seams) ---------------------------------------------

    def _http_get(self, url: str) -> bytes:
        """Fetch ``url`` and return the raw bytes. The network seam for tests.

        Sends an explicit User-Agent: Cloudflare Pages returns HTTP 403 to
        requests with no User-Agent (urllib sends none by default), which would
        otherwise surface as a spurious ``PK-REGISTRY-001``.
        """
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "PipelineKit/1.0 (https://pipelinekit.dev)"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:  # noqa: S310
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
