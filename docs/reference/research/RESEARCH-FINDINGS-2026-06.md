# PipelineKit — Multi-Model Research Findings
## Answers to the 18-question research prompt, grounded in cited evidence

**Version:** 1.0
**Date:** June 28, 2026
**Owner:** Eddy Mkwambe + Command Center
**Method:** Parallel web research across 18 questions (dbt/Fivetran/JetBrains/Stack Overflow surveys, GitHub/PyPI analytics, vendor pricing pages, regulator documents, audit-firm and compliance-vendor material, ML/UX literature). Source URLs cited per question.
**Classification:** Internal — pipelinekit-internal

> **How to read this.** Each question gives a direct answer, flags uncertainty explicitly, and **disagrees with the founder's assumptions where the evidence warrants** — disagreement was the point of the exercise. Regulatory answers are **not legal advice** and require verification with qualified counsel. Where vendor pages or primary PDFs were blocked to automated fetch, findings rest on search-extracted snippets and are flagged accordingly.

---

## Headline disagreements (read first)

The research surfaced **seven assumptions that are wrong, shaky, or strategically misleading** and should change SPECs and positioning before design-partner outreach:

1. **"2-week setup tax" (R-001)** — not supported by any survey as a median. Reframe to the *defensible* claim: engineers spend **44–53% of their time** building/maintaining pipelines (Fivetran/Wakefield 2021; Fivetran 2026).
2. **"Pricing is the #1 Airbyte/Fivetran migration trigger" (R-003)** — pricing triggers *intent* but rarely *completes* migration; reliability + connector parity decide it. And the **dbt Labs + Fivetran merger (completed 1 June 2026)** is now the single biggest migration-intent catalyst in the market — the agenda doesn't mention it.
3. **"We only compete with doing it manually" (R-006)** — **Dagster Components/`dg` is a near-verbatim competitor** to the "installable EMS/blueprint" pitch, free and inside the orchestrator engineers already run.
4. **Soda as the quality layer (R-008)** — Soda is the *smallest* major option (~8–10× behind Great Expectations, ~30× behind dbt tests) and **just deprecated SodaCL** (v4 breaking change). Lead with dbt tests; make the layer backend-agnostic.
5. **Proprietary YAML contract format (R-009)** — the market consolidated onto **ODCS (Bitol/Linux Foundation)** in Dec 2025; the competing spec deprecated *into* ODCS. Proprietary is now a net liability.
6. **"43/43 dbt tests on synthetic seeds = verified" (R-011)** — that's a smoke test, not verification. dbt's own hub **explicitly refuses to certify packages**. Trust comes from coverage + real data + idempotency + CI + production history.
7. **Pricing: $99 Solo and no free tier (R-015)** — the entire substrate (dbt Core, dlt, Soda Core) is **free**. With no free tier there's no acquisition funnel. And **$299/mo/student for Academy (R-016) is ~7–12× market.**

---

# SECTION 1 — Market Reality Check

## Q1 (R-001) — The Setup Tax

**The "2 weeks" claim is not supported by any credible public survey as a measured median — treat it as an anecdote, not a benchmark, and reframe.**

- **Median/mean/outlier?** None — no major survey (dbt, Fivetran/Wakefield, Anaconda, Stack Overflow) measures "time to set up a pipeline before business logic." Vendor/practitioner blogs put a *simple* single-source pipeline at 1–2 weeks and *complex* multi-source pipelines at 4–8 weeks — a wide, complexity-driven distribution, the opposite of a stable median.
- **What the data *does* support:** engineers spend **44% of their time** building/maintaining pipelines (Fivetran/Wakefield 2021, n=300, independent fieldwork) rising to **53%** (Fivetran 2026, n=500+); dbt corroborates ~**56–57%** spend most time maintaining/organizing data, with **poor data quality the #1 challenge every year since 2022** (41%→57%).
- **% split (ingestion/transformation/quality/governance):** **no public survey breaks setup time into these buckets — flag as a genuine gap.** Closest proxy (Anaconda, data scientists not engineers): ~45% on data prep (cleansing ~26%, loading ~19%). Any 4-way split should be labeled unverified.
- **Dollar cost at $150/hr:** Literal reading of the claim = 2 wks × 80 hrs × $150 ≈ **$12,000/project/engineer** — but this rests entirely on the unverified "2 weeks." The defensible figure is **per-company-per-year**: ~**$520K** (2021) rising to ~**$2.2M** for large enterprises (2026).
- **Scales with team size?** **No — it's a largely fixed, per-pipeline / per-engineer-onboarded cost** (Fivetran sizes it per-pipeline at ~$1,600–1,900). It does *not* get cheaper as teams grow — which actually *strengthens* the product thesis.
- **Best citable source:** **Fivetran/Wakefield *State of Data Management* 2021** (disclose vendor interest) and **Fivetran 2026 benchmark**; **dbt State of Analytics Engineering** as the neutral corroborator.

**Recommended hero claim:** *"Independent surveys find data engineers spend 44–53% of their time building and maintaining pipelines rather than on differentiated analytics — a recurring, largely fixed per-pipeline cost sized at ~$520K/company/year (2021), ~$2.2M for large enterprises (2026)."*

Sources: fivetran.com/blog/data-management-survey · businesswire.com (Wakefield methodology) · fivetran.com/blog/the-enterprise-data-infrastructure-benchmark-report-2026 · getdbt.com/blog/state-of-analytics-engineering-2025-summary · hpcwire.com/bigdatawire (Anaconda).

## Q2 (R-002) — Who Actually Buys

**ICP-001 (solo/freelancer):** The individual *is* buyer, user, and approver — pure self-serve PLG. No procurement (stays under ~$5K; freelancers budget ~$200–500/mo for all software). Sales cycle: minutes–days. Proof: **a generous free trial/tier is the only proof that matters**; SOC 2 irrelevant. Top objection: *"Can I justify a recurring sub vs. DIY/free?"*

**ICP-002 (consultancy 2–10):** Founder/principal or lead engineer decides (1–2 person committee). Own purchase stays sub-~$15K (founder discretion); **security review hits via the *client's* deployment, not their own**. Cycle: ~2–6 weeks. Proof: trial on a real client project + ROI (hours saved/engagement) + **peer-consultancy references**; SOC 2 needed indirectly to clear clients' reviews. Top objection: *"Will this fit all our heterogeneous client stacks / can we pass through the cost?"*

**ICP-003 (internal team 5–50, enterprise):** **Buying committee of 5–10** — economic buyer = Head/VP Data; champion = senior/staff engineer (bottom-up trial); IT/security + procurement + finance gates. Thresholds (modal): ~$10K legal, ~$50K procurement, ~$250K CFO; **security review effectively mandatory above ~$25–50K**. Cycle: **3–6 months**, 6–12 at $100K+ ACV. Proof (all of): POC in their stack + **SOC 2 Type II** + security questionnaire + DPA + references + SSO/audit logs. Top objection: *"Why another layer on top of dbt/Snowflake/Soda — can't we build this ourselves?"* — plus process/budget-timing stalls (the real deal-killer).

**Strategic implication:** ICP-001/002 are trial-led self-serve lands; ICP-003 is land-and-expand won/lost on **SOC 2 Type II readiness, security-questionnaire speed, and a credible "why not build it" answer.** Confidence: sales-cycle/committee numbers high; procurement dollar thresholds are modal ranges, not canonical (medium).

Sources: optif.ai · growthspree · McKinsey PLG→PLS · Growth Unhinged/ICONIQ · Sprinto/Secureframe/Vanta (SOC 2 triggers) · Moxo/Brex (procurement thresholds).

## Q3 (R-003) — Airbyte/Fivetran Migration Trigger

**Your assumption is directionally right but misleading. Pricing opens the door; reliability + connector parity decide whether anyone walks through it.**

- **#1 trigger by tool:** For **Fivetran**, pricing dominates — its **March 2025 shift to per-connector MAR pricing** (deletes now billable, lost volume discounts) produced reported 70%–"more than double"–4–8× increases; on G2 ~35% of recent reviewers cite cost as the top con. For **Airbyte**, the #1 trigger is **reliability** (connector crashes/stalls, ~15–20% of beta-connector syncs needing manual intervention), with pricing secondary.
- **Critical context the agenda misses:** **dbt Labs + Fivetran merger completed 1 June 2026** (announced Oct 2025). The lock-in/consolidation fear is *currently the single largest migration-intent catalyst* across the dbt+Fivetran base.
- **% actively considering migration (mid-2026):** **No rigorous public survey exists.** Triangulated estimate: ~**20–35% of Fivetran customers** evaluating alternatives (elevated by the pricing change + merger). Do not put a precise number in a deck without caveating.
- **What stops completion:** the **"stay" math** — self-hosted Airbyte needs ~1–5 hrs/week maintenance (~$600–3,000/mo labor), often *more* than the Fivetran bill; **connector parity gaps** (a "good" 40-connector migration still left 3 fragile beta connectors needing manual restarts); historical-resync cost/risk; dbt refactoring; parallel-run burden.
- **Avg connector count for migrators:** no authoritative figure; case studies cluster **15–50** (pricing-driven migrators skew to the higher end).
- **Migration time without tooling:** **~2 weeks (simple) to ~12 weeks (complex)**, ~4–6 weeks central estimate for a 15–50-connector parallel-run cutover.
- **Best community source:** **r/dataengineering** (read the Oct-2025 merger megathread + "leaving Fivetran"/"Fivetran pricing" threads directly), paired with G2's structured complaint data. Run your own lightweight survey.

**Product implication:** the real opportunity (ICP-004) is **collapsing switching costs** (automated connector mapping, parity checking, backfill management, dbt-refactor assist, parallel-run validation) — more defensible than competing on price. Confidence: qualitative high, quantitative low (vendor-adjacent blogs; Reddit read secondhand).

Sources: weld.app · hevodata.com · definite.app · nexla.com · datacoves.com/post/dbt-fivetran · getdbt.com merger announcement · fivetran.com merger-completion press release · integrate.io · estuary.dev · metaops.solutions · g2.com.

## Q4 (R-004) — East African Data Engineering Market

**Training/web data on this region is genuinely thin — all headcounts are estimates (±~50%); no official "data engineer" count exists for any of these countries.**

- **Employed data engineers (estimates):** South Africa **5,000–9,000**; Nigeria **4,000–8,000**; Kenya **2,000–4,000**; Tanzania **300–800**. Method: 3–5% of professional-developer base (anchored on Google/Accenture Africa Developer Ecosystem 2021: ~716K African pros), cross-checked vs LinkedIn open reqs (SA ~953, Kenya ~554). **Caution:** the viral "3.7M developers / 1.1M on GitHub" figures are *GitHub account holders*, not employed engineers. A paid LinkedIn Talent Insights query is the only rigorous fix.
- **Dominant warehouses (qualitative, no measured share):** **BigQuery + Postgres-only lead; Snowflake trails** outside South Africa — driven by GCP's strong African startup presence, cost, and (until 2025) no local Snowflake region (which collides with data-residency rules). Your hypothesis holds, but it's structural inference, not a survey.
- **Typical fintech data team:** early-stage **0–2** (often zero pure data engineers); Series A–B **3–8** (1–3 DEs); scale-ups (Flutterwave/Moniepoint/OPay tier) **20–60+**. DE-to-analyst ratio ~1:2–1:3. No published benchmark — experience-based.
- **CBK / EA regulation:** see Q12 for detail. Headline: **Kenya DPA 2019 s.50 one-copy-in-Kenya residency**, cross-border transfer restrictions, CBK 24-hour incident reporting; equivalents in Tanzania (PDPA 2022 + PDPC permit to export), Nigeria (NDPA 2023 + CBN/BVN localization), South Africa (POPIA + SARB).
- **PPP-adjusted pricing:** price-level ratio ≈ **0.38 for Kenya, ~0.20 for Nigeria** (post-naira-float, volatile). Strict PPP would put $99→~$38 (KE)/~$20 (NG), but **funded fintechs/banks pay closer to global** — recommend **40–60% of US list** for enterprise, deeper only for SMB/individual tiers, with geo-gating against arbitrage.
- **Communities (active):** Nairobi — **AI Kenya**, AfterWork Data Science, WiMLDS, Nairobi AI. Lagos — **Data Science Nigeria (~14K, not 600K)**, ODSC Lagos, Data Community Africa/DataFest. Dar — **Tanzania Data Lab (dLab)** (materially smaller).

Sources: blog.google (Africa Developer Ecosystem) · LinkedIn jobs · snowflake.com · CBK/ODPC PDFs · indexmundi PPP · kenya.ai · datasciencenigeria.org · dlab.or.tz.

---

# SECTION 2 — Competitive Landscape

## Q5 (R-006) — True Competition

**The "we only compete with doing it manually / we complement everything" framing is the weakest part of the thesis. Disagree.**

- **More-direct competitors the framing minimizes:** (1) **Dagster Components + `dg` CLI (2025)** — "reusable, configurable building blocks" + YAML DSL + `dg scaffold`, letting platform teams "standardize best practices by authoring reusable Components." That is *almost verbatim* the "installable EMS/blueprint" pitch — free, OSS, inside the orchestrator. (2) **dbt Mesh** — owns transformation-layer governance. (3) **Datacoves** (managed dbt+Airflow platform, ~50% lower TCO claims) and **Y42** (live, ~$13.7M rev/~50 customers — *not* defunct) — head-on "stop doing it manually" competitors.
- **Dagster overlap:** asset-based orchestration *is* a coordination layer; Components = native blueprint mechanism; **Embedded ELT/Sling + dlt** pulls ingestion in; **Dagster+** adds catalog/observability/alerts. Dagster already orchestrates, standardizes, ingests, and observes.
- **dbt Cloud governance boundary:** dbt governs *dbt models only* — model contracts (build-time **column names/types only**; not_null/PK not truly enforced on warehouses), model access/groups, Mesh, Catalog. **PipelineKit's whitespace = the end-to-end, cross-tool pipeline contract (ingest→transform→test→observe)** that dbt doesn't span. But for a dbt-only shop, dbt already covers ~70% of governance and PipelineKit's edge shrinks.
- **Monte Carlo overlap:** ML/agentic anomaly detection (freshness/volume/schema), incident lifecycle, field-level lineage. PipelineKit's Soda-based "Observability Management System" is *declarative checks*, not learned baselines — **position as "versioned in-repo quality contracts," not a Monte Carlo replacement.**
- **Top 5 "just use Dagster" objections:** (1) Dagster's asset graph *is* the coordination layer; (2) Components/`dg` already ship free reusable blueprints; (3) Embedded ELT + Dagster+ already cover ingestion/observability; (4) new abstraction/DSL/lock-in + another vendor vs OSS+community; (5) Dagster/dbt are adding their own AI scaffolding — what's durable?
- **Existing registries:** crowded at the *single-tool* level (dbt Package Hub, Dagster Components, Airbyte 600+ connectors, Meltano Hub 500+, dlt Hub verified sources, Coalesce) but **empty at the end-to-end cross-tool blueprint level** — genuine whitespace. **Caution:** template registries historically drive adoption, not revenue (dbt Hub/Meltano Hub are free); and Dagster is closing on this from the orchestrator side.

**Honest positioning:** "We compete with the *roadmaps* of Dagster and dbt Labs, and with internal platform teams. Our wedge is a polished cross-tool, AI-native, version-controlled blueprint layer neither has shipped *yet* — defensible only on execution speed."

Sources: dagster.io/blog (Components) · github.com/dagster-io discussions/28472 · docs.getdbt.com/docs/mesh · montecarlo.ai/platform · datacoves.com · getlatka.com/companies/y42 · airbyte.com/connectors · meltano.com · hub.getdbt.com.

## Q6 (R-007) — dlt Ecosystem

**Net positive bet but a real, named single-vendor dependency risk — not a clean "strategic asset."**

- **Adoption (GitHub-verified):** **5,523 stars**, ~194 contributors, latest v1.28.1 (Jun 2026), rapid release cadence. **Downloads** ~9–11M/mo (self-reported/clickpy; up from 3M/mo at Aug-2025 funding — ~3× in <1 yr, but downloads ≠ users; inflated by CI). Slack ~2,200; dltHub self-reports 5,000+ companies.
- **Awareness vs production use:** no survey names dlt (dbt's survey lists Fivetran/Airbyte/Stitch, *not* dlt). **Estimate (low confidence): ~25–40% aware, ~3–8% production.** Disagree with treating dlt as a mainstream/default — it's early-majority-at-best, niche-popular.
- **Top complaints affecting blueprint reliability:** (1) **state-table fragility** (`_dlt_pipeline_state` bloat can break the environment); (2) **incremental-load duplicates** on partial state-write failure; (3) **schema-evolution quirks** (type changes spawn "variant" columns rather than promoting); (4) OOM on large extracts; (5) normalize-step throughput; (6) **`append` default footgun** (re-runs double-load). PipelineKit should pin/override state management, write-disposition, and schema-contract mode rather than inherit defaults.
- **Top sources:** the 3 generic core sources dominate — **`sql_database`, `rest_api`, `filesystem`** — then GitHub, Slack, Notion, HubSpot, Salesforce, Stripe, Shopify (positions 4+ directional; dltHub publishes no per-source counts).
- **Strategic verdict:** keep dlt (momentum + Apache license) but **mitigate the seed-stage single-vendor risk** (dltHub ~$14M raised, Bessemer-led $8M Aug 2025): pin versions, own a hardened wrapper, avoid coupling to hosted Pro, keep an abstraction boundary so ingestion could be swapped. Re-evaluate at dltHub's next funding event.

Sources: api.github.com/repos/dlt-hub/dlt · dlthub.com/blog · clickpy.clickhouse.com · getdbt.com survey · bvp.com/crunchbase/tracxn (funding).

## Q7 (R-008) — Quality Layer Choice

**Soda is the smallest major option and just made a breaking pivot. Do NOT hard-commit to Soda — build a backend-agnostic interface and lead with dbt tests.**

- **Adoption ranking:** (1) **dbt tests** (dbt-core ~107M downloads/mo) — by far most-used DQ mechanism; (2) **Great Expectations** (11.6k stars, ~30M/mo) — largest dedicated framework; (3) **Soda Core** (2.4k stars, ~3.7M/mo) — credible niche, **not** a leader; (4) Elementary (dbt-native observability, different category); (5) custom/in-house. **GX is ~8–10× Soda; dbt tests ~30× Soda.**
- **GX→Soda friction:** real — GX is Python-first (Suites/Checkpoints), Soda is YAML-first (scans/checks→v4 contracts). Soda is generally *simpler* (friction is "where's my Python escape hatch"), but **SodaCL itself is now a moving target.**
- **Recommendation:** define an internal `QualityCheck` abstraction over the 5 canonical checks and compile to backends. **Priority backend = dbt tests** (largest base, lowest friction). Keep Soda as pluggable but **target Soda v4 Data Contracts, not deprecated SodaCL**; optionally GX. Avoid any hard Soda Cloud dependency. Three reasons against Soda-only: **(a) Soda v4 deprecates SodaCL (breaking)**; (b) Soda Core funnels to paid Cloud (3-dataset free tier); (c) the market's center of gravity is dbt+GX, **now both under Fivetran** (Fivetran became GX Core steward May 2026; merged with dbt June 2026).
- **Top 5 production checks:** uniqueness/PK · null/not-null (completeness) · freshness · volume/row-count · schema + referential integrity. (These map to dbt's canonical `unique`/`not_null`/`accepted_values`/`relationships` + source freshness — portable across all backends.)
- **Security note:** the `elementary-data` PyPI package was compromised (2025–26 infostealer) — relevant if Elementary is ever a backend.

Sources: clickpy dashboards · github.com (soda-core/great_expectations/elementary) · getdbt.com/blog/data-quality-checks · soda.io/blog/introducing-soda-4.0 · businesswire (Fivetran/GX + dbt merger) · snyk.io/bleepingcomputer (Elementary CVE).

---

# SECTION 3 — Technical and Standards

## Q8 (R-009) — Data Contract Standards

**The market consolidated onto ODCS in Dec 2025. A proprietary YAML format is now a net liability — be ODCS-compatible at the boundary.**

- **ODCS adoption:** **v3.1.0 (8 Dec 2025)**, maintained by the **Bitol project under the Linux Foundation AI & Data** (Apache 2.0, ~1,000+ stars, OpenSSF badge). Descends from **PayPal's** data-contract template (strongest production pedigree). **Convergence event:** the competing Data Contract Specification (datacontract.com) was **deprecated into ODCS**, and **datacontract-cli switched to ODCS as default.** (No public end-user adopter roster beyond PayPal — "hundreds of orgs" is Bitol-stated.)
- **ODCS vs dbt vs Soda — three layers, not competitors:** dbt contracts enforce **column names/types at build time only** (not_null/check enforced only post-build; PK/uniqueness *unenforceable* on Snowflake/BigQuery); Soda runs **runtime quality checks against real data**; ODCS is the **declarative agreement** (schema + quality + SLA + ownership + servers). Clean architecture: **ODCS defines → dbt guards schema in-DAG → Soda/GX enforce quality at runtime.**
- **Should PipelineKit be ODCS-compatible?** **Yes.** datacontract-cli already exports one ODCS file to dbt, SodaCL, GX, Avro, Protobuf, JSON Schema, SQL DDL, Terraform + JUnit-XML for CI — emit ODCS and inherit that ecosystem for free. Use ODCS's **Custom Properties** to extend (AI-blueprint provenance, orchestration hints) rather than fork. Posture = **"ODCS-superset," not "ODCS-replacement."** (GoCardless's proprietary "Utopia" is the cautionary precedent.)
- **Top 5 enforced fields:** schema/column presence + types · nullability · uniqueness/PK integrity · freshness/SLA · row-count/volume. **Note: PK and freshness are aspirational at the contract/build layer and only real at the runtime layer** — encode that distinction so you don't promise enforcement you can't deliver.
- **Most common violations:** schema drift (dominant) · type changes · nullability violations · freshness failures · volume anomalies. The most dangerous class is **silent "green-but-wrong" degradation** — pair structural contracts with runtime observability.
- **ODPS note:** the Open Data Product Specification (v4.1, sibling Bitol standard) describes the *product* and *embeds* an ODCS/DCS contract — relevant only if PipelineKit later markets data *products*.

Sources: github.com/bitol-io/open-data-contract-standard · bitol.io (v3.1.0) · datacontract.com · github.com/datacontract/datacontract-cli · docs.getdbt.com/docs/mesh/govern/model-contracts · docs.soda.io · opendataproducts.org.

## Q9 (R-011) — Blueprint Verification Standards

**"43/43 dbt tests on synthetic seeds, locally, in 1 minute" is a smoke test, not verification — and presenting it as strong proof is misleading. Disagree.**

- **Why the metric is weak:** test *count* lacks coverage context (43 trivial `not_null`/`unique` assertions can coexist with zero coverage of what matters); **author-written synthetic seed + author-written assertions = a closed loop** proving internal consistency, not real-world correctness; dbt's own guidance is that tests validate assumptions against *real production data, continuously*.
- **Better trust standards (priority):** (1) **coverage, not count** (% of critical models/KPIs tested across layers); (2) **real-data validation** (production-shaped, not author seeds); (3) **idempotency/reproducibility** (N runs → identical output; safe retries/backfills); (4) **production run history** (green scheduled runs, incident rate, MTTR); (5) **CI signals** (green in CI against a warehouse on PRs, not a laptop).
- **What earns CLIENT-project trust:** active maintenance/recent commits · clear docs with runnable examples · low coupling (utilities, not a forced framework) · performance at scale (10M rows, not 10K seed) · **tested on the client's actual data before deploy.**
- **Certification reality:** **there is no formal certification for dbt packages — dbt's hub hosts them "as a courtesy" and explicitly "does not certify or confirm the integrity, operability, effectiveness, or security of any Packages."** The closest real rubric is the **Trusted Adapter Program** (shared test suite `tests.adapter.basic`, ongoing maintainer duties, **revocation rights**) and **`dbt_project_evaluator`** (best-practice audit).
- **What PipelineKit should build:** adopt the **Trusted-Adapter *model*** (recurring status + shared real-data test harness + revocation), not a test-count badge; be honest like dbt's disclaimer; ship a **blueprint scorecard** (coverage %, conformance, docs, perf, version compat, real-vs-synthetic-data flag); standardize a **shared integration-test harness** across blueprints; expose **explicit trust tiers** — Tier 0 "smoke-tested on synthetic seeds" (where 43/43 belongs) → Tier 1 "validated on real client-shaped data, idempotent, green in CI" → Tier 2 "N production runs, zero incidents." **Do not lean on GitHub stars** (documented ~6M fake stars; "reputation-as-a-service" economy).

Sources: hub.getdbt.com · docs.getdbt.com/docs/build/packages · docs.getdbt.com/docs/trusted-adapters · docs.getdbt.com/blog/align-with-dbt-project-evaluator · airbyte.com/prefect.io (idempotency) · arxiv.org/html/2412.13459v2 (fake stars).

## Q10 (R-012) — AI Diagnosis Accuracy

**No credible adjacent tool leads with a bare 0.00–1.00 number. Don't make the raw score the headline — lead with evidence, bucket the headline, rank hypotheses, and abstain when uncertain.**

- **Trusted threshold:** task-dependent and **calibration-dependent**, not a fixed 0.8. Shipped patterns cluster on two ideas: a *high* bar to trigger automation and a *low-confidence discard* below which results are hidden. Concrete: **Sentry AI Code Review discards low-confidence/low-severity findings** (0.000–1.000 scale, 1.0 = guaranteed crash); **incident.io reports a ~65% confidence inflection** where suggestions become net-useful; **Cleric withholds findings until confident.** An *uncalibrated* score actively erodes trust the first time a "0.95" is wrong.
- **How to present it (in trust-priority order):** (1) **calibrate first, display second**; (2) **lead with the plain-language diagnosis + evidence**, decimal on drill-down only (progressive disclosure beats a bare number — avoids automation bias *and* algorithm aversion); (3) **show the reasoning/evidence chain** — the single biggest trust lever (Datadog Bits' observe→hypothesize→validate/invalidate loop with supporting evidence); (4) **ranked hypotheses with relative likelihood** (PagerDuty Probable Origin: top-3 candidates each with a % likelihood); (5) **bucket the headline** High/Med/Low (Sentry Seer Actionability), decimals for power users; (6) **abstain explicitly** — mark "inconclusive" (Datadog's validated/invalidated/inconclusive; Cleric withholds). An honest "not enough signal" raises trust more than a confident wrong answer.
- **Hardest-to-diagnose failure patterns (lower confidence / prefer abstention here):** (1) **silent "green-but-wrong" degradation** (no log trace, no exception — AI has nothing to latch onto; canonical example: a renamed source column defaulting to 0, "succeeding" green for a week); (2) **data-content vs infrastructure ambiguity**; (3) **schema drift with downstream cascade** (proximate break ≠ true origin); (4) **freshness/late-arriving** (wrong, or just not here yet?); (5) **intermittent/non-deterministic/multi-cause** (self-resolving, retries mask root cause).
- **DiagnosticsEngine recommendations:** don't headline the raw 0.00–1.00; bucket it; always render the reasoning chain; present ranked hypotheses with likelihood; add and *use* an "inconclusive/need-more-signal" state for the hard classes; **track displayed-confidence vs actual-accuracy and prove calibration**; gate automation by a high calibrated threshold (suggest-only below it).

Sources: docs.sentry.io/product/ai-in-sentry/seer · datadoghq.com/blog/bits-ai-sre-deeper-reasoning · docs.datadoghq.com/bits_ai · support.pagerduty.com/main/docs/probable-origin · docs.incident.io/investigations · cleric.ai / resolve.ai (secondhand) · smashingmagazine.com (trust UX) · arxiv.org/pdf/2402.07632 (miscalibrated confidence).

---

# SECTION 4 — Regulatory Compliance

> **Not legal advice — verify with qualified counsel per jurisdiction.**

## Q11 (R-013) — SOC 2 Pipeline Requirements

- **Applicable TSC:** Security **CC-series is mandatory**; **Availability (A1)** is the most relevant add-on for an infra/pipeline vendor; Confidentiality (C1) if handling classified customer data. Pipeline mapping: **CC6.1–6.8** (logical access — warehouse RBAC, MFA, encryption at rest/in transit, egress control, key management) — *the core surface*; **CC7.1–7.5** (system ops/monitoring — security event & anomaly detection → maps to pipeline observability/audit logs); **CC8.1** (change management — satisfied via Git PR approvals, protected branches, CI, author/approver separation); **A1.1–1.3** (capacity, backup, **restore testing**); **CC9.2** (vendor/third-party risk for your data tools).
- **Evidence auditors request (Type II = samples across a 3–12-mo window):** IdP auth logs + **quarterly access reviews** with sign-off + warehouse grant lists + deprovisioning tied to HR dates; **~20–40 sampled deployments each traced to a PR** (independent approver, passed CI, deployed after approval — *Slack approvals don't pass*); encryption config (TLS 1.2+, AES-256, KMS rotation); centralized logging/alerting with documented reviews; backup + **restore-test** evidence; subprocessor inventory + their SOC 2s.
- **Most-failed family: CC6 (Logical Access).** Defensible data — **CBIZ 2024 SOC Benchmark (193 reports):** 54.9% had ≥1 exception; top causes business approvals/reviews 16.5%, **user access reviews 15.6%** (now the #1 driver of qualified opinions), terminations/deprovisioning 12%, change management 11.7%. Data engineering clusters here because access reviews/deprovisioning are manual and **pipeline service accounts/non-human identities are frequently un-reviewed.** (The viral "68% from CC6" stat lacks a traceable dataset — directional only.)
- **Evidence tools:** Vanta (broadest integrations, native Snowflake), Drata (deeper CI/CD), Secureframe; Tugboat Logic absorbed into OneTrust. **Gap = none understand data-pipeline semantics** (dbt model changes as changes, Soda checks as monitoring evidence, connector access, lineage) — PipelineKit's differentiated wedge.
- **Minimum viable for a security questionnaire:** **SOC 2 Type II scoped to Security, ≥3-month window** (Type II strongly preferred over Type I; ~$15–50K, ~4–5 months). Add Availability for a pipeline vendor. A current Type II pre-answers ~40–60% of a standard SIG/CAIQ. **Forward flag:** SOC 2 Type II is now a baseline not a differentiator; questionnaires increasingly add an AI-governance module (ISO 42001 / NIST AI RMF).

Sources: secureframe.com/linfordco/drata (TSC) · cbiz.com 2024 SOC Benchmark · vanta.com/drata.com · vanta.com/resources (questionnaires).

## Q12 (R-014) — CBK & East African Regulatory Requirements

- **Kenya — pipeline-relevant rules:** **CBK Guidance Note on Cybersecurity for the Banking Sector (2017)** (data governance/classification; internal-audit assessment; **24-hour incident reporting** + quarterly reports; third-party/cloud outsourcing expectations); **CBK Prudential Guideline on Outsourcing (CBK/PG/16)**; **Kenya Data Protection Act 2019 + ODPC** (DPIAs, breach notice, fines up to **KES 5M or 1% turnover**); **CBK Digital Credit Providers Regs 2022** (data-protection policies, API data submission to CBK).
- **Data residency:** **DPA 2019 s.50 — at least one serving copy of personal data must be stored on a server/data centre in Kenya** (conditional localization, not a blanket offshore ban). The Cabinet Secretary may mandate full in-Kenya processing on "strategic interest of the state / protection of revenue" grounds. Cross-border transfer needs **adequate safeguards** (SCCs/BCRs/adequacy/consent; **sensitive data requires explicit consent**). *A Kenyan fintech on offshore Snowflake likely needs a Kenya-resident copy + a documented transfer mechanism — verify with counsel.*
- **Audit trails:** Data Protection (General) Regulations 2021 explicitly name **"audit trails and event monitoring"** as required controls; mandatory **retention schedules with periodic audit**; controller–processor contracts must include audit/inspection rights; CBK layers 24-hour/quarterly incident reporting. (No single uniform statutory log-retention period found — sector/purpose-driven; thin, verify.)
- **Peer markets (personal-data transfer is conditional everywhere; the hard residency comes from the central banks):**
  - **Tanzania** — PDPA 2022 + PDPC; cross-border export needs a **PDPC permit** (Reg. 20). The binding residency layer is **BOT's payment-systems rule (Reg. 43): payment-system data's primary data centre must be IN Tanzania**; a 2025 BOT Cloud Computing Guideline would force mission-critical banking/payment systems in-country (in-force vs. draft status disputed — verify).
  - **Nigeria** — NDPA 2023 + NDPC (GAID 2025); NDPA s.41 adequacy-based transfer (no general localization). **NEW & material: a CBN circular dated 15 June 2026 mandates that payment-transaction data generated in Nigeria be stored and managed in Nigeria from 1 January 2027** (banks, MMOs, switches, PTSPs/PSSPs, super agents; cloud only with in-country residency). Plus existing CBN Risk-Based Cybersecurity Framework and **BVN data localization**. *This 2027 mandate is ~2 weeks old as of this writing — verify the raw CBN circular.*
  - **South Africa** — POPIA s.72 conditional transfer (no general localization); National Data & Cloud Policy localizes *government* data only; SARB Directive 3/2018 + Joint Standard 2/2024 impose "regulatory access" / cyber-resilience expectations.
- **Card data (region-wide):** **PCI DSS v4.0.1** (only active version since 1 Jan 2025) is mandatory for anyone touching cardholder data, via card-scheme/acquirer contracts — Req. 3 (render stored PAN unreadable) and **Req. 10 (log all access; ≥12-month retention, 3 months immediately available)** are the binding pipeline controls, independent of jurisdiction.
- **Most relevant frameworks:** **ISO 27001 + PCI DSS are the partner/regulator baseline** in the region (PCI-DSS mandatory for cardholder data, referenced by CBN); **SOC 2 Type II is the cross-border/enterprise requirement.** Architect a **multi-framework control mapping** (one control → SOC 2 + ISO 27001 + local reg).

**Product scoping:** CM-5's binding, codifiable obligations are **DPA s.50 one-copy residency, 2021-Regs audit-trail + retention schedules, CBK 24-hour/quarterly incident reporting, and CBK/PG/16 outsourcing controls.** A compliance package that misstates these destroys trust permanently — verify every line with Kenyan counsel.

Sources: centralbank.go.ke PDFs · odpc.go.ke (General Regs 2021, DCP guidance) · new.kenyalaw.org (DPA) · itif.org (cross-border analyses) · cert.gov.ng (NDPA) · cbn.gov.ng (cyber framework) · michalsons.com (POPIA) · fpf.org (Tanzania PDPA).

---

# SECTION 5 — Pricing and Business Model

## Q13 (R-015) — Pricing Benchmarks

- **Vs comparables:** dbt Cloud (Developer **free** / Starter **$100/seat** / Enterprise custom ~$200–400/seat); Dagster+ (Solo **$10/mo** + credits / Starter $100 / Pro custom); Prefect (Hobby **free** / Starter $100 / Team $400); Monte Carlo (no list; ACV **$25–50K/yr**); Soda (free tier + Core OSS / Team **~$750/mo** / Enterprise custom).
  - **Solo $99/mo is too high** — every comparable entry point is free ($0: dbt Developer, Prefect Hobby, Soda Free) or $10–100. Weakest-value tier in the lineup.
  - **Team $499/mo (~$100/seat) is well-calibrated** — on dbt Starter, above Prefect Team; room to raise.
  - **Enterprise $2,500+/mo ($30K+/yr) is squarely in-market** (Monte Carlo $25–50K; dbt enterprise $36–84K/yr).
- **5-person team tooling budget:** ~$6–30K/yr *per category* (orchestration $6–12K; quality/observability $9–30K). Team at $5,988/yr sits at the bottom — comfortably manager-approvable.
- **Best-converting model:** **hybrid (per-seat for collaboration/registry/governance + a usage meter** for pipelines/runs/agent-actions) — the pattern dbt and Dagster converged on. ~72% of successful dev-tool companies started with a generous free/OSS tier (Redpoint via daily.dev).
- **Solo "manager approval" — false premise:** a solo consultant *is* the approver. The real gate is the **reflexive self-expense ceiling (~$50–150/mo)** and ROI; $99 sits at the top of that band against free alternatives.
- **EA PPP:** ~0.38 (KE) is roughly right; Nigeria volatile. Ship **"PPP-lite" (~50–60% of US list)** with geo-gating, not strict 0.38.
- **Freemium — the biggest gap:** **the substrate (dbt Core/dlt/Soda Core) is all $0**, so "why pay $99?" is fatal with no on-ramp. **Add a free Community tier (1 user, public registry, capped usage); drop/reposition $99 Solo to ~$29–49 Pro.** Monetize on private registries, SSO, SLA, collaboration — what OSS can't give a team.

Sources: getdbt.com/pricing (+Vendr) · dagster.io/pricing · prefect.io/pricing · montecarlodata.com (Vendr) · soda.io/pricing · daily.dev (dev-tool pricing).

## Q14 (R-016) — Academy Pricing

- **Vs comparables:** DataCamp **$25–42/mo**; Pluralsight **$29–45/mo**; Coursera Plus **$59/mo**; **dbt Learn free + cert $200**; Udemy ~$10–150/course; Maven cohorts **$500–3,000** total.
- **$299/mo/student is ~7–12× market — cut it.** At $3,588/yr it exceeds a *live Maven cohort with a human instructor*. **Reframe the unit:** a **one-time ~$299 cohort/bootcamp price** works; a **$29–49/mo** individual plan matches the category; or **free courses + paid cert (~$150–250)** mirroring the proven dbt Learn model.
- **University $5–25K/semester:** plausible but at the *upper* edge for one tool; **lead academic GTM with free/discounted licenses + turnkey course materials** (the GitHub/JetBrains/Snowflake playbook) to win curriculum placement — charging up front prices you out of the hiring-pipeline moat.
- **Corporate $10–50K/cohort:** in-range — ~$1,000/head across 10–50 maps to L&D benchmarks (avg ~$874–902/employee/yr; financial services ~$1,097).
- **University adoption evidence needed:** the tool appears in **real job postings** (strongest signal) + free access + turnkey labs + a credential + peer-institution adopters.
- **Most-valued certs:** AWS data certs (broadest demand) · GCP Professional Data Engineer (highest salaries) · Databricks Data Engineer · Snowflake SnowPro · dbt Analytics Engineering ($200). **A standalone PipelineKit cert has near-zero market value today — align/partner with an existing recognized cert rather than compete.**

Sources: datacamp.com/pluralsight.com/coursera.org pricing · getdbt.com/certifications · maven.com · trainingmag.com 2025 report · dataquest.io/dataengineeracademy (cert value).

---

# SECTION 6 — User Experience

## Q15 (R-017) — CLI vs GUI

- **No survey supports a clean "CLI vs GUI %" — don't cite one.** Stack Overflow 2024 (n=65,437): **VS Code ~73.6%** is the dominant environment — an *editor with an integrated terminal*, neither pure CLI nor hosted GUI. dbt/JetBrains surveys publish no CLI-vs-GUI split. **Reframe the axis: the real question is "raw CLI vs CLI-inside-an-editor," and the market has moved to the editor.**
- **Preference-shift team size:** ~**8–10 people** (practitioner-inferred, medium confidence) — but the true driver is **role heterogeneity** (when non-CLI-native analysts must contribute), not raw headcount.
- **Daily CLI tools:** git, dbt, **uv/poetry** (uv now the recommended path in Meltano + dbt DuckDB quickstart), docker, terraform, Airflow CLI, DuckDB. The audience lives in the terminal — they'll expect a new CLI to compose cleanly with this stack.
- **VS Code extension — highest-leverage bet, table stakes not a "GUI compromise":** the dbt ecosystem converged on VS Code (community **dbt Power User by Altimate** + the **official dbt Labs extension on the Fusion engine**, also targeting Cursor/Windsurf). The category leader is investing in the *editor*. CLI = engine; extension = distribution channel.
- **Risk of CLI-only for ICP-002:** **moderate-to-high and asymmetric** — safe for the *builder* engineers (CLI-native), risky at the **analyst-collaborator and client-handoff seams**, and ICP-002's 2–10 size straddles the ~8–10 shift band. A read/preview/lineage VS Code surface directly addresses the handoff risk.

Sources: survey.stackoverflow.co/2024 · visualstudiomagazine.com · getdbt.com survey · datacoves.com (dbt Core vs Cloud) · github.com/AltimateAI/vscode-dbt-power-user · docs.getdbt.com/docs/about-dbt-extension.

## Q16 (R-018) — First 10 Minutes

- **10 minutes is realistic *only* with a no-credentials, local-engine, seeded, single-command first run — and even then it's unambitious.** Existence proof: dbt's **`jaffle_shop_duckdb`** — *"from `git clone` to `dbt docs serve` in less than 1 minute, for free,"* 28 SQL ops in <1s, **no warehouse, no credentials** (local DuckDB + bundled seeds). With *any* external warehouse/credential step, 10 minutes is unrealistic.
- **Comparable time-to-value:** dbt+DuckDB ~2–5 min (no creds); dbt+Snowflake **30 min–hours** (creds in path); dlt local DuckDB ~5–15 min; Meltano **15–45+ min** (needs *two* credential sets); Prefect local ~5–10 min; Airbyte substantially longer. **Pattern: every tool that hits <10 min defaults to a local engine + seed data + zero credentials.**
- **Most common failure points:** (1) **credentials/auth** (#1 killer); (2) warehouse/destination connection (roles/grants/`profiles.yml`); (3) **Python env/dependency hell** (why the ecosystem moved to uv); (4) **missing source data** (winners ship seeds); (5) version mismatches.
- **Ideal first-run:** no external creds (local embedded engine) · bundled sample data · **one command** to value (not Meltano's init→add→config→add→config→run chain) · uv-based setup · **a clear inspectable result + obvious next step.**
- **What "success" should mean:** **not "exit 0" — a verified, understood result (an "aha")**, like jaffle_shop ending at `dbt docs serve` where you *see* the lineage. DX literature: aim for an aha within ~5 min (top PLG tools 2–3 min). **Disagree with the 10-minute target itself — dbt does <1 min; aim for first successful run under 2 minutes** with a local/seeded path, and redefine success as comprehension of what the pipeline produced.

Sources: github.com/dbt-labs/jaffle_shop_duckdb · docs.getdbt.com/guides · dlthub.com/docs · github.com/meltano · docs.prefect.io · productquant.dev (5-min aha) · amplitude.com (TTV).

---

# SECTION 7 — What You Are Missing (Q17 / R-019)

Synthesis across all findings — the gaps the agenda doesn't cover and the assumptions most likely to be wrong.

### Research questions missing entirely from the agenda
1. **The dbt Labs + Fivetran merger (closed 1 June 2026) and its consolidation gravity.** This is the single biggest 2026 event in the space — it pulls dbt tests, GX Core, and Fivetran ingestion under one roof and is *itself* the top migration-intent catalyst. The agenda treats these as independent complements; they're now one competitor with a roadmap aimed at exactly PipelineKit's territory. **Add as a P0 item.**
2. **"Will engineers trust an AI agent to author/coordinate production pipelines at all?"** The agenda assumes AI-native authoring is a feature; the deeper risk is *adoption of agentic tooling in production data paths* given the silent-failure/trust problems in Q10. No research item interrogates the core "AI-native" premise.
3. **Registry monetization** — every existing pipeline/template registry (dbt Hub, Meltano Hub, dlt Hub) is a *free* adoption asset, not a revenue center. R-006 asks about competitors but nothing asks **"can a blueprint registry actually be monetized, and how?"**
4. **Multi-tenancy / data-isolation architecture** for a tool sitting above customers' warehouses — central to every enterprise security questionnaire (Q11) but absent from the agenda.
5. **dlt single-vendor dependency risk** (R-007 asks about adoption, not *concentration risk* on a seed-stage company) — and the same for Soda (now pivoting its core API).
6. **Time-zone/UTC-partition, late-arriving-data, and idempotency semantics** — the failure classes hardest to diagnose (Q10) and the ones a "coordination layer" most needs opinions about; no research item covers them.
7. **AI-governance compliance (ISO 42001 / NIST AI RMF)** — increasingly appearing in enterprise questionnaires for any tool with AI in the data path.

### Assumptions most likely wrong (ranked by impact if wrong)
1. **"We complement, not compete with, Dagster" (R-006)** — highest impact. Dagster Components/`dg` is a near-verbatim free competitor. If this is wrong, the entire "coordination layer" positioning needs a sharper, narrower wedge.
2. **Soda as the quality layer (R-008)** — building on a tool that's 30× behind dbt tests and just deprecated its API is a concrete, near-term SPEC risk.
3. **Proprietary contract format (R-009)** — wrong against a freshly-consolidated Linux-Foundation standard; cheap to fix now, expensive later.
4. **"2-week setup tax" hero claim (R-001)** — wrong as stated; easy to discredit publicly; the corrected framing is *stronger*, so fix it.
5. **No free tier + $99 Solo (R-015)** — likely kills the acquisition funnel for a tool whose substrate is free.

### Add to P0
- **R-019 (new): the merger/consolidation landscape** (Fivetran+dbt+GX) — blocks competitive positioning *and* quality-layer choice.
- **Promote R-008 (quality layer) and R-009 (contracts) from P1/P2 to P0** — both are time-sensitive standards/ecosystem decisions that get more expensive to reverse every sprint, and both are currently mis-specced.

### Single question that could invalidate the whole positioning
**"Is an end-to-end, cross-tool, version-controlled blueprint registry a product people will pay for — or just an adoption wedge that Dagster/dbt will absorb into their free tiers?"** Every other finding points to this. The whitespace is real (no one ships it yet) but the precedent is that registries don't monetize and incumbents are closing in from the orchestrator and transformation sides.

---

# SECTION 8 — The Synthesis Question (Q18 / R-020)

### If you could answer only ONE question before design-partner outreach
**R-006 — True Competition, specifically the Dagster question.** Everything depends on it. If "we complement, not compete with Dagster" is wrong (and the evidence says it's at least *incomplete*), then the pricing page, the sales narrative, the registry investment, and the "coordination layer" hero message are all built on sand. You can fix a wrong setup-tax number with one edit; you cannot fix a positioning that collapses the first time a prospect says *"this is just Dagster Components with a registry."*

### The single assumption most likely to be wrong
**That PipelineKit occupies defensible whitespace as a "coordination layer / installable EMS / blueprint registry."** The research shows the *bundle* is novel but every *component* of it is being built by a better-funded incumbent from a position of incumbency: Dagster (Components/`dg` + Embedded ELT + Dagster+), dbt (Mesh governance + the Fivetran/GX merger), Monte Carlo (observability), ODCS (contracts), and free single-tool registries everywhere. PipelineKit's genuine edge is **cross-tool neutrality + AI-native authoring + a curated registry** — but that edge is durable only on *execution speed vs. roadmaps*, not on a structural moat.

### Evidence to verify or refute it
1. **Design-partner head-to-heads:** in the first 5 conversations, ask *unprompted*, "What would you use instead of this?" If ≥3 say "Dagster" or "dbt + glue," the complement framing is refuted.
2. **Win/loss on the "why not just build it / use Dagster" objection** (Q5's top-5). Track how often it ends conversations.
3. **Registry willingness-to-pay:** does any design partner say they'd pay for *blueprints* specifically (vs. tolerate them free)? If none would, the registry is a wedge, not a revenue engine.
4. **Watch the Fivetran/dbt/GX merged roadmap** for cross-tool blueprint/standardization features — its appearance would compress PipelineKit's window.
5. **Reframe the wedge narrowly and test it:** pick the *one* job PipelineKit does that Dagster/dbt demonstrably don't (the cross-tool, version-controlled ingest→transform→test→observe contract), and see whether that specific pain pulls design partners. If the narrow wedge resonates where the broad "coordination layer" doesn't, you've found the real product.

---

## Research Log (to backfill into RESEARCH-AGENDA.md)

| Code | Headline finding | Action |
|---|---|---|
| R-001 | "2 weeks" unsourced; use 44–53% time-on-pipelines | Update hero claim |
| R-002 | ICP-003 won on SOC 2 Type II + security-questionnaire speed | Retarget outreach to committee |
| R-003 | Pricing triggers intent, reliability completes; merger is the catalyst | Reposition ICP-004 around switching-cost collapse |
| R-006 | Dagster Components/`dg` is a near-verbatim competitor | **Rewrite competitive positioning (P0)** |
| R-007 | dlt growing but seed-stage single-vendor risk | Add abstraction boundary + version pinning |
| R-008 | Soda smallest option, just deprecated SodaCL | Backend-agnostic; lead with dbt tests |
| R-009 | ODCS consolidated the market Dec 2025 | Make contracts ODCS-compatible |
| R-011 | 43/43 on synthetic seeds = smoke test | Build trust tiers + real-data harness |
| R-012 | Don't headline raw 0.00–1.00; calibrate + abstain | Redesign DiagnosticsEngine UX |
| R-013 | CC6 access reviews most-failed; GRC tools miss pipeline semantics | Scope CM-1 to CC6/CC8/CC7 pipeline evidence |
| R-014 | DPA s.50 one-copy residency is the binding rule | Verify CM-5 with Kenyan counsel |
| R-015 | Add free tier; drop/reposition $99 Solo; hybrid model | Rework pricing page |
| R-016 | $299/mo/student is 7–12× market | Reprice Academy; lead academic GTM with free licenses |
| R-017 | No CLI-vs-GUI %; VS Code extension is table stakes | Add VS Code extension to roadmap |
| R-018 | 10-min only with no-creds/local/seeded run; aim <2 min | Design first-run around DuckDB-style local + seeds |
| R-019 (new) | Fivetran+dbt+GX consolidation | Add as P0 research item |
| R-020 | The one question: can a cross-tool blueprint registry be monetized? | Test in design-partner outreach |

---

*Document: RESEARCH-FINDINGS-2026-06.md*
*Location: pipelinekit-internal/reference/research/*
*Owner: Eddy Mkwambe + Command Center*
*Caveats: Regulatory sections are not legal advice. Vendor pricing and several primary PDFs were blocked to automated fetch and rest on search-extracted snippets — re-verify exact figures against live pages before publishing externally.*
