# PipelineKit — Synthetic Data Requirements
## Engineering, Fine-Tuning, and Infrastructure Needs

**Document type:** Synthetic data specification  
**Date:** June 26, 2026  
**Author:** Command Center (Claude Chat) + Eddy Mkwambe  
**Pack system:** RealityDB CLI v2.38.0 — Pack JSON format (DATA-GENERATION-GUIDE.md v2.0)  
**Status:** Approved — ready for pack authoring

---

## Purpose

This document specifies every synthetic dataset PipelineKit needs for:

1. **Blueprint verification** — local end-to-end testing of each blueprint
2. **AI Blueprint Proposal fine-tuning** — improving BlueprintProposer confidence
3. **Migration Intelligence fine-tuning** — improving MigrationAnalyzer accuracy
4. **Registry and integration testing** — verifying Sprint 6-6 end-to-end
5. **Design partner demos** — showing PipelineKit against real-looking data

Each dataset is specified as a RealityDB pack requirement with the schema, distributions, cardinality, and quality target needed for production use.

---

## DATASET 1: Blueprint Verification — Orders (current seed replacement)

**Purpose:** Replace the minimal Docker seed for Blueprint #001 (postgres-to-snowflake) local verification. Current seed uses a single random INSERT with no distribution logic, causing false dbt test failures (e.g. the `confirmed` status incident).

**Used by:**
- `scripts/verify-blueprint-001.ps1 -Local`
- dbt source tests: `accepted_values`, `not_null`, `unique`
- Contract validation: `orders.yaml`

**Pack name:** `pipelinekit-orders`  
**Target rows:** 10,000 (verified locally at this scale)  
**SQR target:** 97/100 MEDIUM confidence  
**Engine format:** SQL (for assess compatibility)

### Schema

```
Root table: customers
  ├── orders (N per customer, mean 4.2)
  │   └── order_items (N per order, mean 3.2)
  └── addresses (N per customer, mean 1.8)
```

### Table: customers

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK |
| full_name | string | full_name strategy | — |
| email | string | email strategy | — |
| customer_tier | enum | standard 65%, premium 25%, enterprise 10% | Stripe Atlas 2024 |
| signup_source | enum | organic 42%, referral 31%, paid 18%, partner 9% | OpenView 2024 |
| country | enum | US 68%, CA 8%, GB 7%, AU 5%, DE 4%, other 8% | eCommerce benchmarks |
| created_at | past_date | 24-month spread | — |

### Table: orders

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK |
| customer_id | uuid | FK → customers.id | — |
| order_id | string | template: ORD-{6 digits} | — |
| amount | float | lognormal mean=127, stddev=89, min=5, max=5000 | NRF 2024 |
| status | enum | pending 8%, processing 12%, shipped 18%, delivered 55%, cancelled 7% | Shopify Commerce 2024 |
| payment_method | enum | card 72%, paypal 18%, bank_transfer 7%, crypto 3% | Stripe 2024 |
| created_at | past_date | 18-month spread | — |

**Critical note:** `status` must include exactly these values — `pending, processing, shipped, delivered, cancelled`. The dbt `accepted_values` test in sources.yml uses this list. No `confirmed`, no `returned`.

### Table: order_items

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK |
| order_id | uuid | FK → orders.id | — |
| product_name | string | template: Product {alpha} {3digits} | — |
| quantity | integer | poisson mean=2.1, min=1, max=12 | NRF 2024 |
| unit_price | float | lognormal mean=42, stddev=31, min=1, max=500 | — |
| category | enum | electronics 22%, apparel 19%, home 16%, beauty 13%, sports 11%, other 19% | Shopify 2024 |

### Cardinality

```json
"relationships": [
  {
    "sourceTable": "customers",
    "targetTable": "orders",
    "cardinality": { "strategy": "poisson", "mean": 4.2, "min": 1, "max": 24 }
  },
  {
    "sourceTable": "orders",
    "targetTable": "order_items",
    "cardinality": { "strategy": "poisson", "mean": 3.2, "min": 1, "max": 12 }
  }
]
```

### dbt model targets (after transformation)

```sql
-- stg_orders: 1 row per order_id, amount > 0, status in accepted list
-- fct_orders: joined with customers, derived revenue metrics
```

---

## DATASET 2: Blueprint Verification — Salesforce CRM (Blueprint #002)

**Purpose:** Replace synthetic DuckDB seed for Blueprint #002 (salesforce-to-snowflake) local verification. Current seed is inline Python in the verification script — no distribution logic.

**Used by:**
- `scripts/verify-blueprint-002.ps1 -Local`
- dbt source tests on opportunities, accounts, contacts
- Contract: `opportunities.yaml`

**Pack name:** `pipelinekit-crm`  
**Target rows:** 5,000  
**SQR target:** 97/100 MEDIUM confidence

### Schema

```
Root table: accounts
  ├── opportunities (N per account, mean 3.8)
  ├── contacts (N per account, mean 4.1)
  └── activities (N per account, mean 12.0)
```

### Table: accounts

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK |
| name | string | company_name strategy | — |
| industry | enum | Technology 28%, Financial 18%, Healthcare 14%, Manufacturing 11%, Retail 9%, Other 20% | Salesforce State of Sales 2024 |
| annual_revenue | float | lognormal mean=2400000, stddev=8000000, min=50000, max=500000000 | — |
| number_of_employees | integer | poisson mean=180, min=5, max=50000 | — |
| billing_country | enum | US 61%, UK 9%, CA 7%, AU 5%, DE 4%, other 14% | — |
| created_date | past_date | 36-month spread | — |
| last_modified_date | past_date | 6-month spread | — |

### Table: opportunities

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK |
| account_id | uuid | FK → accounts.id | — |
| name | string | template: {company} {product} Deal | — |
| amount | float | lognormal mean=47000, stddev=82000, min=1000, max=2000000 | Salesforce B2B 2024 |
| stage_name | enum | Prospecting 18%, Qualification 15%, Proposal 14%, Negotiation 11%, Closed Won 28%, Closed Lost 14% | Salesforce 2024 |
| close_date | future_date | 90-day spread (mix past/future) | — |
| probability | integer | derived from stage, 10–95 | — |
| is_won | enum | true 28%, false 72% (matches Closed Won rate) | — |
| is_closed | enum | true 42%, false 58% | — |
| created_date | past_date | 24-month spread | — |
| last_modified_date | past_date | 3-month spread | — |

**Critical:** `stage_name` values must match exactly what `contracts/opportunities.yaml` expects.

### Table: contacts

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK |
| account_id | uuid | FK → accounts.id | — |
| first_name | string | full_name strategy (first only) | — |
| last_name | string | full_name strategy (last only) | — |
| email | string | email strategy | — |
| title | enum | VP 12%, Director 18%, Manager 24%, Individual Contributor 31%, C-Suite 8%, Other 7% | LinkedIn 2024 |
| department | enum | Sales 28%, Engineering 22%, Marketing 17%, Finance 11%, HR 8%, Other 14% | — |
| created_date | past_date | 24-month spread | — |

---

## DATASET 3: Blueprint Verification — Stripe Payments (Blueprint #003)

**Purpose:** Enable local verification of Blueprint #003 (stripe-to-snowflake). No verification has been done yet — this is the missing piece before Blueprint #003 can be marked verified.

**Used by:**
- `scripts/verify-blueprint-003.ps1 -Local` (does not yet exist — needs creation)
- dbt models: `stg_stripe__charges`, `stg_stripe__customers`, `fct_charges`, `dim_customers`
- Contracts: `charges.yaml`, `customers.yaml`
- dbt quality tests: `assert_no_negative_charge_amounts`, `assert_no_duplicate_charges`

**Pack name:** `pipelinekit-payments`  
**Target rows:** 10,000  
**SQR target:** 97/100 MEDIUM confidence

### Schema

```
Root table: customers
  └── charges (N per customer, mean 8.4)
      └── refunds (N per charge, mean 0.08 — sparse)
```

### Table: customers

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK (maps to Stripe customer id) |
| email | string | email strategy | — |
| name | string | full_name strategy | — |
| currency | enum | usd 74%, eur 12%, gbp 8%, cad 3%, aud 3% | Stripe Atlas 2024 |
| description | string | nullable 0.60, template: Customer account | — |
| created | integer | Unix epoch, 24-month spread | — |
| last_modified_date | past_date | 6-month spread | — |

**Critical note:** Stripe returns `created` as Unix epoch integer, not a timestamp. The dbt model `stg_stripe__customers` uses `to_timestamp_ntz(created)`. The synthetic data must use integer Unix timestamps, not SQL timestamps.

### Table: charges

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK |
| customer_id | uuid | FK → customers.id | — |
| amount | integer | lognormal mean=8500, stddev=12000, min=50, max=999900 (cents) | Stripe 2024 |
| currency | enum | usd 74%, eur 12%, gbp 8%, cad 3%, aud 3% | — |
| status | enum | succeeded 87%, pending 4%, failed 9% | Stripe failure rate data 2024 |
| refunded | enum | false 93%, true 7% | Stripe refund benchmarks |
| description | string | nullable 0.55, template: Payment for {service} | — |
| payment_method | enum | card 91%, bank_debit 6%, wallet 3% | — |
| created | integer | Unix epoch, 18-month spread | — |

**Critical:** `status` must be `succeeded`, `pending`, or `failed` only — exactly matching the `accepted_values` in dbt schema.yml. No `complete`, no `captured`.

**Critical:** `amount` must always be >= 0. The dbt test `assert_no_negative_charge_amounts` will fail on any negative value.

### Table: refunds (sparse child)

| Column | Type | Distribution | Source |
|---|---|---|---|
| id | uuid | — | PK |
| charge_id | uuid | FK → charges.id | — |
| amount | integer | same distribution as parent charge amount | — |
| reason | enum | duplicate 28%, fraudulent 31%, requested_by_customer 41% | Stripe 2024 |
| status | enum | succeeded 96%, pending 3%, failed 1% | — |
| created | integer | Unix epoch, after parent charge | — |

**Cardinality:** mean 0.08 (sparse — 8% of charges have a refund)

---

## DATASET 4: Migration Intelligence Fine-Tuning — Airbyte Config Corpus

**Purpose:** Generate a corpus of realistic Airbyte connection.json files for testing and fine-tuning the `MigrationAnalyzer`. Current test uses one sparse config; production needs a diverse corpus.

**This is not a RealityDB pack** — it is a JSON document generator. But it follows the same distribution thinking.

**Pack name:** N/A — Python generator script  
**Target:** 500 synthetic Airbyte configs  
**Format:** JSON files (one per connection)

### Corpus Composition

| Source type | Count | Completeness | Notes |
|---|---|---|---|
| postgres → snowflake | 100 | High (all fields) | Should map cleanly |
| postgres → snowflake | 50 | Medium (missing cron) | Should produce 1 blocking gap |
| postgres → snowflake | 50 | Sparse (no source config) | Should produce 3+ blocking gaps |
| salesforce → snowflake | 100 | High | Tests Salesforce parser |
| mysql → bigquery | 100 | High | Tests unsupported source detection |
| stripe → redshift | 100 | High | Tests unsupported destination |

### Per-Config Fields

```json
{
  "connectionId": "uuid",
  "name": "descriptive-connection-name",
  "sourceConfiguration": {
    "host": "db.example.com",
    "port": 5432,
    "database": "production",
    "username": "analyst",
    "ssl": true
  },
  "destinationType": "snowflake|bigquery|redshift",
  "syncCatalog": {
    "streams": [
      {
        "stream": { "name": "table_name" },
        "config": {
          "syncMode": "incremental|full_refresh",
          "cursorField": ["updated_at"]
        }
      }
    ]
  },
  "scheduleType": "cron|manual|basic_schedule",
  "scheduleData": {
    "cron": { "cronExpression": "0 * * * *", "cronTimeZone": "UTC" }
  }
}
```

### Expected Outcomes by Type

| Config type | Expected confidence | Expected blocking gaps |
|---|---|---|
| postgres → snowflake (high) | 0.75–0.90 | 0–1 (credentials only) |
| postgres → snowflake (medium) | 0.50–0.70 | 1–2 |
| postgres → snowflake (sparse) | 0.10–0.30 | 3–6 |
| mysql → bigquery | 0.30–0.50 | 2 (unsupported source + credentials) |
| stripe → redshift | 0.20–0.40 | 2 (unsupported destination) |

This corpus enables regression testing of `MigrationAnalyzer` — confidence scores and gap counts should be stable across code changes.

---

## DATASET 5: AI Blueprint Proposal Pattern Library

**Purpose:** Expand the blueprint pattern library so `BlueprintProposer` has more examples to reason from. Currently 3 patterns → confidence 0.82. Target: 10 patterns → confidence 0.90+.

**These are blueprint JSON structures, not RealityDB packs**, but they require synthetic data for local verification before being added to the library.

### Priority blueprint patterns to generate + verify

| Blueprint | Source | Destination | Priority | Verification data needed |
|---|---|---|---|---|
| stripe-to-bigquery | stripe | bigquery | P1 | Dataset 3 adapted for BigQuery |
| hubspot-to-snowflake | hubspot | snowflake | P1 | New CRM pack (contacts, deals, companies) |
| mysql-to-snowflake | mysql | snowflake | P2 | Orders pack adapted (Dataset 1) |
| shopify-to-snowflake | shopify | snowflake | P2 | E-commerce pack (products, orders, inventory) |
| bigquery-to-snowflake | bigquery | snowflake | P2 | Analytics events pack |

### HubSpot CRM Pack (for hubspot-to-snowflake)

**Tables needed:** companies, contacts, deals, engagements, tickets

| Table | Key columns | Cardinality |
|---|---|---|
| companies | id, name, industry, annual_revenue, employees, country | root |
| contacts | id, company_id, email, first_name, last_name, lifecycle_stage | mean 4.8/company |
| deals | id, company_id, deal_name, amount, stage, close_date, probability | mean 2.1/company |
| engagements | id, contact_id, type, created_at | mean 8.3/contact |
| tickets | id, company_id, subject, status, priority, created_at | mean 1.2/company |

**Key distribution (HubSpot State of Marketing 2024):**
- Deal stage: Appointment Scheduled 22%, Qualified to Buy 18%, Presentation Scheduled 14%, Decision Maker Bought In 11%, Contract Sent 9%, Closed Won 16%, Closed Lost 10%
- Ticket status: open 38%, waiting_on_contact 22%, waiting_on_us 15%, closed 25%

---

## DATASET 6: PipelineKit Health and Regression Testing

**Purpose:** A deterministic dataset for automated regression testing of all PipelineKit commands. Every `pipelinekit run` should produce identical output on this dataset, making CI green/red unambiguous.

**Pack name:** `pipelinekit-regression`  
**Target rows:** 1,000 (small — deterministic at this scale)  
**Seed:** fixed at 42  
**SQR target:** 95/100 (internal use — speed over quality)

### Schema (minimal, covers all dbt model types)

```
Root: accounts (100 rows)
  ├── events (mean 5.0 per account = 500 rows)
  └── metrics (mean 4.0 per account = 400 rows)
```

### Table: accounts

| Column | Type | Values |
|---|---|---|
| id | uuid | — |
| name | string | company_name |
| tier | enum | free 50%, pro 30%, enterprise 20% |
| status | enum | active 80%, churned 15%, paused 5% |
| created_at | past_date | 12-month spread |
| mrr | float | normal mean=500, stddev=300, min=0, max=5000 |

### Table: events

| Column | Type | Values |
|---|---|---|
| id | uuid | — |
| account_id | uuid | FK → accounts.id |
| event_type | enum | login 35%, api_call 40%, export 15%, error 10% |
| created_at | past_date | 6-month spread |

### Table: metrics

| Column | Type | Values |
|---|---|---|
| id | uuid | — |
| account_id | uuid | FK → accounts.id |
| metric_name | enum | api_calls 40%, active_users 35%, data_volume_gb 25% |
| value | float | normal mean=100, stddev=50, min=0, max=1000 |
| recorded_at | past_date | 6-month spread |

**Why this matters:** Blueprint verification currently uses Docker Postgres with a manually seeded dataset. A deterministic RealityDB pack at seed=42 gives byte-identical output every run — making the test suite genuinely regression-proof.

---

## DATASET 7: Design Partner Demo — Analytics Platform

**Purpose:** A showcase dataset for the first design partner conversation. Shows PipelineKit handling real-looking analytics data — not toy orders or placeholder names.

**Domain:** B2B SaaS analytics platform  
**Pack name:** `pipelinekit-saas-demo`  
**Target rows:** 50,000  
**SQR target:** 99/100 HIGH confidence  
**Audience:** Design partner demo — must look production-realistic

### Schema

```
Root: organizations (200 rows)
  ├── users (mean 18 per org = 3,600 rows)
  │   ├── sessions (mean 8.2 per user = 29,520 rows)
  │   └── feature_usage (mean 4.1 per user = 14,760 rows)
  └── subscriptions (mean 1.1 per org = 220 rows)
      └── invoices (mean 12 per subscription = 2,640 rows)
```

Total: ~50,740 rows

### Key Distributions

**organizations:**
- industry: Technology 31%, Financial Services 19%, Healthcare 14%, Retail 12%, Manufacturing 10%, Other 14%
- plan: starter 38%, growth 35%, enterprise 27%
- arr: lognormal mean=28000, stddev=65000, min=1200, max=2000000

**users:**
- role: admin 8%, power_user 22%, regular 55%, viewer 15%
- status: active 72%, inactive 18%, churned 10%
- last_login: past_date 90-day spread

**sessions:**
- duration_seconds: lognormal mean=420, stddev=280, min=30, max=3600
- page_views: poisson mean=8.4, min=1, max=80

**subscriptions:**
- status: active 78%, cancelled 14%, past_due 5%, trialing 3%
- mrr: derived from org.plan (starter $100, growth $350, enterprise $2000 base + seats)

**invoices:**
- status: paid 84%, open 8%, void 4%, uncollectible 4%
- amount: matches subscription mrr

---

## Summary: Pack Authoring Priority

| Priority | Dataset | Purpose | Pack name | Target rows | SQR |
|---|---|---|---|---|---|
| **P0** | Dataset 1: Orders | Blueprint #001 verification | `pipelinekit-orders` | 10,000 | 97/100 |
| **P0** | Dataset 3: Payments | Blueprint #003 verification | `pipelinekit-payments` | 10,000 | 97/100 |
| **P1** | Dataset 2: CRM | Blueprint #002 verification | `pipelinekit-crm` | 5,000 | 97/100 |
| **P1** | Dataset 7: SaaS Demo | Design partner demo | `pipelinekit-saas-demo` | 50,000 | 99/100 |
| **P2** | Dataset 6: Regression | CI/CD regression | `pipelinekit-regression` | 1,000 | 95/100 |
| **P2** | Dataset 4: Airbyte Corpus | Migration fine-tuning | Python script | 500 configs | N/A |
| **P3** | Dataset 5: Pattern library | AI proposal fine-tuning | Multiple packs | varies | 97/100 |

---

## Pack Authoring Notes (RealityDB-specific)

All packs above must follow `DATA-GENERATION-GUIDE.md v2.0` rules. Critical constraints from lessons learned:

1. **One temporal column per table** — do not add `created_at` alongside `event_date` or `created` (Unix epoch). Pick one temporal anchor.

2. **No "none" in enum values** — use `nullable: true` + `nullWeight` instead. `confirmed` is not in the orders status list — it caused a dbt test failure.

3. **Status enums must exactly match dbt accepted_values** — the pack enum values and the dbt test values must be identical. Verify before generating.

4. **Stripe amounts are integers (cents)** — `amount` column for payments is integer, not float. The dbt model divides by 100. Never use float for Stripe amounts.

5. **Unix epoch for Stripe timestamps** — `created` column is integer Unix epoch. The dbt model uses `to_timestamp_ntz(created)`. Do not use SQL `past_date` strategy for Stripe tables.

6. **BOM-free UTF-8** — all generated SQL must be written with `New-Object System.Text.UTF8Encoding $false` to avoid PK-MIGRATE-002 equivalent issues in PipelineKit.

7. **Verify against dbt source tests before committing** — run `dbt parse` and `dbt build --select source:*` against the generated data before marking a dataset as the official verification seed.
