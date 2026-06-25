# **PipelineKit Documentation Lifecycle Standard**

## **Purpose**

Every file in the repository must have a defined lifecycle.

This prevents premature documentation, unnecessary maintenance, and AI-generated content that lacks sufficient implementation context.

---

# **Lifecycle Categories**

## **Level A — Foundational (Complete Before Development)**

These documents define the product.

They must be complete before writing production code.

After approval, they should change only through deliberate architectural decisions.

Examples

* Product Constitution  
* PRD  
* TRD  
* ADRs  
* AI Model Strategy  
* Product Philosophy  
* Specifications  
* Contracts  
* Schemas

Author

Founder

Reviewer

Architecture Review

AI Permission

Read-only.

AI may reference these documents but must not modify them unless explicitly instructed.

---

## **Level B — Living Documentation**

These evolve throughout the life of the project.

Examples

* Customer Interviews  
* Pricing Experiments  
* Market Intelligence  
* Category Thesis  
* Runtime Guides  
* CLI Reference  
* Release Notes

Author

Founder

Engineering Team

AI

Reviewer

Product Owner

Engineering

AI Permission

May update.

Changes should always reflect actual implementation or validated research.

---

## **Level C — Generated Documentation**

These are produced from code or automation.

Never edit manually.

Examples

* API Documentation  
* CLI Help  
* Command Reference  
* Configuration Reference  
* JSON Schema Documentation  
* Coverage Reports

Author

Automation

AI

Reviewer

None

Regenerate instead of editing.

---

## **Level D — Implementation Placeholders**

These intentionally remain incomplete until implementation reaches the appropriate phase.

Examples

runtime/

Dockerfiles

Deployment Guides

Production Architecture

Provider Examples

MCP Configurations

Workflow YAML

Agent Skills

Prompt Libraries

Developer Examples

Author

Assigned Engineering Agent

When

Only when implementation begins.

AI Permission

May generate only after the corresponding Specification exists and implementation has started.

---

## **Level E — Historical Archive**

Never edited.

Preserved only for traceability.

Examples

Archived Specifications

Deprecated ADRs

Retired Product Concepts

Old Sprint Plans

Author

Historical

AI Permission

Read-only.

---

# **Ownership Matrix**

| Area | Primary Owner | AI May Write | Human Review |
| ----- | ----- | ----- | ----- |
| Constitution | Founder | No | Required |
| ADRs | Founder / Architect | Draft only | Required |
| PRD | Founder | Draft only | Required |
| TRD | Architect | Draft only | Required |
| Specifications | Architect | Draft | Required |
| Contracts | Runtime Engineer | Yes | Required |
| Schemas | Runtime Engineer | Yes | Required |
| Runtime | Runtime Engineer | Yes | Required |
| Agents | AI Infrastructure | Yes | Required |
| Skills | AI Infrastructure | Yes | Required |
| Prompts | AI Infrastructure | Yes | Required |
| Customer Interviews | Product | Yes | Required |
| Market Intelligence | Product | Yes | Required |
| Pricing | Founder | Draft | Required |
| Release Notes | Release Engineer | Yes | Optional |

---

# **Current Repository Status**

## **Complete (Development May Depend On)**

* Constitution  
* ADRs  
* PRD  
* TRD  
* Specifications  
* Philosophy  
* AI Strategy  
* Institutional Memory  
* Contracts  
* Initial Schemas

---

## **Intentionally Placeholder**

These should remain minimal until implementation requires them.

* runtime/  
* .mcp/configs/  
* .mcp/servers/  
* prompts/  
* skills/  
* examples/  
* src/  
* tests/

Their structure is complete.

Their contents should emerge from implementation rather than speculation.

---

## **Generated Later**

The following should not be written manually.

* API Reference  
* CLI Reference (generated from implementation)  
* Command Help  
* Configuration Documentation  
* Test Coverage Reports  
* Release Changelog  
* Performance Benchmarks

---

# **Golden Rule**

Documentation should never run ahead of implementation.

Architecture may lead implementation.

Implementation may lead generated documentation.

Generated documentation should never become hand-maintained.

Every document must have a clear owner, lifecycle, and purpose.

