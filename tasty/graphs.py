import json
import os
from typing import List, Union
import uuid

from rdflib import Graph, Namespace, OWL, RDF, RDFS, SKOS, SH, URIRef

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
    if schema == tc.HAYSTACK:
        schema_path = os.path.join(schema_path, f"defs_{version.replace('.', '_')}.ttl")
    elif schema == tc.BRICK:
        schema_path = os.path.join(schema_path, f"Brick_{version.replace('.', '_')}.ttl")
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
    if schema == tc.BRICK:
        if version == tc.V1_1:
            graph.bind("brick", tc.BRICK_1_1)
            graph.bind("tag", tc.TAG_1_1)
            graph.bind("bsh", tc.BSH_1_1)
    elif schema == tc.HAYSTACK:
        if version == tc.V3_9_9:
            graph.bind("ph", tc.PH_3_9_9)
            graph.bind("phIct", tc.PHICT_3_9_9)
            graph.bind("phScience", tc.PHSCIENCE_3_9_9)
            graph.bind("phIoT", tc.PHIOT_3_9_9)
        elif version == tc.V3_9_10:
            graph.bind("ph", tc.PH_3_9_10)
            graph.bind("phIct", tc.PHICT_3_9_10)
            graph.bind("phScience", tc.PHSCIENCE_3_9_10)
            graph.bind("phIoT", tc.PHIOT_3_9_10)


def bind_prefixes(graph: Graph) -> None:
    """
    Associate common prefixes with the graph
    """
    graph.bind("rdf", RDF)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("skos", SKOS)
    graph.bind("sh", SH)


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


def has_one_namespace(ns):
    """
    Run after tg.get_namespaces_given_term to validate only a single ns was found
    :param ns: [List[Namespace]]
    :param candidate: [str]
    :return:
    """
    if len(ns) == 1:
        return True
    elif len(ns) == 0:
        return False
    else:
        return False


def get_namespaced_term(ontology: Graph, term: str) -> Union[URIRef, bool]:
    """
    Return a fully namespaced term if it exists exclusively in the ontology, else return False
    :param ontology:
    :param term:
    :return:
    """
    potential_namespaces = get_namespaces_given_term(ontology, term)
    if has_one_namespace(potential_namespaces):
        ns = potential_namespaces[0]
        return ns[term]
    return False


def print_as_hayson(graph: Graph):
    """
    Return the Hayson encoding of an rdf graph
    :param graph: [rdflib.Graph]
    :return:
    """
    hayson = {

        "meta": {"ver": "3.0"},
        "cols": [],
        "rows": []
    }
    json_ld = graph.serialize(format='json-ld').decode('utf-8')
    data = json.loads(json_ld)
    for row in data:
        hayThing = {"id": str(uuid.uuid4())}
        for key, value in row.items():
            if key == "@id":
                dis = value
                hayThing.update({"dis": dis})
            elif key == "@type":
                tags = value[0].split('#')[1]
                multitag = tags.split("-")
                for tag in multitag:
                    hayThing.update({tag: "m"})
            elif key.split("#")[1] == "hasTag":
                for tag1 in value:
                    for k, v in tag1.items():
                        if k == "@id":
                            t = v.split("#")[1]
                            hayThing.update({t: ":m"})
            elif key.split("#")[1] == "equipRef":
                for ref in value:
                    for k, v in ref.items():
                        if k == "@id":
                            t = v.split("/")[1]
                            hayThing.update({"equipRef": v})
            elif key.split("#")[1] == "condenserWaterRef":
                for ref in value:
                    for k, v in ref.items():
                        if k == "@id":
                            t = v.split("/")[1]
                            hayThing.update({"condenserWaterRef": v})
            elif key.split("#")[1] == "hotWaterRef":
                for ref in value:
                    for k, v in ref.items():
                        if k == "@id":
                            t = v.split("/")[1]
                            hayThing.update({"hotWaterRef": v})
            elif key.split("#")[1] == "airRef":
                for ref in value:
                    for k, v in ref.items():
                        if k == "@id":
                            t = v.split("/")[1]
                            hayThing.update({"airRef": v})

            hayson["rows"].append(hayThing)

    seen = set()
    new_l = []
    cols = set()
    hay_cols = []
    for d in hayson["rows"]:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_l.append(d)
            for tag in t:
                cols.add(tag[0])

    for tag in cols:
        hay_cols.append({"name": tag})

    hayson["cols"] = hay_cols
    hayson["rows"] = new_l
    return json.dumps(hayson)
