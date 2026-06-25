## **Artifact Capability Matrix**

| Artifact | Owner | Capability Standard | AI Permission | Human Validation | Exit Criteria |
| ----- | ----- | ----- | ----- | ----- | ----- |
| Constitution | Founder | Complete, internally consistent, non-contradictory | Read only | Architecture | Approved by founder |
| ADR | Architect | Decision rationale, alternatives considered, consequences documented | Draft | Architecture | Accepted ADR |
| PRD | Product | Complete business requirements, measurable outcomes, success metrics | Draft | Product | Scope frozen |
| TRD | Architect | Architecture fully traceable to PRD | Draft | Architecture | No unresolved technical gaps |
| Specification | Responsible Engineer | Defines one capability completely, independently implementable | Draft | Architecture | Engineering-ready |
| Contract | Runtime Engineer | Stable interface, versioned, backward compatibility defined | Generate | Engineering | Contract approved |
| Schema | Runtime Engineer | Validates all expected inputs and outputs | Generate | Engineering | Passes validation tests |
| Agent | AI Infrastructure | Ownership, responsibilities, guardrails, outputs clearly defined | Generate | Architecture | Agent executable |
| Skill | AI Infrastructure | Produces deterministic, reusable capability | Generate | Engineering | Repeatable results |
| Prompt | AI Infrastructure | Produces structured outputs matching schemas | Generate | Engineering | Passes prompt evaluation suite |
| Runtime | Runtime Engineer | Deployable, reproducible, observable | Generate | Engineering | Successfully deployed |
| Tests | Quality Engineer | Meaningful coverage of capability and failure modes | Generate | Engineering | CI passes |
| Documentation | Documentation Engineer | Matches implementation exactly | Generate | Product | No documentation drift |
| Customer Research | Product | Evidence-backed, source referenced | Generate | Product | Research accepted |
| Pricing | Founder | Financial assumptions justified by evidence | Draft | Founder | Pricing approved |

---

## **Capability Standards**

Every artifact should satisfy one or more capability standards.

### **C1 — Completeness**

The artifact defines everything required for its intended purpose.

### **C2 — Correctness**

The artifact contains no known factual or logical errors.

### **C3 — Consistency**

The artifact does not contradict the Constitution, ADRs, Specifications, or Contracts.

### **C4 — Traceability**

Every requirement can be traced to a higher-level decision.

### **C5 — Testability**

The artifact can be objectively verified.

### **C6 — Reusability**

The artifact can be reused without modification.

### **C7 — Determinism**

Repeated execution produces equivalent outcomes.

### **C8 — Minimalism**

Contains no unnecessary concepts or speculative content.

### **C9 — Evolvability**

Can be extended without breaking existing implementations.

### **C10 — AI Readiness**

The artifact is structured so an AI engineer can reliably consume it without additional clarification.

---

## **Development Rule**

An artifact is not considered complete because a human approved it.

An artifact is complete only when it satisfies its required capability standards.

Human validation confirms compliance with those standards rather than replacing them.

