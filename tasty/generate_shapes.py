import os
import json
from typing import List, Dict, Tuple

from rdflib import BNode, Namespace, Literal, Graph, URIRef, SH, RDF

import tasty.graphs as tg
import tasty.constants as tc


# TODO:
# we should probably refactor this as a class since we are just passing
# data around between functions

# Functions
def load_sources(schema: str) -> Dict:
    """
    Load all JSON source shapes for a given schema. Return a dictionary that looks like:
    {
        'path-to-file': { data-loaded-from-file }
    }
    :param schema:
    :return:
    """
    root = os.path.join(os.path.dirname(__file__), 'source_shapes', schema)
    files = [os.path.join(root, f) for f in
             os.listdir(root) if f.endswith('.json')]

    # read json files in
    data = {}
    for file in files:
        with open(file, 'r') as f:
            data[os.path.basename(file)] = json.loads(f.read())

    return data


def write_shapes_graph_to_generated_shapes_dir(g: Graph, file_name: str):
    """
    Serialize the provided shapes graph to the tasty/generated_shapes/ directory.
    :param g: shapes graph to write
    :param file_name: name of the output file to write
    :return:
    """
    output = os.path.join(os.path.dirname(__file__), 'generated_shapes')
    if not os.path.isdir(output):
        os.mkdir(output)
    g.serialize(destination=os.path.join(output, file_name), format='turtle')
    return True


def add_all_tags(g: Graph, ontology: Graph, shape_map: List, namespaced_shape: URIRef) -> int:
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

    return count_tags


def add_all_types(g: Graph, ontology: Graph, shape_map: Dict, namespaced_shape: URIRef) -> int:
    """
    Loop through the 'types' in the shape_map and add a sh:class constraint for each.
    The types are not expected to be namespaced, but should exist in the ontology.
    :param g:
    :param ontology:
    :param shape_map:
    :param namespaced_shape:
    :return:
    """
    assert shape_map.get("types") is not None, f"There must be a 'type' key in {shape_map}"

    count_types = 0
    for each_type in shape_map["types"]:
        type_ns = tg.get_namespaced_term(ontology, each_type)
        if type_ns:
            g.add((namespaced_shape, SH['class'], type_ns))
            count_types += 1

    return count_types


def add_predicates(g: Graph, ontology: Graph, namespaced_shape: URIRef, predicates: dict, importance: str):
    """
    Loop through required and optional predicates key from the source shape and transform to SHACL.
    for each path, add in the required shapes and types.
    :param g:
    :param ontology:
    :param namespaced_shape:
    :param predicates:
    :param importance:
    :return:
    """
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


def add_shapes_and_types(g: Graph, ontology: Graph, namespaced_shape: URIRef, namespaced_path: URIRef, each_path: dict,
                         optional=False):
    """
    For a given path provided, transform all of the 'shapes' and 'types' from the source shape definition into SHACL.
    Handles optional by setting the sh:severity to sh:Warning
    :param g:
    :param ontology:
    :param namespaced_shape:
    :param namespaced_path:
    :param each_path:
    :param optional:
    :return:
    """
    if each_path.get('shapes') is not None:
        for each_shape in each_path['shapes']:
            prop_bn = stub_new_qualified_value_property(g, each_path, namespaced_shape, namespaced_path)
            g.add((prop_bn, SH.qualifiedValueShape, tc.PH_SHAPES_CORE[each_shape]))
            if optional:
                # For optionals, we set the severity to warning
                g.add((prop_bn, SH.severity, SH.Warning))

    if each_path.get("types") is not None:
        for each_type in each_path["types"]:
            prop_bn = stub_new_qualified_value_property(g, each_path, namespaced_shape, namespaced_path)
            namespaced_type = tg.get_namespaced_term(ontology, each_type)
            nodeshape_bn = BNode()
            g.add((prop_bn, SH.qualifiedValueShape, nodeshape_bn))
            g.add((nodeshape_bn, RDF.type, SH.NodeShape))
            g.add((nodeshape_bn, SH['class'], namespaced_type))
            if optional:
                # For optionals, we set the severity to warning
                g.add((prop_bn, SH.severity, SH.Warning))


def add_all_mixins(g: Graph, namespaced_shape: URIRef, shape: dict, ns: Namespace):
    """
    Add all mixins to the provided namespaced_shape.
    :param g:
    :param namespaced_shape:
    :param shape:
    :param ns: namespace to use for the mixin
    :return:
    """
    if shape.get('shape-mixins') is not None:
        for each_mixin in shape['shape-mixins']:
            ns_mixin = ns[each_mixin]
            if ns_mixin not in g.subjects():
                print(f"Mixin {ns_mixin} not in graph")
            else:
                g.add((namespaced_shape, SH.node, ns_mixin))


def stub_new_qualified_value_property(g: Graph, each_path: dict, parent_namespaced_shape: URIRef,
                                      namespaced_path: URIRef) -> BNode:
    """
    Create a new property as a BNode, where the property specifies qualified constraints.

    Output looks like:
        [ sh:path [ sh:inversePath phIoT:equipRef ] ;
            sh:qualifiedMaxCount 1 ;
            sh:qualifiedMinCount 1 ;
            sh:qualifiedValueShapesDisjoint true ] ;

    The sh:qualifiedValueShape added elsewhere.
    Assumes we want:
        - exactly 1 of the shapes
        - distinctness (i.e. disjoint)
    :param g:
    :param each_path:
    :param parent_namespaced_shape:
    :param namespaced_path:
    :return:
    """
    property_bn = BNode()
    g.add((parent_namespaced_shape, SH.property, property_bn))
    add_sh_path(g, property_bn, each_path, namespaced_path)
    g.add((property_bn, SH.qualifiedMinCount, Literal(1)))
    g.add((property_bn, SH.qualifiedMaxCount, Literal(1)))
    g.add((property_bn, SH.qualifiedValueShapesDisjoint, Literal(True)))
    return property_bn


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
    required_nodes = len(each_path.get("types", [])) + len(each_path.get('shapes', []))
    if required_nodes > 0:
        # we define a minCount for each given relationship type
        min_count_bn = BNode()
        g.add((namespaced_shape, SH.property, min_count_bn))
        g.add((min_count_bn, SH.minCount, Literal(required_nodes)))
        add_sh_path(g, min_count_bn, each_path, namespaced_path)


def add_sh_path(g: Graph, property_bn: BNode, each_path: dict, namespaced_path):
    """
    Add a path constraint, either inverse or direct. Looks like:
        [ sh:path [ sh:inversePath phIoT:equipRef ] ] (inverse)
        [ sh:path phIoT:equipRef ] (direct)
        where the outer is the property_bn
    :param g:
    :param property_bn: blank node of the current property
    :param each_path:
    :param namespaced_path: the predicate to be traversed, i.e. ph:hasTag, phIoT:equipRef
    :return:
    """
    # Here we translate the path into a BNode if necessary (i.e. for inverse pathing)
    if each_path.get('path-type') is not None and each_path['path-type'] == 'inverse':
        path_bn = BNode()
        g.add((property_bn, SH.path, path_bn))
        g.add((path_bn, SH.inversePath, namespaced_path))
    elif each_path.get('path-type') is not None and each_path['path-type'] == 'direct':
        g.add((property_bn, SH.path, namespaced_path))


def add_tags_types_and_predicates(g: Graph, ns_shape: URIRef, shape: dict, ontology: Graph):
    """
    Take the provided source shape dict object and transform to a SHACL shape:
    - tag requirements will be added as property shape requirements to the shape itself with a ph:hasTag traversal
    - type requirements will be added as sh:class constrants to the shape itself
    - predicates will be added as property shape requirements to the shape itself with a traversal defined by
        the 'path' and 'path-type' keys.
    :param g:
    :param ns_shape:
    :param shape:
    :param ontology:
    :return:
    """
    # add tag requirements to shacl shape
    if shape.get('tags') is not None:
        add_all_tags(g, ontology, shape, ns_shape)

    # add typing requirements to shacl shape
    if shape.get("types") is not None:
        add_all_types(g, ontology, shape, ns_shape)

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
        add_predicates(g, ontology, ns_shape, shape['predicates'], 'requires')
    if optional:
        add_predicates(g, ontology, ns_shape, shape['predicates'], 'optional')


def set_version_and_load(file_path) -> Tuple[Graph, Graph]:
    """
    Given a file path to a source_shape JSON file, set defaults for the namespaces.
    Return a graph with default namespaces loaded in and graph with the correct versioned
    ontology loaded.
    see tc.set_default_versions()
    :param file_path:
    :return:
    """
    bn = os.path.basename(file_path)
    no_ext = os.path.splitext(bn)[0]
    if 'brick' in file_path:
        g = tg.get_versioned_graph(tc.BRICK, tc.V1_1)
        ontology = tg.load_ontology(tc.HAYSTACK, tc.V1_1)
    else:
        if no_ext.endswith('v1'):
            version = tc.V3_9_9
        else:
            version = tc.V3_9_10
        tc.set_default_versions(haystack_version=version)
        g = tg.get_versioned_graph(tc.HAYSTACK, version)
        ontology = tg.load_ontology(tc.HAYSTACK, version)
    return g, ontology


def generate_shapes_given_source_template(source_shape_full: dict, g: Graph, ontology: Graph):
    """
    Given a full source shape as a dict, generate SHACL shapes for all items under 'shapes' list.
    :param source_shape_full:
    :param g:
    :param ontology:
    :return:
    """
    ns = Namespace(source_shape_full['namespace'])
    g.bind(source_shape_full['prefix'], ns)

    # we separate out mixins to process later
    have_mixins = []

    # now iterate through and build shapes
    for shape in source_shape_full['shapes']:
        ns_shape = ns[shape['name']]
        if shape.get("shape-mixins"):
            have_mixins.append(shape)
            continue
        nodeshape_triple = (ns_shape, RDF.type, SH.NodeShape)
        g.add(nodeshape_triple)
        add_tags_types_and_predicates(g, ns_shape, shape, ontology)
        print(f"Processed shape: {ns_shape}")

    # now we process things with mixins.
    # we assume mixins might contain other mixins,
    # which is why we have the double loops
    while len(have_mixins) > 0:

        # loop in reverse so that when we pop it dont blow up
        for i in range(len(have_mixins) - 1, -1, -1):
            shape = have_mixins[i]
            ns_shape = ns[shape['name']]
            print(f"Processing mixin: {ns_shape}")
            mixins = shape.get("shape-mixins")
            skip = False
            for mixin in mixins:
                ns_mixin = ns[mixin]
                if ns_mixin not in g.subjects():
                    print(f"{ns_mixin} required for {ns_shape}, but not yet in graph.")
                    skip = True
                    continue
            if not skip:
                nodeshape_triple = (ns_shape, RDF.type, SH.NodeShape)
                g.add(nodeshape_triple)
                # if we get to this point, all mixins required for this
                # particular shape are already in the graph and we can begin
                # processing this shape
                add_tags_types_and_predicates(g, ns_shape, shape, ontology)
                add_all_mixins(g, ns_shape, shape, ns)
                have_mixins.pop(i)
    return g
