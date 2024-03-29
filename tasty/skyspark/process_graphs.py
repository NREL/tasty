import json
import os
import re

from rdflib import Namespace, RDF, SH, BNode

from tasty import constants as tc
from tasty import graphs as tg
from tasty.skyspark import point_mapper as pm
from tasty.skyspark import helpers

PHCUSTOM = Namespace("https://project-haystack.org/def/custom#")
# POINT = Namespace("https://skyfoundry.com/def/point/3.0.27#")
# BACNET = Namespace("https://skyfoundry.com/def/bacnet/3.0.27#")

source_shapes_dir = os.path.join(os.path.dirname(__file__), '../source_shapes')

ph_versioned_ns_dict = {
    tc.V3_9_9: {
        'ph': tc.PH_3_9_9,
        'phict': tc.PHICT_3_9_9,
        'phscience': tc.PHSCIENCE_3_9_9,
        'phiot': tc.PHIOT_3_9_9,
    },
    tc.V3_9_10: {
        'ph': tc.PH_3_9_10,
        'phict': tc.PHICT_3_9_10,
        'phscience': tc.PHSCIENCE_3_9_10,
        'phiot': tc.PHIOT_3_9_10
    }
}


class SkysparkGraphProcessor:
    """
    This class is a wrapper for a number of methods which clean, process, and generate the RDF graphs required for
    validating SkySpark instance data against defined SHACL shapes using pySHACL's 'validate' method. The class is
    instantiated with a schema and version as well as a namespace-URI which is used to define the SkySpark namespace.
    Once an instance is created, it can clean the raw skyspark instance data and generate the data graph, SHACL shapes
    graph, and ontology graph needed for pySHACL's validation method. It can also parse the results graph generated
    by pySHACL to determine missing points.
    """

    def __init__(self, input_namespace_uri, schema=tc.HAYSTACK, version=tc.V3_9_10):
        self.input_namespace_uri = input_namespace_uri
        self.schema = schema
        self.version = version
        self.ontology_graph = tg.load_ontology(schema, version)

    def get_ontology_graph(self):
        return self.ontology_graph

    def clean_raw_skyspark_turtle(self, file_in, file_out):
        """
        Takes in a raw SkySpark turtle file, performs some cleanup processes on it, and saves it to
        a new file, designated by 'file_out'

        :param file_in: the filepath/filename of the raw file to process
        :param file_out: the filepath/filename in which to save the cleaned file

        Note regarding this method
        The raw data file generate by Skyspark cannot be parsed by rdflib as is, and also needs to be updated in a couple of other ways:

           1. The date-time fields generated by Skyspark cause errors in rdflibs parse function. These fields are removed
           2. The Skyspark namespace-prefix is and underscore "_" (this may be worth changing in the future), but more importantly this
           prefix is not associated with a URI namespace. The file will be parsed, however there is no way to reference the associated
           equipment as the namespace is not defined. The following prefix/namespace paring is added `@prefix _: <urn:/_#>`.
           3. Finally the project haystack namespaces that are listed in the raw file are version '3.9.9', however the shapes graph that
           is currently generated by tasty uses '3.9.10'. So the namespaces for the project haystack prefixes are updated to version 10.

        There are likely more elegant ways to handle these changes. For #3, we can likely generated a haystack version '3.9.9' graph to avoid
        this requirement. For #2 there is likely a way to bind this prefix to the graph prior to parsing the instance data file.
        """
        # read in the file
        with open(file_in, 'r') as raw_file:
            filedata = raw_file.read()

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
        """
        Generates a list of valid tags based on the given schema and the .json files in the associated source shape
        directory. This list of valid tags can then be used to remove extraneous tags from the data graph to aid in validation

        :return: a dict containing two lists - 'plain' is a list of the tags as plain strings, 'namespaced' is a list of the tags
        as UIRs with the proper namespaces.
        :rtype: a dict with the structure { 'plain': [...], 'namespaced': [...] }
        """

        # get the source shapes directory based on the given schema and create a list of all the json files in that directory
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
        """
        This method retrieves the list of valid tags, then checks the tags of each point in the given rdf grpah against this list.
        If the tags are not in the list of valid tags, they are removed from the graph

        :param data_graph: the rdf (instance data) graph to process
        """

        # get the list of valid tags
        valid_tags = self.get_valid_tags()
        valid_tags_ns = valid_tags['namespaced']

        # Iterate over all points in the graph (anything with an "equipRef" tag)
        for s1, p1, o1 in data_graph.triples((None, ph_versioned_ns_dict[self.version]['phiot']["equipRef"], None)):
            print(f"...processing node: \t{s1}")
            # iterate over each tag
            for s, p, o in data_graph.triples((s1, ph_versioned_ns_dict[self.version]['ph']["hasTag"], None)):
                # if the tag is not in the list of valid tags, remove it
                if o not in valid_tags_ns:
                    data_graph.remove((s, p, o))

    def add_first_class_point_types(self, data_graph):
        """
        This method adds the first-class-point-type to each point in the given rdf graph.

        :param data_graph: the rdf (instance data) graph to process
        """

        # load the point tree
        file = os.path.join(os.path.dirname(__file__), '../schemas/haystack/defs_3_9_10.ttl')
        pt = pm.PointTree(file, 'point')
        root = pt.get_root()

        # Get all 'points' that have a 'equipRef' tag
        for s, p, o in data_graph.triples((None, ph_versioned_ns_dict[self.version]['phiot']["equipRef"], None)):
            print(f"Point: \t{s}")
            print(f"Tags: ", end="")

            # get the tags for this point
            tags = []
            for s1, p1, o1 in data_graph.triples((s, ph_versioned_ns_dict[self.version]['ph']["hasTag"], None)):
                tag = o1[o1.find('#') + 1:]
                print(f"\t{tag}")
                tags.append(tag)

            # now determine first class point type
            fc_point = pt.determine_first_class_point_type(root, tags)
            print(f"\t...First Class Entity Type: {fc_point.type}\n")

            # add first class point type as class to the point
            data_graph.add((s, RDF.type, ph_versioned_ns_dict[self.version]['phiot'][fc_point.type]))
            # remove the tags associated with first class point
            for tag in fc_point.tags:
                # using all three namespaces because i do not know which is correct
                # TODO: develop method for determining proper namespace
                data_graph.remove((s, ph_versioned_ns_dict[self.version]['ph']["hasTag"], ph_versioned_ns_dict[self.version]['phiot'][tag]))
                data_graph.remove((s, ph_versioned_ns_dict[self.version]['ph']["hasTag"], ph_versioned_ns_dict[self.version]['phscience'][tag]))
                data_graph.remove((s, ph_versioned_ns_dict[self.version]['ph']["hasTag"], ph_versioned_ns_dict[self.version]['ph'][tag]))

    def add_target_nodes(self, shapes_graph, target_node, shape_name):
        """
        This method adds the given equip as a target node to the given shape against which to validate.

        :param shapes_graph: the rdf (SHACL) shapes graph against which validation is to be run
        :param target_node: the the sample equipment (as a URI) to be validated
        :param shape_name: the SHACL equipment shape (as a URI) against which to validate the sample equipment
        """
        # add Instance Equipment as target node to SHACL Equipment Shape
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        # add Instance Equipment as target node to SHACL Functional Groups Shapes
        for s, p, o in shapes_graph.triples((shape_name, SH.node, None)):
            shapes_graph.add((o, SH.targetNode, target_node))

    def get_data_graph(self, data_graph_filename):
        """
        This method generates and returns a cleaned and processed data graph given a file input that contains the instance data.
        The data graph can then be used with the pySHACL validate method.

        :param data_graph_filename: the filepath/filename of the raw instance data file from which to generate the data graph
        """
        data_graph = helpers.parse_file_to_graph(data_graph_filename, self.schema, self.version)
        self.remove_invalid_tags(data_graph)
        self.add_first_class_point_types(data_graph)
        return data_graph

    def get_shapes_graph(self, shapes_graph_filename, target_node, shape_name):
        """
        This method generates a (SHACL) shapes graph given a file input that contains the SHACL definitions, and adds the given
        'target_node' as a target node to the given 'shape_name' in the SHACL definition. The shapes graph can then be used with
        the pySHACL validate method.

        :param shapes_graph_filename: the filepath/filename of the SHACL shapes definitions from which to generate the shapes graph
        :param target_node: the the sample equipment (as a URI) to be validated
        :param shape_name: the SHACL equipment shape (as a URI) against which to validate the sample equipment
        """
        shapes_graph = helpers.parse_file_to_graph(shapes_graph_filename, self.schema, self.version)
        self.add_target_nodes(shapes_graph, target_node, shape_name)
        return shapes_graph

    def determine_missing_points(self, results_graph):
        """
        Given a results_graph generated by pySHACL's validate method, this method returns a list of points that were not validated
        (i.e. are missing) from the equipment.

        :param results_graph: the rdf results graph returned by pySHACL's validate method
        """
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
