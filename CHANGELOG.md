# Changelog

All notable changes to OntoGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Placeholder for future features

### Changed
- Placeholder for future changes

### Fixed
- Placeholder for future bug fixes

## [0.1.0] - 2026-01-20

### Added
- Initial release of OntoGuard
- Core `OntologyValidator` class for validating actions against OWL ontologies
- `ValidationResult` Pydantic model for structured validation responses
- Command-line interface (CLI) with three commands:
  - `validate`: Validate a single action
  - `interactive`: Interactive REPL for testing
  - `info`: Show ontology information
- MCP (Model Context Protocol) server integration with FastMCP
- Four MCP tools:
  - `validate_action`: Validate if an action is allowed
  - `get_allowed_actions`: Query allowed actions for an entity
  - `explain_rule`: Explain business rules
  - `check_permissions`: Check role-based permissions
- Comprehensive test suite with 138+ tests
- Example ontologies:
  - `ecommerce.owl`: E-commerce system with business rules
  - `healthcare.owl`: Healthcare system with HIPAA-compliant rules
  - `finance.owl`: Banking system with regulatory compliance rules
- Integration examples for popular AI agent frameworks:
  - LangChain integration
  - AutoGen (Microsoft) integration
  - CrewAI integration
- Rich documentation:
  - Comprehensive README.md
  - Usage examples
  - API documentation
  - Integration guides
- GitHub workflow for automated testing
- Issue templates for bug reports and feature requests
- Contributing guidelines
- Code of Conduct

### Features
- OWL ontology loading and parsing
- Semantic action validation
- Role-based access control
- Business rule enforcement
- Constraint checking (amounts, temporal, etc.)
- Action suggestion for denied actions
- Detailed denial explanations
- Context-aware validation
- Support for multiple ontology formats (OWL, RDF, Turtle)

### Documentation
- README with quick start guide
- Example scripts demonstrating usage
- Integration examples for major frameworks
- MCP server usage guide
- API documentation in docstrings

[Unreleased]: https://github.com/cloudbadal007/ontoguard-ai/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cloudbadal007/ontoguard-ai/releases/tag/v0.1.0
