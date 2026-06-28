# PipelineKit Research Prompt
## For multi-model review — paste this entire prompt to any AI model

---

You are a senior researcher and product strategist with deep expertise in:
- Data engineering tooling and the modern data stack
- B2B SaaS go-to-market strategy
- Developer tool pricing and adoption
- Enterprise compliance and governance
- East African fintech and regulatory landscape
- AI-native product development

I am building **PipelineKit** — an AI-native coordination layer that sits above dbt, Snowflake, Airbyte, dlt, and Soda. It provides Engineering Management Systems (EMSs) that package organizational engineering knowledge into installable, version-controlled capabilities.

The full research agenda is at:
https://github.com/emkwambe/pipelinekit/blob/main/docs/reference/RESEARCH-AGENDA.md

Read it before answering. Then answer every question below as precisely as possible, citing sources where you can. Flag where you are uncertain. Disagree with my assumptions where the evidence suggests I am wrong.

---

## SECTION 1: Market Reality Check

### Q1 — The Setup Tax (Research item R-001)

My current claim: "Data engineers spend 2 weeks on pipeline setup before writing business logic."

- Is 2 weeks an accurate median, or is the real number different?
- What percentage of setup time is ingestion vs transformation vs quality vs governance?
- At a blended rate of $150/hour for a senior engineer, what is the dollar cost of this setup per project?
- Does setup time scale with team size, or does it stay roughly constant?
- What is the most credible public source I can cite for this claim?

Flag if my 2-week assumption is wrong and give me the correct framing.

---

### Q2 — Who Actually Buys (Research item R-002)

I am targeting three buyer types:
- ICP-001: Solo analytics engineer / freelance consultant
- ICP-002: Analytics consultancy (2-10 engineers)
- ICP-003: Internal data team (5-50 engineers, enterprise)

For each ICP:
- Who actually makes the purchase decision?
- At what price point does a procurement process become required?
- What is the typical sales cycle length?
- What evidence or proof does each buyer type need before committing?
- What is the most common objection at the moment of purchase?

---

### Q3 — The Airbyte/Fivetran Migration Trigger (Research item R-003)

My assumption: Pricing changes are the primary migration trigger.

- Is pricing actually the #1 migration trigger, or is it reliability, support quality, or feature gaps?
- What percentage of Airbyte/Fivetran users are actively considering migration right now (mid-2026)?
- What has stopped people who considered migration from completing it?
- What is the average connector count for a team actively migrating?
- How long do teams estimate migration would take without dedicated tooling?
- What is the most credible community source (Reddit threads, surveys) for migration intent data?

---

### Q4 — East African Data Engineering Market (Research item R-004)

- How many data engineers are currently employed in Kenya, Tanzania, Nigeria, South Africa?
- What data warehousing tools are dominant in East African enterprises (Snowflake vs BigQuery vs Postgres-only)?
- What is the typical data team size at a Kenyan or Nigerian fintech?
- What specific CBK (Central Bank of Kenya) regulations require data pipeline governance?
- What equivalent regulations exist in Tanzania (BOT), Nigeria (CBN), South Africa (SARB)?
- What is a realistic PPP-adjusted price point for a data tool in East African markets?
- Are there active data engineering communities in Nairobi, Lagos, or Dar es Salaam?

---

## SECTION 2: Competitive Landscape

### Q5 — True Competition (Research item R-006)

I claim PipelineKit's primary competition is "doing it manually" and that it complements rather than competes with dbt, Airflow, Dagster, and Monte Carlo.

- Is this framing accurate or is there a more direct competitor I am missing?
- Where specifically does Dagster overlap with PipelineKit's coordination layer positioning?
- Where does dbt Cloud's governance features end and PipelineKit's governance capabilities begin?
- What does Monte Carlo offer that overlaps with our Observability Management System?
- What are the top 5 objections a prospect raises when comparing PipelineKit to "just using Dagster"?
- Is there any existing blueprint registry or pipeline template marketplace I should know about?

---

### Q6 — dlt Ecosystem (Research item R-007)

PipelineKit uses dlt as its primary ingestion layer.

- What is dlt's current adoption rate among data engineers? (GitHub stars, PyPI downloads, community size)
- What percentage of data engineers have heard of dlt vs have used it in production?
- What are the most common complaints about dlt that would affect PipelineKit blueprint reliability?
- What are the top 10 most-used dlt sources?
- Is dlt adoption growing fast enough that using it as a foundation is a strategic asset, or is it a risk?

---

### Q7 — Quality Layer Choice (Research item R-008)

PipelineKit uses Soda Core as its quality layer.

- What quality tool do most data engineers actually use today: dbt tests, Great Expectations, Soda, or custom?
- What is Soda Core's adoption rate vs Soda Cloud vs competitors?
- Would a prospect who uses Great Expectations feel friction with a Soda-first approach?
- Should PipelineKit support multiple quality backends or commit to Soda?
- What are the top 5 data quality checks that engineers actually enforce in production?

---

## SECTION 3: Technical and Standards

### Q8 — Data Contract Standards (Research item R-009)

I have built a proprietary YAML-based contract format.

- What is the current adoption rate of the Open Data Contract Standard (ODCS)?
- How does ODCS compare to dbt contracts and Soda contracts?
- Should PipelineKit contracts be ODCS-compatible? What are the tradeoffs?
- What are the top 5 fields that engineers actually enforce in production contracts?
- What contract violations are most commonly caught in real production pipelines?

---

### Q9 — Blueprint Verification Standards (Research item R-011)

My current verification claim: "43/43 dbt tests passed locally in 1 minute using synthetic seed data."

- Is dbt test count the right metric for blueprint trust, or is there a better standard?
- What would make an engineer trust a blueprint enough to use it on a client project?
- Are there existing standards for data pipeline template certification I should align with?
- How do tools like dbt packages establish trust? What can we learn from their approach?

---

### Q10 — AI Diagnosis Accuracy (Research item R-012)

Our DiagnosticsEngine returns confidence scores between 0.00 and 1.00.

- What confidence threshold do engineers actually trust for AI-generated recommendations?
- What is the right way to present an AI confidence score so it increases rather than decreases trust?
- What failure patterns in data pipelines are hardest for AI to diagnose correctly?
- How do comparable AI diagnostic tools in adjacent spaces (software debugging, infrastructure) present uncertainty?

---

## SECTION 4: Regulatory Compliance

### Q11 — SOC 2 Pipeline Requirements (Research item R-013)

I am planning a SOC 2 Control Mapping capability (CM-1).

- What specific SOC 2 Type II Trust Services Criteria apply to data pipeline infrastructure?
- What evidence do auditors actually request for data pipeline compliance?
- Which of these control families are most commonly failed in data engineering contexts: CC6 (Logical Access), CC7 (System Operations), CC8 (Change Management), or A1 (Availability)?
- What tools do SOC 2-compliant organizations currently use for pipeline evidence collection?
- What is the minimum viable SOC 2 compliance capability that would satisfy an enterprise buyer's security questionnaire?

---

### Q12 — CBK and East African Regulatory Requirements (Research item R-014)

I am planning a CBK Compliance Package (CM-5) for the East African market.

- What specific Central Bank of Kenya regulations require data pipeline governance?
- What data residency requirements apply (must data stay in Kenya)?
- What audit trail requirements exist for regulated financial data pipelines?
- What equivalent regulations exist in Tanzania (BOT), Nigeria (CBN), South Africa (SARB)?
- What existing compliance frameworks (ISO 27001, NIST CSF, PCI DSS) are most relevant for East African fintechs?

---

## SECTION 5: Pricing and Business Model

### Q13 — Pricing Benchmarks (Research item R-015)

My current pricing:
- Solo: $99/month (1 user, public registry)
- Team: $499/month (5 users, private registry)
- Enterprise: $2,500+/month (unlimited, SSO, SLA)

- How does this compare to dbt Cloud, Monte Carlo, Soda Cloud, Prefect, and Dagster pricing?
- What is the typical data engineering tool budget for a 5-person team annually?
- What pricing model converts best for developer CLI tools (per seat, per pipeline, per usage, flat fee)?
- At what price point does a solo consultant need manager approval?
- What is the right East African PPP-adjusted pricing for each tier?
- Is there a freemium tier I should be offering that I am not?

---

### Q14 — Academy Pricing (Research item R-016)

I am planning a training platform (PipelineKit Academy) at:
- $299/month per student
- $5,000-25,000/semester for university licenses
- $10,000-50,000 per corporate training cohort

- How does this compare to DataCamp, dbt Learn, Coursera data engineering, and Pluralsight?
- What is the typical university budget for technology curriculum licensing?
- What evidence does a university need to adopt a new tool in their data engineering curriculum?
- What certification is most valued in the data engineering job market right now?
- What is the corporate training budget per employee for data engineering upskilling?

---

## SECTION 6: User Experience

### Q15 — CLI vs GUI (Research item R-017)

PipelineKit is CLI-first with no GUI.

- What percentage of data engineers prefer CLI tools vs GUI tools for pipeline management?
- At what team size does the preference typically shift from CLI to GUI?
- What CLI tools do data engineers use daily (dbt, git, poetry, docker)?
- Would a VS Code extension significantly expand our addressable market?
- What is the risk of being CLI-only for ICP-002 (analytics consultancies)?

---

### Q16 — First 10 Minutes (Research item R-018)

I claim a new user can get to a successful pipeline run in under 10 minutes.

- Is 10 minutes a realistic benchmark for a CLI data tool first-run experience?
- What is the typical time-to-value for comparable developer tools (dbt, Airbyte, Prefect)?
- What are the most common failure points in data engineering tool onboarding?
- What does the ideal first-run experience look like for a CLI-first data tool?
- What should "success" mean in the first 10 minutes — a run that completes, or something more meaningful?

---

## SECTION 7: What I Am Missing

### Q17 — Gaps in My Research Agenda

Read the full research agenda at the URL above.

- What important research questions am I missing entirely?
- Which of my current assumptions are most likely to be wrong based on what you know?
- Which research items would have the highest impact on product decisions if answered incorrectly?
- What would you add to the P0 priority list that is not currently there?
- Is there a research question that would invalidate the entire PipelineKit positioning if answered incorrectly?

---

## SECTION 8: The Synthesis Question

### Q18 — The One Question That Matters Most

If you could only answer one of the research questions above before we start design partner outreach — which one would it be and why?

What is the single assumption in PipelineKit's current positioning that is most likely to be wrong, and what evidence would you look for to verify or refute it?

---

## Instructions for Your Response

- Answer each numbered question directly. Do not combine answers.
- Cite sources where you can (reports, surveys, documentation, community data).
- Flag uncertainty explicitly — "I am not certain about this" is more useful than a confident wrong answer.
- Disagree with my assumptions where evidence suggests I am wrong. Disagreement is the point of this exercise.
- For East African questions, flag if your training data on this region is limited.
- For regulatory questions, flag that this is not legal advice and requires verification with qualified legal counsel.
- Prioritize accuracy over comprehensiveness — a precise answer to 5 questions is more useful than a vague answer to 18.

The goal of this research is to close the gap between what we assume and what is true — so that every SPEC we write and every design partner conversation we have is grounded in verified market reality.
