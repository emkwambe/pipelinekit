# **PIPELINEKIT-AI & Model Strategy Standard**

## **Version 1.0**

### **Official Guidance for AI, LLMs, Agents, and Model Selection**

---

# **Executive Summary**

PipelineKit is not an AI product.

PipelineKit is a Trusted Analytics Infrastructure platform.

AI exists to improve:

* diagnosis  
* remediation  
* onboarding  
* observability  
* migration

AI does not replace:

* contracts  
* quality checks  
* deterministic validation  
* observability

PipelineKit follows:

## **Deterministic First**

## **AI Second**

Every AI recommendation must be grounded in observable evidence.

---

# **AI Design Principles**

## **Principle 1**

Trust Before Intelligence

Incorrect automation is worse than no automation.

PipelineKit must prioritize:

* correctness  
* explainability  
* reproducibility

before intelligence.

---

## **Principle 2**

Deterministic Systems Own Truth

The following systems are authoritative:

Data Contracts

Quality Checks

dbt Tests

Observability Reports

Execution Logs

Pipeline State

AI interprets.

AI never defines truth.

---

## **Principle 3**

Model Agnostic Architecture

PipelineKit must never depend on:

* OpenAI  
* Anthropic  
* Google  
* DeepSeek  
* Ollama

directly.

Models are replaceable providers.

---

# **AI Capability Roadmap**

## **Phase 1**

AI-Assisted Diagnostics

Status:

MVP

Capabilities:

* summarize failures  
* classify incidents  
* identify likely root causes  
* explain contract violations

No autonomous actions.

---

## **Phase 2**

AI Recommendations

Capabilities:

* suggest remediation  
* generate runbooks  
* suggest contract updates  
* propose quality checks

Human approval required.

---

## **Phase 3**

AI Operators

Capabilities:

* automated investigation  
* evidence gathering  
* dependency analysis  
* migration planning

Human approval required.

---

## **Phase 4**

Self-Healing Workflows

Capabilities:

* approved remediation execution  
* rollback workflows  
* alert routing

Enterprise only.

---

# **Official Model Architecture**

PipelineKit uses:

## **Thinkers**

Deep reasoning models.

## **Sprinters**

High-volume operational models.

## **Local Models**

Privacy-first deployments.

---

# **Model Classes**

## **Class A**

Sprinter Models

Purpose:

Fast classification.

Tasks:

* log classification  
* issue categorization  
* contract summaries  
* alert enrichment

Requirements:

Fast

Cheap

Reliable JSON

Examples:

GPT-4o Mini

Gemini Flash

Claude Haiku

Qwen Small

---

## **Class B**

Thinker Models

Purpose:

Root cause analysis.

Tasks:

* diagnosis  
* dependency tracing  
* remediation planning  
* migration analysis

Requirements:

Deep reasoning

Long context

Strong tool usage

Examples:

GPT-5

Claude Opus

DeepSeek Reasoning Models

Future equivalents

---

## **Class C**

Local Models

Purpose:

Air-gapped deployments.

Tasks:

* diagnostics  
* summaries  
* migrations  
* contract generation

Requirements:

Local execution

Structured output

Tool calling

Examples:

Qwen

Phi

Gemma

Llama

---

# **Official AI Architecture**

                 PIPELINEKIT

                         │  
                         ▼

              Evidence Collection Layer

                         │

     ┌───────────────────┼───────────────────┐

     ▼                   ▼                   ▼

 Execution Logs     Contracts         Quality Results

     ▼                   ▼                   ▼

            Structured Evidence Package

                         │

                         ▼

                 AI Decision Layer

                         │

     ┌───────────────────┼───────────────────┐

     ▼                   ▼                   ▼

  Sprinter          Thinker            Local Model

                         │

                         ▼

              Structured Recommendation

                         │

                         ▼

                    Human Review

                         │

                         ▼

                   Approved Action

---

# **Structured Output Standard**

Every AI response must follow:

{  
  "status": "success",  
  "finding\_type": "schema\_drift",  
  "confidence": 0.91,  
  "evidence": \[\],  
  "impact": "",  
  "recommended\_actions": \[\],  
  "can\_auto\_fix": false  
}

No free-form prose.

No markdown.

No explanations outside JSON.

---

# **Diagnose Command**

## **Purpose**

Primary AI feature.

Command:

pipelinekit diagnose

Input:

* logs  
* contracts  
* quality results  
* observability reports

Output:

{  
  "status": "diagnosis\_complete",  
  "root\_cause": "column\_removed",  
  "confidence": 0.94,  
  "affected\_models": \[  
    "stg\_orders",  
    "fct\_revenue"  
  \],  
  "recommended\_actions": \[  
    "update contract",  
    "modify model"  
  \]  
}

---

# **Migration Assistant**

Command:

pipelinekit migrate

AI Tasks:

* analyze current stack  
* identify dependencies  
* generate migration plans  
* estimate effort

Human approves execution.

---

# **Contract Assistant**

Command:

pipelinekit contract generate

AI Tasks:

* inspect schema  
* suggest contracts  
* generate quality checks

Human approves publication.

---

# **Observability Assistant**

Command:

pipelinekit doctor \--ai

AI Tasks:

* summarize incidents  
* identify recurring failures  
* explain trends

Human reviews output.

---

# **AI Safety Rules**

AI may:

✓ Recommend

✓ Explain

✓ Summarize

✓ Investigate

✓ Prioritize

---

AI may not:

✗ Modify production data

✗ Change contracts automatically

✗ Disable quality checks

✗ Ignore contract violations

✗ Override human approval

---

# **Model Selection Policy**

## **Default Cloud Configuration**

Sprinter:

GPT-4o Mini

Thinker:

GPT-5

Reason:

Strong ecosystem

Reliable tool calling

Reliable structured output

---

## **Alternative Cloud Configuration**

Sprinter:

Gemini Flash

Thinker:

Claude Opus

Reason:

Cost optimization

Provider diversity

---

## **Local Configuration**

Sprinter:

Qwen

Thinker:

Qwen Large or Phi

Reason:

Air-gapped environments

Maximum privacy

---

# **Vendor Lock-In Prevention**

Every provider implements:

class LLMProvider:

    def diagnose(self):  
        pass

    def summarize(self):  
        pass

    def recommend(self):  
        pass

    def generate\_contract(self):  
        pass

No provider-specific code outside adapters.

---

# **AI Success Metrics**

Measure:

Diagnosis Accuracy

False Positive Rate

Recommendation Acceptance Rate

Time to Diagnosis

Time to Recovery

Human Override Rate

---

# **Strategic Rule**

PipelineKit competes on:

Trusted Analytics

Blueprint Intelligence

Observability

Migration

Operational Knowledge

PipelineKit does NOT compete on:

Who has the biggest model.

Models will change.

Trusted analytics infrastructure remains valuable.

---

# **Final AI Mission**

AI exists to reduce:

Time-to-Diagnosis

Time-to-Recovery

Time-to-Trusted-Data

without sacrificing trust, transparency, or human control.

AI is an accelerator.

Not the product.

The product is Trusted Analytics Infrastructure.

