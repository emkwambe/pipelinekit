# PipelineKit Academy — Synthetic Data Requirements
## Training Data Engineering Through Simulation

**Document type:** Synthetic data specification — Education and Training  
**Date:** June 26, 2026  
**Author:** Command Center (Claude Chat) + Eddy Mkwambe  
**Pack system:** RealityDB CLI v2.38.0 — Pack JSON format (DATA-GENERATION-GUIDE.md v2.0)  
**Companion document:** PIPELINEKIT-SYNTHETIC-DATA-REQUIREMENTS.md (engineering needs)  
**Status:** Approved — ready for pack authoring

---

## The Learning Model

Traditional data engineering courses teach students how to use tools.  
PipelineKit Academy teaches students how to operate analytics systems.

The difference is the simulator.

```
Traditional:           PipelineKit Academy:
Download CSV           RealityDB generates synthetic enterprise
     ↓                           ↓
Import CSV             Student receives: "Your analytics platform has failed"
     ↓                           ↓
Transform              Student builds pipeline with PipelineKit
     ↓                           ↓
Finish assignment      RealityDB introduces production incident
                                 ↓
                       Student diagnoses, recovers, and explains
                                 ↓
                       Certification: 12 incidents recovered = certified
```

**RealityDB is the flight simulator. PipelineKit is the aircraft.**

---

## Synthetic Data Architecture for the Academy

Every course module requires three types of synthetic data:

1. **Baseline enterprise dataset** — the company the student operates
2. **Incident injection** — the failure RealityDB introduces each week
3. **Assessment dataset** — the controlled scenario used to grade the student

These are distinct. A baseline must be internally consistent and realistic. An incident must be precisely wrong in a specific, diagnosable way. An assessment must be deterministic — same seed, same failure, same correct answer.

---

## THE SYNTHETIC ENTERPRISES

Six synthetic companies, one per learning path. Each is a complete RealityDB pack. Each runs on PipelineKit.

---

### ENTERPRISE 1: FinCore Analytics
**Domain:** B2B FinTech SaaS — payments processing platform  
**Learning path:** Core Data Engineering (Beginner → Intermediate)  
**Pack name:** `academy-fincore`  
**Target rows:** 100,000  
**SQR target:** 99/100 HIGH confidence  
**Citation standard:** Federal Reserve Payments Study 2024, Stripe Atlas 2024

#### Schema

```
Root: merchants (500 rows)
  ├── customers (mean 120 per merchant = 60,000 rows)
  │   ├── transactions (mean 8.4 per customer = 504,000 rows)
  │   │   └── transaction_events (mean 3.1 per transaction)
  │   └── payment_methods (mean 2.2 per customer)
  ├── invoices (mean 24 per merchant = 12,000 rows)
  │   └── invoice_line_items (mean 4.1 per invoice)
  └── fraud_cases (mean 0.08 per merchant — sparse)
```

#### Table Specifications

**merchants**
| Column | Distribution | Citation |
|---|---|---|
| industry | Retail 28%, Restaurant 19%, Healthcare 16%, Professional Services 14%, E-commerce 13%, Other 10% | Fed Reserve 2024 |
| monthly_volume | lognormal mean=$180K, stddev=$420K | Stripe Atlas 2024 |
| plan | starter 42%, growth 35%, enterprise 23% | OpenView 2024 |
| status | active 78%, suspended 12%, churned 10% | — |
| country | US 68%, CA 9%, UK 8%, AU 5%, other 10% | — |

**transactions**
| Column | Distribution | Citation |
|---|---|---|
| amount | lognormal mean=$127, stddev=$89, min=$0.50, max=$50,000 | NRF 2024 |
| status | succeeded 87%, failed 9%, pending 3%, refunded 7% (overlapping) | Stripe 2024 |
| payment_method | card 74%, ACH 16%, wire 6%, check 4% | Fed Reserve 2024 |
| currency | USD 74%, EUR 12%, GBP 8%, CAD 3%, AUD 3% | — |
| created_at | past_date 24-month spread | — |

**fraud_cases**
| Column | Distribution | Citation |
|---|---|---|
| fraud_type | card_not_present 51%, account_takeover 28%, friendly_fraud 14%, identity_theft 7% | LexisNexis Fraud Report 2024 |
| amount | lognormal mean=$340, stddev=$280 | — |
| resolved | true 73%, false 27% | — |

#### What students build with FinCore
- Week 1: `pipelinekit blueprint install fincore-to-snowflake` → run first pipeline
- Week 2-3: dbt staging models for merchants, customers, transactions
- Week 4: Contract enforcement on transactions (amount > 0, status in accepted list)
- Week 5: Soda freshness checks (transactions must arrive within 4 hours)
- Week 6: fct_revenue, fct_fraud_rate, dim_merchants core models

---

### ENTERPRISE 2: MedTrack Systems
**Domain:** Healthcare — clinic management and revenue cycle  
**Learning path:** Healthcare Data Engineering  
**Pack name:** `academy-medtrack`  
**Target rows:** 50,000  
**SQR target:** 99/100 HIGH confidence  
**Citation standard:** CDC NCHS, MGMA Survey 2024, CMS data

#### Schema

```
Root: clinics (50 rows)
  ├── patients (mean 180 per clinic = 9,000 rows)
  │   ├── appointments (mean 6.2 per patient/year = 55,800 rows)
  │   │   ├── diagnoses (mean 1.8 per appointment)
  │   │   └── prescriptions (mean 2.1 per appointment)
  │   └── insurance_info (mean 1.2 per patient)
  ├── providers (mean 8 per clinic = 400 rows)
  └── claims (mean 8.3 per patient = 74,700 rows)
      └── claim_payments (mean 0.85 per claim — some denied)
```

#### Key Distributions

**appointments.status**
- completed 72%, no_show 12%, cancelled 11%, rescheduled 5%  
- Source: MGMA Physician Practice Management Survey 2024

**diagnoses.icd10_code**
- Top 20 ICD-10 codes weighted by CDC prevalence
- Hypertension (I10) 15%, Type 2 Diabetes (E11) 11%, Hyperlipidemia (E78) 9%...
- Source: CDC National Ambulatory Medical Care Survey 2024

**claims.status**
- paid 68%, denied 18%, pending 9%, appealed 5%
- Source: CMS Medicare/Medicaid denial rate data 2024

**claim_payments.payment_source**
- insurance 74%, patient 18%, medicare 6%, medicaid 2%

#### What students build with MedTrack
- HIPAA-aware pipeline patterns (PII handling)
- dbt models: stg_appointments, fct_encounter_metrics, dim_providers
- Contract on claims (amount > 0, status in accepted list, no orphaned claim_id)
- Freshness SLA: claims must arrive within 48 hours of appointment
- fct_denial_rate: the hidden story metric

---

### ENTERPRISE 3: RetailFlow Commerce
**Domain:** E-commerce — multi-channel retail  
**Learning path:** E-Commerce Analytics Engineering  
**Pack name:** `academy-retailflow`  
**Target rows:** 200,000  
**SQR target:** 99/100 HIGH confidence  
**Citation standard:** Shopify Commerce Report 2024, NRF, Digital Commerce 360

#### Schema

```
Root: stores (100 rows)
  ├── products (mean 280 per store = 28,000 rows)
  │   └── inventory (mean 3.2 per product — SKU variants)
  ├── customers (mean 400 per store = 40,000 rows)
  │   ├── orders (mean 4.2 per customer = 168,000 rows)
  │   │   ├── order_items (mean 3.2 per order)
  │   │   └── shipments (mean 1.1 per order)
  │   └── reviews (mean 0.15 per order — sparse)
  └── marketing_campaigns (mean 6 per store)
      └── campaign_events (mean 840 per campaign)
```

#### Key Distributions

**orders.status**
- delivered 55%, processing 12%, shipped 18%, cancelled 7%, returned 8%
- Source: Shopify Commerce Report 2024

**customers.acquisition_channel**
- organic_search 31%, paid_social 24%, email 19%, referral 14%, direct 12%
- Source: Digital Commerce 360 2024

**products.category**
- Apparel 22%, Electronics 19%, Home & Garden 16%, Beauty 13%, Sports 11%, Other 19%

#### What students build with RetailFlow
- Multi-source ingestion (orders + inventory + marketing in one run)
- SCD Type 2 for product pricing changes
- fct_orders, fct_inventory_turns, dim_customers, dim_products
- Marketing attribution model (last-touch, first-touch, linear)
- Freshness checks per source (orders 1hr, inventory 6hr, marketing 24hr)

---

### ENTERPRISE 4: CloudPulse SaaS
**Domain:** B2B SaaS — product analytics platform  
**Learning path:** SaaS Analytics Engineering  
**Pack name:** `academy-cloudpulse`  
**Target rows:** 150,000  
**SQR target:** 99/100 HIGH confidence  
**Citation standard:** OpenView SaaS Benchmarks 2024, Bessemer Cloud Index

#### Schema

```
Root: organizations (300 rows)
  ├── users (mean 22 per org = 6,600 rows)
  │   ├── sessions (mean 8.4 per user = 55,440 rows)
  │   │   └── page_events (mean 12 per session)
  │   └── feature_usage (mean 4.1 per user)
  ├── subscriptions (mean 1.1 per org = 330 rows)
  │   └── invoices (mean 12 per subscription = 3,960 rows)
  └── support_tickets (mean 0.3 per user per month)
```

#### Key Distributions

**subscriptions.status**
- active 78%, cancelled 14%, past_due 5%, trialing 3%
- Source: Bessemer Cloud Index 2024

**organizations.churn_risk**
- low 58%, medium 28%, high 14%
- Source: Gainsight Customer Success Report 2024

**feature_usage.feature_name**
- dashboard 34%, export 22%, api_access 18%, alerts 14%, integrations 12%
- Source: Pendo Product Benchmark Report 2024

#### What students build with CloudPulse
- Product-led growth metrics pipeline
- fct_mrr, fct_churn, dim_accounts, fct_feature_adoption
- NRR (Net Revenue Retention) calculation in dbt
- Health score model combining usage + support + billing signals
- PipelineKit diagnose after intentional pipeline failure

---

### ENTERPRISE 5: LogiTrack Freight
**Domain:** Supply chain and logistics  
**Learning path:** Operations Analytics Engineering  
**Pack name:** `academy-logitrack`  
**Target rows:** 80,000  
**SQR target:** 99/100 HIGH confidence  
**Citation standard:** Bureau of Transportation Statistics 2024, FreightWaves

#### Schema

```
Root: carriers (80 rows)
  ├── shipments (mean 420 per carrier = 33,600 rows)
  │   ├── shipment_events (mean 6.2 per shipment = 208,320 rows)
  │   └── delivery_exceptions (mean 0.12 per shipment — sparse)
  ├── routes (mean 18 per carrier = 1,440 rows)
  └── drivers (mean 24 per carrier = 1,920 rows)
      └── driver_logs (mean 22 per driver = 42,240 rows)
```

#### Key Distributions

**shipments.status**
- delivered 71%, in_transit 14%, delayed 9%, exception 4%, returned 2%
- Source: FreightWaves Sonar 2024

**delivery_exceptions.reason**
- address_not_found 28%, recipient_unavailable 22%, weather 19%, vehicle_breakdown 16%, customs 15%
- Source: UPS/FedEx public exception rate data 2024

**shipment_events.event_type**
- picked_up 17%, in_transit 34%, out_for_delivery 16%, delivered 17%, exception 8%, returned 8%

#### What students build with LogiTrack
- On-time delivery (OTD) pipeline
- fct_shipments, fct_exception_rates, dim_carriers, dim_routes
- Freshness SLA: shipment_events must arrive within 2 hours
- Late arrival pattern: simulate delayed events, student sets up alerting
- fct_driver_performance model

---

### ENTERPRISE 6: EduMetrics Academy
**Domain:** Education analytics — K-12 and higher education  
**Learning path:** Education Data Engineering  
**Pack name:** `academy-edumetrics`  
**Target rows:** 60,000  
**SQR target:** 99/100 HIGH confidence  
**Citation standard:** NCES 2024, UNESCO, State Education Departments  
**Special:** Directly connects to EduNode Analytics and MathAthlone data

#### Schema

```
Root: schools (60 rows)
  ├── students (mean 320 per school = 19,200 rows)
  │   ├── enrollments (mean 6.2 per student = 119,040 rows)
  │   │   └── grades (mean 4.8 per enrollment)
  │   ├── assessments (mean 8.4 per student = 161,280 rows)
  │   └── attendance (mean 180 per student/year)
  ├── teachers (mean 18 per school = 1,080 rows)
  └── interventions (mean 0.28 per student — MTSS)
```

#### Key Distributions

**students.risk_level** (MTSS tiers)
- tier_1 68%, tier_2 22%, tier_3 10%
- Source: NCES MTSS Implementation Study 2024

**assessments.subject**
- Mathematics 28%, ELA 26%, Science 18%, Social Studies 14%, Other 14%
- Source: NCES Nation's Report Card 2024

**assessments.score_percentile**
- normal distribution mean=52, stddev=21, min=1, max=99
- Source: NAEP score distribution 2024

**attendance.status**
- present 91%, absent_excused 5%, absent_unexcused 3%, tardy 1%
- Source: Attendance Works 2024

#### What students build with EduMetrics
- MTSS Early Warning System pipeline (feeding EduNode Analytics)
- fct_student_performance, dim_schools, fct_attendance_rates
- Chronic absenteeism calculation (>10% absence = chronically absent)
- Assessment trend analysis (year-over-year by cohort)
- Teacher effectiveness model from grade distributions

---

## THE INCIDENT LIBRARY

This is the core of the Academy. Each incident is a precisely engineered data failure that students must diagnose and recover using PipelineKit.

Each incident is a RealityDB **Story Enforcer** script — a post-generation UPDATE/INSERT that introduces a specific, realistic failure into the baseline enterprise dataset.

---

### INCIDENT-001: Schema Drift
**Enterprise:** Any  
**Week:** 2  
**Failure type:** Source table adds a new NOT NULL column without migration

```sql
-- Story enforcer adds this to the source:
ALTER TABLE transactions ADD COLUMN payment_processor VARCHAR(50) NOT NULL DEFAULT '';

-- dbt model breaks because stg_transactions doesn't select new column
-- Contract fails because new column appears in source but not in contract
```

**Student task:**
1. Run `pipelinekit run` → see failure
2. Run `pipelinekit diagnose` → AI identifies schema drift
3. Update dbt staging model to include new column
4. Update contract to include new field
5. Re-run → green

**Assessment criteria:**
- pipelinekit validate passes after fix
- All dbt tests pass
- Contract updated with correct data type

---

### INCIDENT-002: Duplicate Primary Keys
**Enterprise:** FinCore, RetailFlow  
**Week:** 3  
**Failure type:** ETL bug introduces duplicate customer IDs

```sql
-- Story enforcer:
INSERT INTO customers (id, email, name, created_at)
SELECT id, email || '.dup', name || ' (Duplicate)', NOW()
FROM customers
WHERE id IN (SELECT id FROM customers ORDER BY RANDOM() LIMIT 50);
-- 50 customers now have duplicate IDs
```

**Student task:**
1. `pipelinekit run` → contract violation (PK uniqueness)
2. `pipelinekit diagnose` → identifies 50 duplicate customer_ids
3. Write deduplication logic in dbt (ROW_NUMBER() over partition)
4. Update contract's uniqueness rule
5. Document the incident in runbook

**Assessment criteria:**
- Zero duplicates in fct_customers after fix
- dbt unique test passes on customer_id
- Root cause explanation in runbook

---

### INCIDENT-003: Late Arriving Facts
**Enterprise:** All  
**Week:** 4  
**Failure type:** Orders arrive 36 hours late — freshness SLA breached

```sql
-- Story enforcer:
UPDATE orders
SET created_at = created_at - INTERVAL '36 hours'
WHERE created_at > NOW() - INTERVAL '2 days';
-- 2 days of orders appear 36 hours late
```

**Student task:**
1. Freshness alert fires (Soda check: max_age_hours: 4)
2. `pipelinekit diagnose` → identifies freshness breach
3. Trace root cause (upstream ETL delay)
4. Set up monitoring alert for future breaches
5. Backfill logic: re-run with `--full-refresh` after data arrives

**Assessment criteria:**
- Freshness check passes after backfill
- Alert config updated in alerts/config.yaml
- Runbook documents the recovery procedure

---

### INCIDENT-004: Revenue Mismatch
**Enterprise:** FinCore, RetailFlow, CloudPulse  
**Week:** 5  
**Failure type:** Finance reports revenue 23% higher than analytics dashboard

```sql
-- Story enforcer introduces two bugs simultaneously:
-- Bug 1: Refunds not being subtracted from revenue
UPDATE transactions SET status = 'succeeded'
WHERE status = 'refunded' AND amount > 100;
-- Bug 2: Test transactions included in production metric
INSERT INTO transactions (id, merchant_id, amount, status, is_test)
SELECT gen_random_uuid(), merchant_id, amount * 0.23, 'succeeded', true
FROM transactions WHERE status = 'succeeded' LIMIT 1000;
```

**Student task:**
1. Finance raises ticket: "Dashboard revenue is wrong"
2. `pipelinekit architect analyze` → identifies two possible data models
3. Student traces lineage: which dbt model computes revenue?
4. Find bug 1: refunds not excluded
5. Find bug 2: test transactions not filtered
6. Fix both in dbt model logic
7. Validate: revenue matches finance's number

**Assessment criteria:**
- Revenue calculation excludes refunds
- is_test = true records excluded from all revenue metrics
- Data lineage documented

---

### INCIDENT-005: Volume Spike — Pipeline Under Pressure
**Enterprise:** RetailFlow  
**Week:** 6  
**Failure type:** Black Friday sale — 10x normal transaction volume

```sql
-- Story enforcer:
INSERT INTO orders
SELECT gen_random_uuid(), customer_id, amount * (0.8 + random() * 0.4),
       'processing', NOW() - (random() * INTERVAL '2 hours')
FROM orders CROSS JOIN generate_series(1, 9)
WHERE created_at > NOW() - INTERVAL '1 day';
-- 10x order volume in 24-hour window
```

**Student task:**
1. `pipelinekit health` → sees warnings on performance
2. Run pipeline → succeeds but takes 8x longer than usual
3. Identify bottleneck: full table scan in stg_orders
4. Add incremental materialization to dbt model
5. Add volume anomaly check to Soda quality checks
6. Re-run: pipeline handles volume, alert configured for future spikes

**Assessment criteria:**
- dbt model uses incremental strategy
- Soda volume anomaly check in quality/checks.yaml
- Pipeline completes in under 2x normal time

---

### INCIDENT-006: Contract Violation — Null Explosion
**Enterprise:** MedTrack  
**Week:** 7  
**Failure type:** 40% of diagnosis codes become NULL after upstream system update

```sql
-- Story enforcer:
UPDATE diagnoses
SET icd10_code = NULL
WHERE id IN (
  SELECT id FROM diagnoses ORDER BY RANDOM()
  LIMIT (SELECT COUNT(*) * 0.40 FROM diagnoses)
);
```

**Student task:**
1. `pipelinekit run` → contract violation (not_null on icd10_code)
2. `pipelinekit diagnose` → identifies 40% NULL rate
3. Trace to upstream: which system sends diagnosis codes?
4. Implement NULL handling in dbt (COALESCE with 'UNKNOWN' + flag column)
5. Update contract: allow NULLs with documentation
6. Add quality check: alert if NULL rate exceeds 5% (not 40%)

**Assessment criteria:**
- Pipeline completes without contract violation
- NULL rate quality check in place
- Data dictionary updated with NULL handling explanation

---

### INCIDENT-007: CDC Failure — Slowly Changing Dimensions
**Enterprise:** CloudPulse  
**Week:** 8  
**Failure type:** Customer plan upgrades not captured — SCD Type 2 breaks

```sql
-- Story enforcer — simulates CDC missing updates:
UPDATE subscriptions
SET plan = 'enterprise', mrr = mrr * 3.2
WHERE plan = 'growth'
AND id IN (SELECT id FROM subscriptions ORDER BY RANDOM() LIMIT 80);
-- 80 subscriptions upgraded but no history preserved
```

**Student task:**
1. MRR report shows sudden spike that doesn't match sales records
2. Student identifies: no historical plan data preserved
3. Implement SCD Type 2 in dbt (dbt_utils.generate_surrogate_key)
4. Backfill: reconstruct history from audit logs
5. Set up contract: valid_from < valid_to on all SCD tables

**Assessment criteria:**
- SCD Type 2 implemented on subscriptions model
- Historical MRR accurately reconstructed
- Contract enforces temporal validity

---

### INCIDENT-008: GDPR Deletion Request
**Enterprise:** FinCore, RetailFlow  
**Week:** 9  
**Failure type:** 200 customer deletion requests arrive — pipeline must handle right-to-be-forgotten

```sql
-- Story enforcer — marks customers for deletion:
INSERT INTO deletion_requests (customer_id, requested_at, status)
SELECT id, NOW(), 'pending'
FROM customers ORDER BY RANDOM() LIMIT 200;
```

**Student task:**
1. Deletion requests arrive in new `deletion_requests` table
2. Current pipeline has no deletion handling
3. Implement: identify all tables containing customer PII
4. Build deletion cascade in dbt (mark records as deleted, anonymize PII)
5. Verify: deleted customers produce no PII in analytics output
6. Add to runbook: GDPR deletion SLA (72 hours per GDPR Article 17)

**Assessment criteria:**
- All PII removed from analytics tables for deleted customers
- Metrics still compute correctly (deleted customers excluded cleanly)
- Runbook documents GDPR deletion procedure

---

### INCIDENT-009: Timezone Bug
**Enterprise:** Any  
**Week:** 10  
**Failure type:** Server timezone change causes 24-hour offset in all timestamps

```sql
-- Story enforcer:
UPDATE transactions
SET created_at = created_at + INTERVAL '14 hours'
WHERE created_at > '2026-01-01';
-- Simulates UTC+14 → UTC shift causing future-dated transactions
```

**Student task:**
1. Daily revenue report shows no transactions for today
2. Tomorrow shows 2x transactions
3. `pipelinekit diagnose` → temporal anomaly detected
4. Identify root cause: timezone offset in ingestion layer
5. Fix: standardize all timestamps to UTC at ingestion in dlt pipeline
6. Update contract: freshness check must account for timezone

**Assessment criteria:**
- All timestamps in UTC after fix
- Revenue report shows correct daily totals
- Timezone standardization documented in ingestion/pipeline.py

---

### INCIDENT-010: Corrupted Batch
**Enterprise:** LogiTrack  
**Week:** 11  
**Failure type:** 3 hours of shipment events contain malformed JSON

```sql
-- Story enforcer:
UPDATE shipment_events
SET event_metadata = '{"status": null, "location": , "driver_id": "broken}'
WHERE created_at BETWEEN NOW() - INTERVAL '5 hours'
AND NOW() - INTERVAL '2 hours';
-- 3 hours of events have malformed metadata field
```

**Student task:**
1. `pipelinekit run` → dlt ingestion fails on malformed JSON
2. Error: `PK-ADAPTER-002` — dlt build failed
3. `pipelinekit diagnose` → identifies 3-hour window of bad data
4. Implement JSON validation in dbt (TRY_PARSE_JSON or COALESCE)
5. Set up quality check: alert if JSON parse failure rate > 0.1%
6. Backfill clean records after upstream fixes malformed batch

**Assessment criteria:**
- Pipeline handles malformed JSON gracefully (no hard failure)
- Quality alert configured
- Corrupted window documented in runbook

---

### INCIDENT-011: Decimal Precision Error
**Enterprise:** FinCore  
**Week:** 12  
**Failure type:** Float rounding causes $0.01 revenue discrepancy per transaction — $4,200 total

```sql
-- Story enforcer:
UPDATE transactions
SET amount = ROUND(amount::numeric, 1)  -- rounds to 1 decimal instead of 2
WHERE created_at > NOW() - INTERVAL '30 days';
-- Float64 rounding: $127.456 → $127.5 instead of $127.46
```

**Student task:**
1. Finance audit: total revenue is $4,200 higher than should be
2. No obvious cause — all transactions look correct individually
3. `pipelinekit architect analyze` → suggests data type audit
4. Identify: amount column using FLOAT not NUMERIC(10,2)
5. Fix: change column type in dbt model to NUMERIC(10,2)
6. Update contract: amount precision rule

**Assessment criteria:**
- amount column is NUMERIC(10,2) in all dbt models
- Revenue reconciliation matches to the cent
- Contract enforces decimal precision

---

### INCIDENT-012: The Certification Incident (Final Assessment)
**Enterprise:** Random assignment from Enterprises 1-6  
**Week:** Final  
**Failure type:** CLASSIFIED — student does not know which incidents are active

```
The student receives:
"Your company's analytics platform has experienced multiple incidents.
Your job is to find them, fix them, and document the recovery.
You have 4 hours. The dashboard is wrong. The business is waiting."

Active incidents (randomly selected, unknown to student):
- 3 of the 11 incidents above are active simultaneously
- Student must identify all three without being told what to look for
- Student uses: pipelinekit health → diagnose → architect → manual investigation
```

**Certification criteria (all required):**
- All 3 incidents identified within 4 hours
- All 3 incidents recovered (pipeline green, contracts passing)
- Runbook updated with root cause and prevention for each
- AI diagnosis used and cited in runbook

**This is the pilot simulator certification. Not a quiz. Not multiple choice. Recovery under pressure.**

---

## ASSESSMENT DATASETS

Every graded exercise requires a deterministic dataset — same seed, same failure, same correct answer across all students.

### Assessment Pack Standard

```json
"_meta": {
  "domain": "PipelineKit Academy Assessment",
  "seed": 42,
  "assessment_id": "ASSESS-001",
  "expected_outcomes": {
    "row_count_transactions": 4200,
    "revenue_pre_fix": 534821.47,
    "revenue_post_fix": 498234.12,
    "null_rate_icd10": 0.40,
    "duplicate_customer_count": 50
  }
}
```

Every assessment outcome is pre-computed and stored. Grading is automated: student's pipeline output is compared against expected values.

### Assessment Datasets Required

| Assessment | Enterprise | Incident | Seed | Expected outcome |
|---|---|---|---|---|
| ASSESS-001 | FinCore | Revenue Mismatch | 42 | Revenue = $498,234.12 |
| ASSESS-002 | MedTrack | Null Explosion | 42 | NULL rate = 40.0% |
| ASSESS-003 | RetailFlow | Duplicate PKs | 42 | 50 duplicates exactly |
| ASSESS-004 | CloudPulse | CDC Failure | 42 | 80 subscriptions affected |
| ASSESS-005 | LogiTrack | Corrupted Batch | 42 | 3-hour window corrupted |
| ASSESS-CERT | Random | 3 incidents | Random | All 3 recovered |

---

## PACK AUTHORING PRIORITY

| Priority | Pack | Purpose | Rows | SQR |
|---|---|---|---|---|
| **P0** | `academy-fincore` | Core curriculum, most students | 100,000 | 99/100 HIGH |
| **P0** | `academy-edumetrics` | EduNode Analytics integration demo | 60,000 | 99/100 HIGH |
| **P1** | `academy-cloudpulse` | SaaS learning path | 150,000 | 99/100 HIGH |
| **P1** | `academy-retailflow` | E-commerce learning path | 200,000 | 99/100 HIGH |
| **P2** | `academy-medtrack` | Healthcare learning path | 50,000 | 99/100 HIGH |
| **P2** | `academy-logitrack` | Operations learning path | 80,000 | 99/100 HIGH |
| **P3** | Assessment packs (6) | Graded exercises | 10,000 each | 100/100 HIGH |

---

## INCIDENT LIBRARY AUTHORING NOTES

Incidents are RealityDB Story Enforcer scripts — post-generation SQL UPDATE/INSERT that introduce precise failures. Rules from MedCore lessons:

1. **Filter on name columns, not id columns** — root table sizing is variable; `name` is bounded by enum values. Use `WHERE merchant_name = 'MidState Financial'` not `WHERE id = 'abc-123'`.

2. **One temporal anchor per table** — incidents that manipulate timestamps must target only one timestamp column. Two independent timestamps = temporal_logic 51/100.

3. **Incidents must be reversible** — every enforcer has a corresponding recovery script. Recovery = the student's assignment.

4. **Pre-compute expected outcomes** — before finalizing an incident, run it and record the exact expected metric values. These become the assessment rubric.

5. **Incidents stack for certification** — the final certification runs 3 incidents simultaneously. Design incidents that do not interfere with each other at the SQL level.

---

## THE STRATEGIC POSITION

```
RealityDB                    PipelineKit
Synthetic Enterprise    →    AI-Native OS
Generator                    for Trusted Analytics
     │                             │
     └──────────────┬──────────────┘
                    │
                    ▼
          PipelineKit Academy
          Simulation-Based
          Analytics Engineering
                    │
                    ▼
            Certification
            12 Incidents Recovered
                    │
                    ▼
          Enterprise Training
          University Programs
          Bootcamp Partnerships
```

**What competitors cannot replicate:**

A competitor can copy PipelineKit's CLI. They can copy RealityDB's pack format. They cannot easily replicate the *combination* — an AI-native operating system for analytics pipelines paired with a synthetic enterprise generator that produces deterministic, research-backed failures for pedagogical purposes.

The moat is not the tools. It is the simulator.

---

*Document: PIPELINEKIT-ACADEMY-SYNTHETIC-DATA-REQUIREMENTS.md*  
*Companion: PIPELINEKIT-SYNTHETIC-DATA-REQUIREMENTS.md (engineering needs)*  
*Next: PIPELINEKIT-ACADEMY-SYNTHETIC-DATA-REQUIREMENTS-EDUCATION.md (MathAthlone, MathPivot, SQL Learn integration)*
