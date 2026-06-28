# Role Disambiguation

The existing OntoGuard Role model uses flat RBAC (Reader, Updater, Admin), which conflates three separate concepts that the enterprise ontology community requires to be distinct: **AccessRole** — a system-level permission proxy (e.g. ReadOnlyUser, Updater); **OccupationalPost** — a position a person holds in an organisation (e.g. Doctor, CaseWorker); and **ActorGuise** — a context-specific guise in which an agent acts (e.g. Jim acting as Doctor in this encounter). Collapsing these into a single role type loses the ability to express who someone is, what they are permitted to do, and how they are acting in a given context as independent, composable facts.

When these three concepts are merged, real bugs appear at system integration boundaries — for example, granting clinical authority because someone holds an admin permission, or denying access because an occupational title was mistaken for a system role.

This module aligns with the four-layer stack: **Sapiento** → **OntoEnact** → **OntoArc** → live graph.
