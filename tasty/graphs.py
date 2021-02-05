import os

from typing import List
from rdflib import Graph
from rdflib.namespace import Namespace

import tasty.constants as tc


def get_versioned_graph(schema: str, version: str) -> Graph:
    """
    Get an empty Graph with the correct namespaces loaded

    :param schema: [str] A valid key from SUPPORTED_SCHEMAS
    :param version: [str] A valid version from SUPPORTED_SCHEMAS
    :return:
    """
    g: Graph = Graph()
    bind_prefixes(g)
    valid = is_valid_schema_and_version(schema, version)
    if valid:
        bind_versioned_prefixes(g, schema, version)
    return g


def load_ontology(schema: str, version: str) -> Graph:
    """
    Load an ontology and return as Graph with the correct namespaces
    :param schema: [str] A valid key from SUPPORTED_SCHEMAS
    :param version: [str] A valid version from SUPPORTED_SCHEMAS
    :return:
    """
    g = get_versioned_graph(schema, version)
    schema_path = os.path.join(tc.SCHEMAS_DIR, schema.lower())
    if schema == 'Haystack':
        schema_path = os.path.join(schema_path, f"defs_{version.replace('.','_')}.ttl")
    elif schema == 'Brick':
        schema_path = os.path.join(schema_path, f"Brick_{version.replace('.','_')}.ttl")
    with open(schema_path, 'r') as f:
        data = f.read()
    g.parse(data=data, format='ttl')
    return g


def bind_versioned_prefixes(graph: Graph, schema: str, version: str) -> None:
    """

    :param graph: [rdflib.Graph]
    :param schema: [str] A valid key from SUPPORTED_SCHEMAS
    :param version: [str] A valid version from SUPPORTED_SCHEMAS
    :return:
    """
    if schema == 'Brick':
        if version == '1.1':
            graph.bind("brick", tc.BRICK_1_1)
            graph.bind("tag", tc.TAG_1_1)
            graph.bind("bsh", tc.BSH_1_1)
    elif schema == 'Haystack':
        if version == '3.9.9':
            graph.bind("ph", tc.PH_3_9_9)
            graph.bind("phIct", tc.PHICT_3_9_9)
            graph.bind("phScience", tc.PHSCIENCE_3_9_9)
            graph.bind("phIoT", tc.PHIOT_3_9_9)


def bind_prefixes(graph: Graph) -> None:
    """
    Associate common prefixes with the graph
    """
    graph.bind("rdf", tc.RDF)
    graph.bind("owl", tc.OWL)
    graph.bind("rdfs", tc.RDFS)
    graph.bind("skos", tc.SKOS)
    graph.bind("sh", tc.SH)


def is_valid_schema_and_version(schema: str, version: str) -> bool:
    """
    Check that schema and version are supported.  Raise exceptions if not.
    :param schema: [str] A valid key from SUPPORTED_SCHEMAS
    :param version: [str] A valid version from SUPPORTED_SCHEMAS
    :return: [bool]
    """
    if schema in tc.SUPPORTED_SCHEMAS.keys():
        if version in tc.SUPPORTED_SCHEMAS[schema]:
            return True
        else:
            raise Exception(
                f"Schema: {schema} with version: {version} not supported.  Supported versions include: {list(tc.SUPPORTED_SCHEMAS[schema])}")
    else:
        raise Exception(
            f"Schema: {schema} not supported.  Supported schemas include: {list(tc.SUPPORTED_SCHEMAS.keys())}")

    return False


def get_namespaces_given_term(ontology: Graph, term: str) -> List[Namespace]:
    """
    Return a list of Namespaces where this term exists in the provided Graph.
    The hope is for the len to be 1, i.e. there is just one Namespace where this
    term exists
    :param ontology: [Graph] an ontology (Brick or Haystack) pre
    :param term: [str] a term to search for in the Namespace
    :return: [list[Namespace]]
    """
    graph_namespaces = list(ontology.namespaces())
    ns_objects = [Namespace(x[1]) for x in graph_namespaces]
    subjects = set(ontology.subjects())
    matched_namespaces = []
    for gn in ns_objects:
        if gn[term] in subjects:
            matched_namespaces.append(gn)
    return matched_namespaces
