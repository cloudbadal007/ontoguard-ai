# Run: pytest role_disambiguation/tests/test_role_disambiguation.py -v
# Requires: pip install pyshacl rdflib pytest

from pathlib import Path

import pyshacl
from rdflib import Graph, Namespace
from rdflib.namespace import OWL, RDF

ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY = ROOT / "ontology" / "role_types.ttl"
SHACL = ROOT / "shacl" / "role_constraints.shacl.ttl"
JIM = ROOT / "examples" / "jim_as_doctor.ttl"
VIOLATION = ROOT / "examples" / "agent_as_readonly.ttl"

ONTO = Namespace("http://ontoarc.ai/ontology/roles#")


def _load_graph(*paths: Path) -> Graph:
    graph = Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def _validate(data_paths: list[Path]) -> tuple[bool, str]:
    data_graph = _load_graph(*data_paths)
    shacl_graph = _load_graph(SHACL)
    conforms, _, report_text = pyshacl.validate(
        data_graph=data_graph,
        shacl_graph=shacl_graph,
        inference="rdfs",
        advanced=True,
    )
    return conforms, report_text


def test_valid_jim_passes_shacl() -> None:
    conforms, _ = _validate([ONTOLOGY, JIM])
    assert conforms is True


def test_violation_agent_fails_shacl() -> None:
    conforms, report_text = _validate([ONTOLOGY, VIOLATION])
    assert conforms is False
    assert report_text


def test_disjoint_classes_enforced() -> None:
    graph = _load_graph(ONTOLOGY)

    assert ONTO.DoctorPost != ONTO.ReadOnlyUser
    assert (ONTO.DoctorPost, RDF.type, ONTO.OccupationalPost) in graph
    assert (ONTO.ReadOnlyUser, RDF.type, ONTO.AccessRole) in graph

    disjoint_sets = list(graph.subjects(RDF.type, OWL.AllDisjointClasses))
    assert disjoint_sets, "Expected owl:AllDisjointClasses axiom in ontology"

    members_list = graph.value(disjoint_sets[0], OWL.members)
    members = set(graph.items(members_list))
    assert members == {ONTO.AccessRole, ONTO.OccupationalPost, ONTO.ActorGuise}
