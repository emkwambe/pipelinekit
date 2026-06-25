# **PIPELINEKIT-IMPLEMENTATION ASSET \#2**

# **Repository Structure & Coding Standards**

---

# **Repository Layout**

pipelinekit/

├── cli/  
│   ├── init.py  
│   ├── run.py  
│   ├── validate.py  
│   ├── doctor.py  
│   ├── migrate.py  
│   └── report.py  
│  
├── adapters/  
│   ├── ingestion/  
│   │   └── dlt/  
│   │  
│   ├── transformation/  
│   │   └── dbt/  
│   │  
│   ├── quality/  
│   │   └── soda/  
│   │  
│   └── alerts/  
│       └── resend/  
│  
├── blueprints/  
│  
├── contracts/  
│  
├── observability/  
│  
├── migrations/  
│  
├── state/  
│  
├── ai/  
│  
├── tests/  
│  
├── docs/  
│  
└── examples/

---

# **Coding Standards**

Python Version:

3.11+

---

Formatting

black

---

Linting

ruff

---

Typing

mypy required

---

Testing

pytest

Minimum Coverage:

80%

---

# **Naming Rules**

Classes:

PascalCase

Functions:

snake\_case

Variables:

snake\_case

Constants:

UPPER\_CASE

---

# **Architecture Rules**

Rule 1

Adapters never call each other.

---

Rule 2

CLI never directly calls providers.

---

Rule 3

All provider interactions go through interfaces.

---

Rule 4

No vendor-specific logic outside adapters.

---

Rule 5

Contracts own truth.

AI never owns truth.

---

# **Documentation Requirements**

Every feature requires:

* architecture notes  
* examples  
* tests  
* acceptance criteria

before merge approval.

---

# **Branch Strategy**

main

develop

feature/\*

hotfix/\*

release/\*

