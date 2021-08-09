from rdflib import OWL, RDF, RDFS
from tasty import constants as tc
from tasty import graphs as tg


class PointNode:

    # -- Class Constructor --
    def __init__(self, type: str, parent):
        self.type = type
        self.parent = parent
        self.children = []
        self.tags = []
        self.load_tags()

    def add_child(self, child: 'PointNode'):
        """
        Add a child (node) to the given node

        :param child: the child node to add
        :type child: PointNode
        """
        self.children.append(child)

    def load_tags(self):
        """
        Load the tags for this node based on the 'type' string passed in at instantiation. This method will split the
        'type' on hyphens and add each word as a tag to the node. The tag "point" is removed (this may be updated at
        a later time)
        """
        self.tags = self.type.split("-")

        # remove empty strings and 'point'
        # eventually we may want "point" as a tag, but it's currently not in the "source" or "generated" shapes
        for tag in self.tags:
            if(tag == '' or tag == 'point'):
                self.tags.remove(tag)

# Note this data structure implicitly assumes that points fall into a tree-like hierarchy and that each point can only be
# a subtype of ONE point type. This may not be the actual case in some systems and may need to be re-considered at another
# time. Also because of this, if 'his', 'cur', 'writable', or 'weather' tags are not removed, first class point may not be
# correct, as it assumes mutual exclusivity.


class PointTree:

    # -- Class Constructor --
    def __init__(self, filename: str, root_type: str):
        self.root_type = root_type
        self.filename = filename
        self.root = None
        self.generate_point_tree(filename)

    def get_root(self) -> 'PointNode':
        return self.root

    def generate_point_tree(self, filename: str):
        """
        Generates/populates a PointTree based on a schema definition file (e.g. 'schemas/haystack/defs_3_9_10.ttl') which
        describes the desired ontology.

        :param filename: the filepath/filename from which to generate the PointTree
        """
        # parse the file to an rdf graph
        graph = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_10)
        graph.parse(filename, format='turtle')

        # get root of graph from the rdf graph
        root_uri = tc.PHIOT_3_9_10[self.root_type]
        count = 0
        for s, p, o in graph.triples((root_uri, RDF.type, OWL.Class)):
            count += 1
            # create new root node
            # for now passing in a type of "point" - the load_tags method will ignore this so no tags are added to the root
            self.root = PointNode("point", None)

        # assert that there can only be one root value
        assert count == 1

        # now iterate over all items which are a subclass of "point" and recursively add all subnodes
        self.add_subnodes(graph, self.root, root_uri)

    def add_subnodes(self, graph, parentNode: 'PointNode', parentUri):
        """
        Adds all subnodes of a given parent node to the PointTree. Given an rdf graph and a parent node in that graph,
        this method adds subtypes of the root node as children to the root, and recursively does the same for each child
        node untill all subtypes are discovered and the PointTree is fully populated.

        :param graph: the rdf graph describing the given ontology from which to construct the PointTree
        :param parentNode: the parent node as a PointNode, for which all subtypes should be added
        :param parentUri: the uri of the parent node in the rdf graph
        """
        for s, p, o in graph.triples((None, RDFS.subClassOf, parentUri)):
            # print(s[s.find('#')+1:])
            new_node = PointNode(s[s.find('#') + 1:], parentNode)
            parentNode.add_child(new_node)
            self.add_subnodes(graph, new_node, s)

    def determine_first_class_point_type(self, root: 'PointNode', input_tags) -> 'PointNode':
        """
        Determines the first-class-point-type based on a given set of tags starting at the given root node.
        This method looks at the root node and then recursively at each subnode untill the set of tags stops
        matching the point type.

        :param root: the node at which to begin checking against
        :param input_tags: a list of the tags to use to identify the point type
        """
        # iterate over children node
        for node in root.children:

            counter = 0
            # iterate over the node tags
            for tag in node.tags:
                # if the tag is not in the input tag set, break and go to next node
                if(tag not in input_tags):
                    break
                # otherwise the tag is in the set, increment the count
                counter += 1
                # if all tags are there, then the input point is a subtype of this node
                if counter == len(node.tags):
                    # check the next level of nodes
                    return self.determine_first_class_point_type(node, input_tags)

        # Otherwise the point does not match any of the tags; return the root (i.e. the most specific point type mathced thus far)

        # (but if the root is one of the immediate children of 'point', then just return 'point' - this is idiosyncratic to the
        # current implementation of the the PointTree and schema)
        if root.parent is self.root:
            return self.root

        return root

# -------------------- Sample Code --------------------------)
# p = PointNode("air-sensor-sp", "parent")
# print(p.tags)
# print(p.parent)

# pt = PointTree('schemas/haystack/defs_3_9_10.ttl', 'point')
# print("created 'PointTree' using 'schemas/haystack/defs_3_9_10.ttl' and 'point' as the root element")
# r = pt.get_root()
# # print(len(r.tags))
# print(f"root: {r.type} \ttags: {r.tags}")
# for child in r.children:
#     print(f"\tchild: {child.type:<20} tags: {child.tags}")


# fcn = pt.determine_first_class_point_type(r, ["zone", "temp", "air", "sp"])
# print(fcn.type)
