> Part of [ontoguard-ai](https://github.com/cloudbadal007/ontoguard-ai) — 
> semantic firewall for AI agents using OWL and SHACL enforcement.

# Role Disambiguation

Many systems model access control with flat RBAC labels (such as Reader, Updater, and Admin). That approach treats three different ideas as one:

| Concept | What it means | Typical examples |
|---|---|---|
| **AccessRole** | A system-level permission proxy — what the platform allows an account to do | ReadOnlyUser, Updater, Admin |
| **OccupationalPost** | A position held in an organisation — what job or formal role someone has | Doctor, CaseWorker, Analyst |
| **ActorGuise** | A context-specific way someone is acting in one situation — who they are *for this interaction* | Acting as clinician in encounter E1, acting as approver in workflow step 42 |

When these are collapsed into a single "role" field, you can no longer express three independent facts: **who someone is in the organisation**, **what the system permits them to do**, and **how they are acting in a given context**.

That loss shows up as real defects at integration boundaries — for example, granting operational authority because an account has an admin permission, or denying access because a job title was treated as a login role.

This module keeps the three concepts separate in the ontology, enforces the separation with SHACL shapes, and provides passing and failing examples plus tests. It aligns with the four-layer stack: **EA Governance** → **Formal Proof** → 
**Adapter and Enforcement** → **Live Graph**.

## Contents

| Path | Purpose |
|---|---|
| `ontology/role_types.ttl` | OWL classes, properties, and disjointness axioms |
| `shacl/role_constraints.shacl.ttl` | Validation rules that prevent role collapse |
| `examples/jim_as_doctor.ttl` | Valid instance: separate job, system permission, and encounter guise |
| `examples/agent_as_readonly.ttl` | Deliberate violation for testing |
| `tests/test_role_disambiguation.py` | Automated SHACL and ontology checks |
| `tests/README.md` | Detailed walkthrough of the test suite |

## Run tests

```bash
pip install pyshacl rdflib pytest
pytest role_disambiguation/tests/ -v
```
