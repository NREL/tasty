import os
import json
from typing import List

from rdflib import BNode, Namespace, Literal, Graph, URIRef, SH, RDF

import tasty.graphs as tg
import tasty.constants as tc


# Functions
def load_sources():
    root = os.path.join(os.path.dirname(__file__), 'source_shapes')
    files = [os.path.join(root, f) for f in
             os.listdir(root) if f.endswith('.json')]

    # read json files in
    data = {}
    for file in files:
        with open(file, 'r') as f:
            data[os.path.basename(file)] = json.loads(f.read())

    return data


def write_to_output(g, name):
    output = os.path.join(os.path.dirname(__file__), 'generated')
    if not os.path.isdir(output):
        os.mkdir(output)
    g.serialize(destination=os.path.join(output, name), format='turtle')
    return True


def add_all_tags(g: Graph, ontology: Graph, shape_map: List, namespaced_shape: URIRef):
    """
    Consider both 'tags' and 'tags-custom' keys.
    :param g:
    :param ontology:
    :param shape_map:
    :param namespaced_shape:
    :return:
    """
    assert shape_map.get('tags') is not None, f"There must be a 'tags' key in {shape_map}"
    count_tags = 0

    def add_tag_as_bnode(namespaced_tag):
        prop_bn = BNode()
        qvs_bn = BNode()
        g.add((namespaced_shape, SH.property, prop_bn))
        g.add((prop_bn, SH.path, tc.PH_DEFAULT.hasTag))
        g.add((prop_bn, SH.qualifiedValueShape, qvs_bn))
        g.add((prop_bn, SH.qualifiedMinCount, Literal(1)))
        g.add((qvs_bn, SH.hasValue, namespaced_tag))

    for tag in shape_map['tags']:
        tag_ns = tg.get_namespaced_term(ontology, tag)
        if tag_ns:
            count_tags += 1
            add_tag_as_bnode(tag_ns)

    if shape_map.get('tags-custom') is not None:
        g.bind('phCustom', tc.PH_CUSTOM)
        for tag in shape_map['tags-custom']:
            tag_ns = tc.PH_CUSTOM[tag]
            count_tags += 1
            add_tag_as_bnode(tag_ns)

    # Here we just add a minCount equal to the total number of tags
    # as a secondary step. Helpful for debugging
    bn = BNode()
    g.add((namespaced_shape, SH.property, bn))
    g.add((bn, SH.path, tc.PH_DEFAULT.hasTag))
    g.add((bn, SH.minCount, Literal(count_tags)))


def add_type(g: Graph, ontology: Graph, shape_map: List, namespaced_shape: URIRef):
    assert shape_map.get('type') is not None, f"There must be a 'type' key in {shape_map}"
    for each_type in shape_map['type']:
        type_ns = tg.get_namespaced_term(ontology, each_type)
        if type_ns:
            g.add((namespaced_shape, SH['class'], type_ns))


def add_predicates(g: Graph, ontology: Graph, namespaced_shape: URIRef, predicates: dict, importance: str):
    if importance == 'requires' and predicates.get('requires') is not None:
        for each_path in predicates['requires']:
            path = each_path.get('path')
            namespaced_path = tg.get_namespaced_term(ontology, path)
            add_min_count_for_required_nodes(g, each_path, namespaced_shape, namespaced_path)
            add_shapes_and_types(g, ontology, namespaced_shape, namespaced_path, each_path)

    elif importance == 'optional' and predicates.get('optional') is not None:
        for each_path in predicates['optional']:
            path = each_path.get('path')
            namespaced_path = tg.get_namespaced_term(ontology, path)
            # specify these as optional in the function argument
            add_shapes_and_types(g, ontology, namespaced_shape, namespaced_path, each_path, True)


def add_shapes_and_types(g: Graph, ontology: Graph, namespaced_shape: URIRef, namespaced_path, each_path,
                         optional=False):
    if each_path.get('shapes') is not None:
        for each_shape in each_path['shapes']:
            prop_bn = add_qvs_property(g, each_path, namespaced_shape, namespaced_path)
            g.add((prop_bn, SH.qualifiedValueShape, tc.PH_SHAPES[each_shape]))
            if optional:
                # For optionals, we set the severity to warning
                g.add((prop_bn, SH.severity, SH.Warning))

    if each_path.get('type') is not None:
        for each_type in each_path['type']:
            prop_bn = add_qvs_property(g, each_path, namespaced_shape, namespaced_path)
            namespaced_type = tg.get_namespaced_term(ontology, each_type)
            nodeshape_bn = BNode()
            g.add((prop_bn, SH.qualifiedValueShape, nodeshape_bn))
            g.add((nodeshape_bn, RDF.type, SH.NodeShape))
            g.add((nodeshape_bn, SH['class'], namespaced_type))
            if optional:
                # For optionals, we set the severity to warning
                g.add((prop_bn, SH.severity, SH.Warning))


def add_qvs_property(g: Graph, each_path: dict, parent_namespaced_shape: URIRef, namespaced_path: URIRef) -> BNode:
    property_bn = BNode()
    g.add((parent_namespaced_shape, SH.property, property_bn))
    add_sh_path(g, property_bn, each_path, namespaced_path)
    g.add((property_bn, SH.qualifiedMinCount, Literal(1)))
    g.add((property_bn, SH.qualifiedMaxCount, Literal(1)))
    g.add((property_bn, SH.qualifiedValueShapesDisjoint, Literal(True)))
    return property_bn


# def add_optional_qvs_property(g: Graph, each_path: dict, namespaced_shape: URIRef, namespaced_path: URIRef):
#     property_bn = BNode()
#     g.add((namespaced_shape, SH.property, property_bn))
#     add_sh_path(g, property_bn, each_path, namespaced_path)


def add_min_count_for_required_nodes(g: Graph, each_path: dict, namespaced_shape: URIRef, namespaced_path: URIRef):
    """
    Count the required number of 'types' and 'shapes' and add a minCount property constraint. Considers
     inverse paths as well. Something like:
            sh:property [
            sh:path [ sh:inversePath phIoT:equipRef ] ;
            sh:minCount 3 ;
        ] ;
    :param g:
    :param each_path:
    :param namespaced_shape:
    :param namespaced_path:
    :return:
    """
    required_nodes = len(each_path.get('type', [])) + len(each_path.get('shapes', []))
    if required_nodes > 0:
        # we define a minCount for each given relationship type
        min_count_bn = BNode()
        g.add((namespaced_shape, SH.property, min_count_bn))
        g.add((min_count_bn, SH.minCount, Literal(required_nodes)))
        add_sh_path(g, min_count_bn, each_path, namespaced_path)


def add_sh_path(g: Graph, property_bn: BNode, each_path: dict, namespaced_path):
    """
    Add a path constraint, either inverse or direct
    :param g:
    :param property_bn:
    :param each_path:
    :param namespaced_path:
    :return:
    """
    # Here we translate the path into a BNode if necessary (i.e. for inverse pathing)
    if each_path.get('path-type') is not None and each_path['path-type'] == 'inverse':
        path_bn = BNode()
        g.add((property_bn, SH.path, path_bn))
        g.add((path_bn, SH.inversePath, namespaced_path))
    elif each_path.get('path-type') is not None and each_path['path-type'] == 'direct':
        g.add((property_bn, SH.path, namespaced_path))


def safe_add(g: Graph, nodeshape_triple: tuple):
    if nodeshape_triple not in g:
        g.add(nodeshape_triple)


# Load in the template files
data = load_sources()

# get a blank versioned graph
g = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_10)

# load in the ontology
ontology = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)

# Pull out the v2 info
v2 = data['core_v2.json']
ns = Namespace(v2['namespace'])
g.bind(v2['prefix'], ns)

# now iterate through and build shapes
for shape in v2['shapes']:
    ns_shape = ns[shape['name']]
    nodeshape_triple = (ns_shape, RDF.type, SH.NodeShape)

    # add tag requirements to shacl shape
    if shape.get('tags') is not None:
        safe_add(g, nodeshape_triple)
        add_all_tags(g, ontology, shape, ns_shape)

    # add typing requirements to shacl shape
    if shape.get("type") is not None:
        safe_add(g, nodeshape_triple)
        add_type(g, ontology, shape, ns_shape)

    # add other relationship requirements
    required = optional = False
    try:
        required = shape.get('predicates').get('requires')
    except (KeyError, AttributeError):
        pass
    try:
        optional = shape.get('predicates').get('optional')
    except (KeyError, AttributeError):
        pass
    if required:
        safe_add(g, nodeshape_triple)
        add_predicates(g, ontology, ns_shape, shape['predicates'], 'requires')
    if optional:
        safe_add(g, nodeshape_triple)
        add_predicates(g, ontology, ns_shape, shape['predicates'], 'optional')

write_to_output(g, 'core_v2.ttl')
