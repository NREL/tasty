from dataclasses import dataclass
from difflib import SequenceMatcher
from colorama import init as colorama_init
from colorama import Fore, Style
import brickschema
from brickschema.namespaces import BRICK, RDF, RDFS
from collections import defaultdict
from rdflib import Namespace, URIRef
import itertools
import sys

from typing import List, Tuple, Optional


colorama_init()
DEBUG = False
BLDG = Namespace("http://example.org/building/")


@dataclass
class EntityFeature:
    uri: URIRef
    typ: URIRef
    label: str
    namespace: URIRef

    def similarity(self, other: "EntityFeature"):
        assert other.namespace == self.namespace
        len_ns = len(self.namespace)
        score = 0
        score += SequenceMatcher(None, self.uri[len_ns:], other.uri[len_ns:]).ratio()
        # score += SequenceMatcher(None, self.typ, other.typ).ratio()
        score += SequenceMatcher(None, self.label, other.label).ratio()
        return score


def validate(g):
    valid, _, report = g.validate()
    if not valid:
        raise Exception(report)


def unify_entities(G, e1, e2):
    """
    Replaces all instances of e2 with e1 in graph G
    """
    print(Style.BRIGHT + Fore.CYAN + f"Unifying {e1} and {e2}" + Style.RESET_ALL)
    e1 = URIRef(e1)
    e2 = URIRef(e2)
    pos = G.predicate_objects(subject=e2)
    for (p, o) in pos:
        G.remove((e2, p, o))
        G.add((e1, p, o))

    sps = G.subject_predicates(object=e2)
    for (s, p) in sps:
        G.remove((s, p, e2))
        G.add((s, p, e1))


def all_pairs_of_entities(g1ents, g2ents):
    """
    Generate all possible 'matchings'. A matching is
    a pairing of all ents in g1 to a unique eng in g2
    """
    for g1perm in itertools.permutations(g1ents, len(g1ents)):
        yield list(zip(g1perm, g2ents))


def score_matching(matching: List[Tuple[EntityFeature, EntityFeature]]):
    """
    Returns a similarity score over all of the pairs
    """
    total_sim = 0
    for ent1, ent2 in matching:
        total_sim += ent1.similarity(ent2)
    return total_sim


def get_entity_feature_vector(e, g, namespace) -> EntityFeature:
    return EntityFeature(e,
            g.value(e, RDF.type),
            g.value(e, RDFS.label),
            namespace)
    # res = g.query(
    #     f"""SELECT ?type ?label WHERE {{
    #     {e.to_n3()} rdf:type ?type .
    #     OPTIONAL {{ ?ent rdfs:label ?label }} .
    # }}"""
    # )
    # features = {}
    # for row in res:
    #     etype, label = row
    #     features["type"] = str(etype)
    #     features["label"] = str(label)
    #     features["uri"] = str(e)

    # return features


def get_common_types(g1, g2, namespace):
    """
    Returns the list of types that are common to both graphs. A type is included
    if both graphs have instances of that type
    """
    g1ents = g1.query(
        f"""SELECT DISTINCT ?type WHERE {{
        ?ent rdf:type ?type .
        FILTER(STRSTARTS(STR(?ent), STR(<{namespace}>)))
    }}"""
    )

    g2ents = g2.query(
        f"""SELECT DISTINCT ?type WHERE {{
        ?ent rdf:type ?type .
        FILTER(STRSTARTS(STR(?ent), STR(<{namespace}>)))
    }}"""
    )

    g1types = set([x[0] for x in g1ents])
    g2types = set([x[0] for x in g2ents])
    return list(g1types.intersection(g2types))


def get_pairs_by_type(g1, g2, ns) -> List[Tuple[URIRef, URIRef]]:
    types = get_common_types(g1, g2, ns)

    # assume no covariancy (yet)
    for typ in types:
        g1ents = list(g1.subjects(RDF.type, typ))
        g2ents = list(g2.subjects(RDF.type, typ))
        if len(g1ents) != len(g2ents):
            print(
                Fore.YELLOW + f"Not same # of instances for type {typ} ({len(g1ents)} != {len(g2ents)})" + Style.RESET_ALL,
                file=sys.stderr,
            )
            continue

        g1ents = [get_entity_feature_vector(e1, g1, BLDG) for e1 in g1ents]
        g2ents = [get_entity_feature_vector(e2, g2, BLDG) for e2 in g2ents]

        # same # of entities of type 'typ' in g1 and g2.
        # Find the most likely bipartite matching
        max_score = float('-inf')
        max_matching = None
        for matching in all_pairs_of_entities(g1ents, g2ents):
            score = score_matching(list(matching))
            if score > max_score:
                print(matching)
                print(score)
                print('-'*30)
                max_score = score
                max_matching = matching[:]
        print(max_matching)
        print(max_score)

    return []


g1 = brickschema.Graph().load_file("../nrel/mediumOffice_brick.ttl")
g2 = brickschema.Graph().load_file("../pnnl/mediumOffice_brick.ttl")

# TODO: incorporate this. Throw out any permutation that violates the initial mapping
initial_mapping = {}

def merge(g1, g2, ns):
    get_pairs_by_type(g1, g2, ns)

merge(g1, g2, BLDG)

# G = merge_type_cluster(g1, g2, BLDG, similarity_threshold=0.1)
# validate(G)
# G.serialize("merged.ttl", format="ttl")
