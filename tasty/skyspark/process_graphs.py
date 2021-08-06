import re
import os
import json

from rdflib import Namespace, RDF, SH, BNode

from tasty import constants as tc
from tasty import graphs as tg
from tasty.skyspark import point_mapper as pm
from tasty.skyspark import helpers


# ----------------------------------------
# Variables and Constants
# ----------------------------------------

PHCUSTOM = Namespace("https://project-haystack.org/def/custom#")
# POINT = Namespace("https://skyfoundry.com/def/point/3.0.27#")
# BACNET = Namespace("https://skyfoundry.com/def/bacnet/3.0.27#")

source_shapes_dir = os.path.join(os.path.dirname(__file__), '../source_shapes')

# ----------------------------------------
# Class Definition
# ----------------------------------------


class SkysparkGraphProcessor:

    def __init__(self, input_namespace_uri, schema=tc.HAYSTACK, version=tc.V3_9_10):
        self.input_namespace_uri = input_namespace_uri
        self.schema = schema
        self.version = version
        self.ontology_graph = tg.load_ontology(schema, version)

    def get_ontology_graph(self):
        return self.ontology_graph

    def clean_raw_skyspark_turtle(self, file_in, file_out):

        # read in the file
        with open(file_in, 'r') as raw_file:
            filedata = raw_file.read()

        # REMOVE DATE-TIME FIELDS
        # -------------------------
        # remove date-time fields in the middle of the definition
        filedata = re.sub(r'\n.*\^{2}xsd:dateTime.*;', '', filedata)
        # remove date-time fields at the end of the definition
        filedata = re.sub(r';\n.*\^{2}xsd:dateTime.*.', '.', filedata)

        # add urn namespace to graph
        filedata = re.sub('@prefix', '@prefix _: <' + self.input_namespace_uri + '> .\n@prefix', filedata, count=1)

        # change the project haystack namespaces to v10
        filedata = re.sub('/3.9.9', '/3.9.10', filedata)

        # save to clean file
        with open(file_out, 'w') as clean_file:
            clean_file.write(filedata)

    def get_valid_tags(self):

        source_shapes_schema_dir = os.path.join(source_shapes_dir, self.schema.lower())
        files = [os.path.join(source_shapes_schema_dir, f) for f in
                 os.listdir(source_shapes_schema_dir) if f.endswith('.json')]

        valid_tags = []
        valid_tags_ns = []

        # go through schema files and extract valid tags
        for file in files:
            # open file and read in json to python dict
            with open(file, 'r') as f:
                filedata = json.loads(f.read())
                # for each shape
                for shape in filedata['shapes']:
                    # add tags if not already added to the tags list
                    if 'tags' in shape:
                        for tag in shape['tags']:
                            if tag not in valid_tags:
                                valid_tags.append(tag)
                    # add custom tags if not already added to the tags list
                    if 'tags-custom' in shape:
                        for tag in shape['tags-custom']:
                            if tag not in valid_tags:
                                valid_tags.append(tag)

        print("...generated tag list")
        print("...adding namespaces")
        # sort tags list
        valid_tags = sorted(valid_tags)

        # add namespaces to all valid tags
        for tag in valid_tags:
            tag_ns = tg.get_namespaced_term(self.ontology_graph, tag)
            # take care of custom tags
            if tag_ns is False:
                tag_ns = PHCUSTOM[tag]
            valid_tags_ns.append(tag_ns)

        tags_dict = {
            'plain': valid_tags,
            'namespaced': valid_tags_ns
        }

        return tags_dict

    def remove_invalid_tags(self, data_graph):
        valid_tags = self.get_valid_tags()
        valid_tags_ns = valid_tags['namespaced']

        # keep only valid tags
        for s1, p1, o1 in data_graph.triples((None, tc.PHIOT_3_9_10["equipRef"], None)):
            print(f"...processing node: \t{s1}")
            for s, p, o in data_graph.triples((s1, tc.PH_3_9_10["hasTag"], None)):
                if o not in valid_tags_ns:
                    data_graph.remove((s, p, o))

    def add_first_class_point_types(self, data_graph):
        # load the point tree
        file = os.path.join(os.path.dirname(__file__), '../schemas/haystack/defs_3_9_10.ttl')
        pt = pm.PointTree(file, 'point')
        root = pt.get_root()

        # Get all 'points' that have a 'equipRef' tag
        for s, p, o in data_graph.triples((None, tc.PHIOT_3_9_10["equipRef"], None)):
            print(f"Point: \t{s}")
            print(f"Tags: ", end="")

            # get the tags for this point
            tags = []
            for s1, p1, o1 in data_graph.triples((s, tc.PH_3_9_10["hasTag"], None)):
                tag = o1[o1.find('#') + 1:]
                print(f"\t{tag}")
                tags.append(tag)

            # now determine first class point type
            fc_point = pt.determine_first_class_point_type(root, tags)
            print(f"\t...First Class Entity Type: {fc_point.type}\n")

            # add first class point type as class to the point
            data_graph.add((s, RDF.type, tc.PHIOT_3_9_10[fc_point.type]))
            # remove the tags associated with first class point
            for tag in fc_point.tags:
                # using all three namespaces because i do not know which is correct
                # TODO: develop method for determining proper namespace
                data_graph.remove((s, tc.PH_3_9_10["hasTag"], tc.PHIOT_3_9_10[tag]))
                data_graph.remove((s, tc.PH_3_9_10["hasTag"], tc.PHSCIENCE_3_9_10[tag]))
                data_graph.remove((s, tc.PH_3_9_10["hasTag"], tc.PH_3_9_10[tag]))

    def add_target_nodes(self, shapes_graph, target_node, shape_name):
        # add Instance Equipment as target node to SHACL Equipment Shape
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        # add Instance Equipment as target node to SHACL Functional Groups Shapes
        for s, p, o in shapes_graph.triples((shape_name, SH.node, None)):
            shapes_graph.add((o, SH.targetNode, target_node))

    def get_data_graph(self, data_graph_filename):
        data_graph = helpers.parse_file_to_graph(data_graph_filename, self.schema, self.version)
        self.remove_invalid_tags(data_graph)
        self.add_first_class_point_types(data_graph)
        return data_graph

    def get_shapes_graph(self, shapes_graph_filename, target_node, shape_name):
        shapes_graph = helpers.parse_file_to_graph(shapes_graph_filename, self.schema, self.version)
        self.add_target_nodes(shapes_graph, target_node, shape_name)
        return shapes_graph

    def determine_missing_points(self, results_graph):
        missing_points = []

        # Find the Validation Results
        for subject, predicate, object in results_graph.triples((None, RDF.type, SH.ValidationResult)):
            # check if Validation result points to a BNode
            for node in results_graph.objects(subject=subject, predicate=SH.sourceShape):
                # if it points to a BNode wee assume it's a constraint on a functional group has a `sh:qualifiedValueShape`
                # which should be a URI of one of the simple shapes - our missing point
                if isinstance(node, BNode):
                    point = results_graph.value(subject=node, predicate=SH.qualifiedValueShape)
                    missing_points.append(point)

        return missing_points
