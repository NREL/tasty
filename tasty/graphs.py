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


def graph_to_hayson_string(graph: Graph) -> str:
    """
    Return the Haystack JSON (Hayson) encoding of an RDF graph.
    :param graph: [rdflib.Graph]
    :return: [str]
    """
    hayson_dict = {
        "meta": {"ver": "3.0"},
        "cols": [],
        "rows": []
    }
    json_ld_str = json.loads(graph.serialize(format='json-ld').decode('utf-8'))
    for row in json_ld_str:
        json_ld_dict = {"id": str(uuid.uuid4())}
        for key, val in row.items():
            uri_fragment_list = key.split("#")
            if key == "@id":
                dis = val
                json_ld_dict .update({"dis": dis})
            elif key == "@type":
                tags = val[0].split('#')[1]
                multitag = tags.split("-")
                [json_ld_dict .update({tag: "m"}) for tag in multitag]
            elif uri_fragment_list[1] == "hasTag":
                for tag1 in val:
                    for k, v in tag1.items():
                        if k == "@id":
                            t = v.split("#")[1]
                            json_ld_dict .update({t: ":m"})
            elif uri_fragment_list[1] == "equipRef":
                for ref in val:
                    for k, v in ref.items():
                        if k == "@id":
                            t = v.split("/")[1]
                            json_ld_dict .update({"equipRef": v})
            elif uri_fragment_list[1] == "condenserWaterRef":
                for ref in val:
                    for k, v in ref.items():
                        if k == "@id":
                            t = v.split("/")[1]
                            json_ld_dict .update({"condenserWaterRef": v})
            elif uri_fragment_list[1] == "hotWaterRef":
                for ref in val:
                    for k, v in ref.items():
                        if k == "@id":
                            t = v.split("/")[1]
                            json_ld_dict .update({"hotWaterRef": v})
            elif uri_fragment_list[1] == "airRef":
                for ref in val:
                    for k, v in ref.items():
                        if k == "@id":
                            t = v.split("/")[1]
                            json_ld_dict .update({"airRef": v})

            hayson_dict["rows"].append(json_ld_dict)

    seen = set()
    hayson_rows_list = []
    cols = set()
    hayson_cols_list = []
    for d in hayson_dict["rows"]:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            hayson_rows_list.append(d)
            for tag in t:
                cols.add(tag[0])

    [hayson_cols_list.append({"name": tag}) for tag in cols]

    hayson_dict["cols"] = hayson_cols_list
    hayson_dict["rows"] = hayson_rows_list
    return json.dumps(hayson_dict)
