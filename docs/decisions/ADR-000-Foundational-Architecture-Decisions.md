# **PipelineKit Architectural Decision Records (ADR)**

**Version:** 1.0  
**Status:** Foundational Architecture Decisions  
**Date:** June 24, 2026

---

# **Purpose**

Architectural Decision Records (ADRs) preserve the reasoning behind significant technical and product decisions.

An ADR is permanent institutional memory.

An accepted ADR supersedes informal discussions, meeting notes, and temporary implementation decisions.

Every architectural change after Version 1.0 must be documented through a new ADR.

---

# **ADR-001**

## **Standardize on dlt**

**Status**

Accepted

**Date**

2026-06-24

### **Context**

PipelineKit originally evaluated multiple ingestion technologies.

The product required:

* permissive licensing  
* Python-native development  
* AI friendliness  
* low operational complexity  
* deterministic execution

Airbyte introduced licensing uncertainty and operational overhead.

### **Decision**

PipelineKit adopts **dlt** as the standard ingestion and loading framework.

### **Consequences**

Benefits

* Apache 2.0 license  
* Python-native architecture  
* Simplified implementation  
* Better AI integration  
* Lower maintenance burden

Trade-offs

* Smaller enterprise connector ecosystem  
* Additional connector development may be required

---

# **ADR-002**

## **Remove Sling**

**Status**

Accepted

**Date**

2026-06-24

### **Context**

Sling provided an elegant orchestration layer but introduced licensing complexity and duplicated capabilities provided by dlt.

### **Decision**

PipelineKit will not depend on Sling.

Pipeline execution is standardized around:

* dlt  
* dbt Core  
* Soda  
* PipelineKit orchestration

### **Consequences**

Benefits

* Reduced dependency footprint  
* Simpler architecture  
* Lower legal risk

Trade-offs

* Loss of Sling-specific workflow features

---

# **ADR-003**

## **CLI-First Product**

**Status**

Accepted

### **Context**

Most competing products prioritize graphical interfaces.

PipelineKit targets engineers.

### **Decision**

Every feature shall be accessible from the command line.

Graphical interfaces are optional.

CLI functionality is mandatory.

### **Consequences**

Benefits

* Scriptability  
* Automation  
* AI compatibility  
* Developer productivity

---

# **ADR-004**

## **Local-First Architecture**

**Status**

Accepted

### **Context**

Many organizations require offline execution, private infrastructure, or regulated deployments.

### **Decision**

PipelineKit executes locally by default.

Cloud services remain optional.

### **Consequences**

Benefits

* Privacy  
* Performance  
* Offline operation  
* Enterprise adoption

---

# **ADR-005**

## **BYOK AI Policy**

**Status**

Accepted

### **Context**

Customers increasingly require flexibility in AI providers.

Vendor lock-in contradicts PipelineKit philosophy.

### **Decision**

PipelineKit never bundles or mandates a proprietary AI provider.

Customers configure their preferred provider.

Supported providers may include:

* OpenAI  
* Anthropic  
* Google Gemini  
* OpenRouter  
* Ollama  
* Local OpenAI-compatible servers

### **Consequences**

Benefits

* Customer ownership  
* Vendor neutrality  
* Future-proof architecture

Trade-offs

* Additional configuration complexity

---

# **ADR-006**

## **Multi-Model AI Architecture**

**Status**

Accepted

### **Context**

Different AI tasks require different optimization targets.

No single model is optimal for all workloads.

### **Decision**

PipelineKit separates AI responsibilities.

Small models perform:

* classification  
* summarization  
* structured extraction

Large reasoning models perform:

* diagnostics  
* remediation planning  
* root cause analysis

Model selection is configurable.

### **Consequences**

Benefits

* Lower cost  
* Better latency  
* Higher reasoning quality

---

# **ADR-007**

## **AI Is an Operator, Not an Owner**

**Status**

Accepted

### **Context**

PipelineKit is AI-native but must remain operationally safe.

### **Decision**

AI may:

* inspect  
* validate  
* diagnose  
* recommend  
* summarize  
* classify

AI shall not automatically:

* deploy  
* delete  
* migrate  
* modify production  
* rotate secrets  
* approve releases

Production changes require explicit human approval.

### **Consequences**

PipelineKit adopts a Human-on-the-Loop operating model.

---

# **ADR-008**

## **Deterministic Execution**

**Status**

Accepted

### **Context**

Analytics infrastructure must produce reproducible results.

### **Decision**

Given identical inputs, PipelineKit must produce identical execution behavior.

AI recommendations must never change deterministic pipeline execution.

### **Consequences**

Benefits

* Debuggability  
* Repeatability  
* Trust

---

# **ADR-009**

## **Human-Readable Infrastructure**

**Status**

Accepted

### **Context**

Generated infrastructure should remain maintainable without AI.

### **Decision**

Every generated artifact must be understandable and editable by an engineer.

Examples include:

* YAML  
* SQL  
* Python  
* Markdown

Opaque binary configuration is prohibited.

---

# **ADR-010**

## **Explainability Before Automation**

**Status**

Accepted

### **Context**

Automation without explanation reduces trust.

### **Decision**

Every diagnosis must include:

* evidence  
* reasoning  
* confidence  
* recommended action

PipelineKit explains before it automates.

---

# **ADR-011**

## **Trust Is the Primary Product Metric**

**Status**

Accepted

### **Context**

PipelineKit is not optimized for throughput alone.

Its purpose is trusted analytics.

### **Decision**

All new capabilities must improve at least one of:

* trust  
* reliability  
* explainability  
* diagnosability  
* developer productivity

Features that improve none of these should not be implemented.

---

# **ADR-012**

## **Product Boundary**

**Status**

Accepted

### **Context**

Product focus is essential for long-term execution.

### **Decision**

PipelineKit is:

* AI-native  
* CLI-first  
* trusted analytics infrastructure

PipelineKit is not:

* an ETL platform  
* a cloud platform  
* a notebook environment  
* a BI platform  
* a dashboard application  
* a workflow scheduling platform  
* a general-purpose AI assistant

Integrations are encouraged.

Category expansion beyond these boundaries requires a new ADR.

---

# **ADR Governance**

Every new ADR shall contain:

* ADR Number  
* Title  
* Status  
* Date  
* Context  
* Decision  
* Alternatives Considered  
* Consequences  
* Principle Alignment  
* Superseded ADRs (if applicable)

---

# **Architectural Rule**

An accepted ADR becomes part of the PipelineKit Constitution.

Implementation must conform to accepted ADRs.

If implementation requires violating an ADR, the ADR must be amended before code is changed.

Architecture evolves through decisions—not through undocumented implementation.

