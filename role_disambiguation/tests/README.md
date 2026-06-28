# Test Suite

Three automated tests verify that the SHACL enforcement layer correctly 
handles the three-construct Role split.

## Tests

### test_valid_jim_passes_shacl
Loads examples/jim_as_doctor.ttl against the SHACL shapes.
Jim has three correctly separated constructs: OccupationalPost, 
AccessPermission, and ActorGuise. Each is a separate node. 
No SHACL constraint fires.
Expected result: conforms = True.

### test_violation_agent_fails_shacl
Loads examples/agent_as_readonly.ttl against the SHACL shapes.
This instance deliberately collapses AccessPermission and OccupationalPost 
onto one node. This is the silent bug described in the README.
The SHACL constraint must catch and reject it.
Expected result: conforms = False.

### test_disjoint_classes_enforced
Programmatically checks that DoctorPost and ReadOnlyUser are not the same 
OWL class. Verifies that the owl:disjointWith axioms in role_types.ttl hold.
Expected result: assertion passes.

## How to run

pip install pyshacl rdflib pytest
pytest role_disambiguation/tests/ -v

## Expected output

test_valid_jim_passes_shacl        PASSED    [ 33%]
test_violation_agent_fails_shacl   PASSED    [ 66%]
test_disjoint_classes_enforced     PASSED    [100%]

3 passed
