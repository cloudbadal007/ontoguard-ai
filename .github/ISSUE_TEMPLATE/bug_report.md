---
name: Bug Report
about: Create a report to help us improve OntoGuard
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## Steps to Reproduce

1. Load ontology: `...`
2. Validate action: `...`
3. See error: `...`

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

A clear and concise description of what actually happened.

## Environment

- **OS**: [e.g., Windows 10, macOS 13.0, Ubuntu 22.04]
- **Python Version**: [e.g., 3.10.5]
- **OntoGuard Version**: [e.g., 0.1.0]
- **Ontology Format**: [e.g., OWL/RDF, Turtle]

## Code Example

```python
# Minimal code example that reproduces the issue
from ontoguard import OntologyValidator

validator = OntologyValidator("path/to/ontology.owl")
result = validator.validate(...)
```

## Error Message

```
Paste the full error message or traceback here
```

## Additional Context

Add any other context about the problem here. For example:
- Does this happen with all ontologies or just specific ones?
- Are there any workarounds you've found?
- Related issues or discussions

## Checklist

- [ ] I have searched existing issues to ensure this bug hasn't been reported
- [ ] I have provided a minimal code example that reproduces the issue
- [ ] I have included all relevant environment information
