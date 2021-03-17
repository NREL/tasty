import os
import json
from typing import Dict

from rdflib import BNode, Namespace, Literal, Graph, URIRef, SH, RDF

import tasty.graphs as tg
import tasty.constants as tc
import tasty.exceptions as te


class ShapesGenerator:
    def __init__(self, schema, version):
        self.root_dir = os.path.dirname(__file__)
        self.source_shapes_dir = os.path.join(self.root_dir, 'source_shapes')
        self.generated_shapes_dir = os.path.join(self.root_dir, 'generated_shapes')
        self.schema_source_shapes_dir: str = None
        self.source_shapes_by_file: dict = {}
        self.shapes_lookup: dict = {}
        self.current_shape_ns: Namespace = None

        # create dirs if not exist
        if not os.path.isdir(self.generated_shapes_dir):
            os.mkdir(self.generated_shapes_dir)

        # initialize blank graph and ontology
        if schema == tc.HAYSTACK:
            tc.set_default_versions(haystack_version=version)
        elif schema == tc.BRICK:
            tc.set_default_versions(brick_version=version)
        else:
            raise te.TastyError(f"Schema must be one of: {tc.SUPPORTED_SCHEMAS.keys()}")

        # Set the schema and version
        self.schema = schema
        self.version = version

        # Load in the ontology and a blank shapes graph to use
        self.ontology: Graph = tg.load_ontology(self.schema, self.version)
        self.shapes_graph: Graph = tg.get_versioned_graph(self.schema, self.version)

        self.load_all_source_shapes_by_schema()

    def load_all_source_shapes_by_schema(self):
        source_shapes_schema_dir = os.path.join(self.source_shapes_dir, self.schema.lower())
        files = [os.path.join(source_shapes_schema_dir, f) for f in
                 os.listdir(source_shapes_schema_dir) if f.endswith('.json')]

        for file in files:
            with open(file, 'r') as f:
                self.source_shapes_by_file[os.path.basename(file)] = json.loads(f.read())

        for file, file_data in self.source_shapes_by_file.items():
            ns = file_data['namespace']
            prefix = file_data['prefix']
            for shape in file_data['shapes']:
                if shape['name'] not in self.shapes_lookup:
                    self.shapes_lookup[shape['name']] = {
                        'namespace': ns,
                        'prefix': prefix
                    }
                else:
                    print(f"WARNING: {shape['name']} exists in multiple namespaces")

    def reset_shapes_graph(self):
        self.shapes_graph: Graph = tg.get_versioned_graph(self.schema, self.version)

    def write_shapes_graph_to_generated_shapes_dir(self, file_name: str):
        """
        Serialize the provided shapes graph to the tasty/generated_shapes/ directory.
        :param file_name: name of the output file to write
        :return:
        """
        self.shapes_graph.serialize(destination=os.path.join(self.generated_shapes_dir, file_name), format='turtle')
        return True

    def add_all_tags(self, shape_map: Dict, namespaced_shape: URIRef) -> int:
        """
        Considers both 'tags' and 'tags-custom' keys.
        :param shape_map:
        :param namespaced_shape:
        :return:
        """
        assert shape_map.get('tags') is not None, f"There must be a 'tags' key in {shape_map}"
        count_tags = 0

        def add_tag_as_bnode(namespaced_tag):
            prop_bn = BNode()
            qvs_bn = BNode()
            self.shapes_graph.add((namespaced_shape, SH.property, prop_bn))
            self.shapes_graph.add((prop_bn, SH.path, tc.PH_DEFAULT.hasTag))
            self.shapes_graph.add((prop_bn, SH.qualifiedValueShape, qvs_bn))
            self.shapes_graph.add((prop_bn, SH.qualifiedMinCount, Literal(1)))
            self.shapes_graph.add((qvs_bn, SH.hasValue, namespaced_tag))

        for tag in shape_map['tags']:
            tag_ns = tg.get_namespaced_term(self.ontology, tag)
            if tag_ns:
                count_tags += 1
                add_tag_as_bnode(tag_ns)

        if shape_map.get('tags-custom') is not None:
            self.shapes_graph.bind('phCustom', tc.PH_CUSTOM)
            for tag in shape_map['tags-custom']:
                tag_ns = tc.PH_CUSTOM[tag]
                count_tags += 1
                add_tag_as_bnode(tag_ns)

        # Here we just add a minCount equal to the total number of tags
        # as a secondary step. Helpful for debugging
        bn = BNode()
        self.shapes_graph.add((namespaced_shape, SH.property, bn))
        self.shapes_graph.add((bn, SH.path, tc.PH_DEFAULT.hasTag))
        self.shapes_graph.add((bn, SH.minCount, Literal(count_tags)))

        return count_tags

    def add_all_types(self, shape_map: Dict, namespaced_shape: URIRef) -> int:
        """
        Loop through the 'types' in the shape_map and add a sh:class constraint for each.
        The types are not expected to be namespaced, but should exist in the ontology.
        :param shape_map:
        :param namespaced_shape:
        :return:
        """
        assert shape_map.get("types") is not None, f"There must be a 'type' key in {shape_map}"

        count_types = 0
        for each_type in shape_map["types"]:
            type_ns = tg.get_namespaced_term(self.ontology, each_type)
            if type_ns:
                self.shapes_graph.add((namespaced_shape, SH['class'], type_ns))
                count_types += 1

        return count_types

    def add_predicates(self, namespaced_shape, predicates: list, required=True):
        for each_path in predicates:
            path = each_path.get('path')
            namespaced_path = tg.get_namespaced_term(self.ontology, path)
            self.add_shapes_and_types(namespaced_shape, namespaced_path, each_path)
            if required:
                self.add_min_count_for_required_nodes(each_path, namespaced_shape, namespaced_path)

    def add_shapes_and_types(self, namespaced_shape: URIRef, namespaced_path: URIRef, each_path: dict, required=True):
        """
        For a given path provided, transform all of the 'shapes' and 'types' from the source shape definition into SHACL.
        Handles optional by setting the sh:severity to sh:Warning
        :param namespaced_shape:
        :param namespaced_path: example: URIRef('https://project-haystack.org/def/phIoT/3.9.10#equipRef')
        :param each_path:
        :param required:
        :return:
        """
        if each_path.get('shapes') is not None:
            for each_shape in each_path['shapes']:
                prop_bn = self.stub_new_qualified_value_property(each_path, namespaced_shape, namespaced_path)
                shape_info = self.shapes_lookup.get(each_shape)
                if shape_info:
                    ns = Namespace(shape_info['namespace'])
                    self.shapes_graph.add((prop_bn, SH.qualifiedValueShape, ns[each_shape]))
                    if not required:
                        # For optionals, we set the severity to warning
                        self.shapes_graph.add((prop_bn, SH.severity, SH.Warning))

        if each_path.get("types") is not None:
            for each_type in each_path["types"]:
                prop_bn = self.stub_new_qualified_value_property(each_path, namespaced_shape, namespaced_path)
                namespaced_type = tg.get_namespaced_term(self.ontology, each_type)
                nodeshape_bn = BNode()
                self.shapes_graph.add((prop_bn, SH.qualifiedValueShape, nodeshape_bn))
                self.shapes_graph.add((nodeshape_bn, RDF.type, SH.NodeShape))
                self.shapes_graph.add((nodeshape_bn, SH['class'], namespaced_type))
                if not required:
                    # For optionals, we set the severity to warning
                    self.shapes_graph.add((prop_bn, SH.severity, SH.Warning))

    def add_all_mixins(self, namespaced_shape: URIRef, shape: dict):
        """
        Add all mixins to the provided namespaced_shape.
        :param namespaced_shape:
        :param shape:
        :param ns: namespace to use for the mixin
        :return:
        """
        if shape.get('shape-mixins') is not None:
            for each_mixin in shape['shape-mixins']:
                ns_mixin = self.current_shape_ns[each_mixin]
                if ns_mixin not in self.shapes_graph.subjects():
                    print(f"Mixin {ns_mixin} not in graph")
                else:
                    self.shapes_graph.add((namespaced_shape, SH.node, ns_mixin))

    def stub_new_qualified_value_property(self, each_path: dict, parent_namespaced_shape: URIRef,
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
        :param each_path:
        :param parent_namespaced_shape:
        :param namespaced_path:
        :return:
        """
        property_bn = BNode()
        self.shapes_graph.add((parent_namespaced_shape, SH.property, property_bn))
        self.add_sh_path(property_bn, each_path, namespaced_path)
        self.shapes_graph.add((property_bn, SH.qualifiedMinCount, Literal(1)))
        self.shapes_graph.add((property_bn, SH.qualifiedMaxCount, Literal(1)))
        self.shapes_graph.add((property_bn, SH.qualifiedValueShapesDisjoint, Literal(True)))
        return property_bn

    def add_min_count_for_required_nodes(self, each_path: dict, namespaced_shape: URIRef, namespaced_path: URIRef):
        """
        Count the required number of 'types' and 'shapes' and add a minCount property constraint. Considers
         inverse paths as well. Something like:
                sh:property [
                sh:path [ sh:inversePath phIoT:equipRef ] ;
                sh:minCount 3 ;
            ] ;
        :param each_path:
        :param namespaced_shape:
        :param namespaced_path:
        :return:
        """
        required_nodes = len(each_path.get("types", [])) + len(each_path.get('shapes', []))
        if required_nodes > 0:
            # we define a minCount for each given relationship type
            min_count_bn = BNode()
            self.shapes_graph.add((namespaced_shape, SH.property, min_count_bn))
            self.shapes_graph.add((min_count_bn, SH.minCount, Literal(required_nodes)))
            self.add_sh_path(min_count_bn, each_path, namespaced_path)

    def add_sh_path(self, property_bn: BNode, each_path: dict, namespaced_path):
        """
        Add a path constraint, either inverse or direct. Looks like:
            [ sh:path [ sh:inversePath phIoT:equipRef ] ] (inverse)
            [ sh:path phIoT:equipRef ] (direct)
            where the outer is the property_bn
        :param property_bn: blank node of the current property
        :param each_path:
        :param namespaced_path: the predicate to be traversed, i.e. ph:hasTag, phIoT:equipRef
        :return:
        """
        # Here we translate the path into a BNode if necessary (i.e. for inverse pathing)
        if each_path.get('path-type') is not None and each_path['path-type'] == 'inverse':
            path_bn = BNode()
            self.shapes_graph.add((property_bn, SH.path, path_bn))
            self.shapes_graph.add((path_bn, SH.inversePath, namespaced_path))
        elif each_path.get('path-type') is not None and each_path['path-type'] == 'direct':
            self.shapes_graph.add((property_bn, SH.path, namespaced_path))

    def add_tags_types_and_predicates(self, ns_shape: URIRef, shape: dict):
        """
        Take the provided source shape dict object and transform to a SHACL shape:
        - tag requirements will be added as property shape requirements to the shape itself with a ph:hasTag traversal
        - type requirements will be added as sh:class constrants to the shape itself
        - predicates will be added as property shape requirements to the shape itself with a traversal defined by
            the 'path' and 'path-type' keys.
        :param ns_shape:
        :param shape:
        :return:
        """
        # add tag requirements to shacl shape
        if shape.get('tags') is not None:
            self.add_all_tags(shape, ns_shape)

        # add typing requirements to shacl shape
        if shape.get("types") is not None:
            self.add_all_types(shape, ns_shape)

        # add other relationship requirements
        required = shape.get('predicates', {}).get('requires', {})
        optional = shape.get('predicates', {}).get('optional', {})
        if required:
            self.add_predicates(ns_shape, shape['predicates']['requires'], required=True)
        if optional:
            self.add_predicates(ns_shape, shape['predicates']['optional'], required=False)

    def main(self, source_shape_full: dict):
        """
        Given a full source shape as a dict, generate SHACL shapes for all items under 'shapes' list.
        :param source_shape_full:
        :param g:
        :param ontology:
        :return:
        """
        self.current_shape_ns = Namespace(source_shape_full['namespace'])
        self.shapes_graph.bind(source_shape_full['prefix'], self.current_shape_ns)

        # we separate out mixins to process later
        have_mixins = []

        # now iterate through and build shapes
        for shape in source_shape_full['shapes']:
            ns_shape = self.current_shape_ns[shape['name']]
            if shape.get("shape-mixins"):
                have_mixins.append(shape)
                continue
            nodeshape_triple = (ns_shape, RDF.type, SH.NodeShape)
            self.shapes_graph.add(nodeshape_triple)
            self.add_tags_types_and_predicates(ns_shape, shape)
            print(f"Processed shape: {ns_shape}")

        # now we process things with mixins.
        # we assume mixins might contain other mixins,
        # which is why we have the double loops
        while len(have_mixins) > 0:

            # loop in reverse so that when we pop it dont blow up
            for i in range(len(have_mixins) - 1, -1, -1):
                shape = have_mixins[i]
                ns_shape = self.current_shape_ns[shape['name']]
                print(f"Processing mixin: {ns_shape}")
                mixins = shape.get("shape-mixins")
                skip = False
                for mixin in mixins:
                    ns_mixin = self.current_shape_ns[mixin]
                    if ns_mixin not in self.shapes_graph.subjects():
                        print(f"{ns_mixin} required for {ns_shape}, but not yet in graph.")
                        skip = True
                        continue
                if not skip:
                    nodeshape_triple = (ns_shape, RDF.type, SH.NodeShape)
                    self.shapes_graph.add(nodeshape_triple)
                    # if we get to this point, all mixins required for this
                    # particular shape are already in the graph and we can begin
                    # processing this shape
                    self.add_tags_types_and_predicates(ns_shape, shape)
                    self.add_all_mixins(ns_shape, shape)
                    have_mixins.pop(i)
        return self.shapes_graph
