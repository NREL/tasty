import os
from rdflib import OWL, RDF, RDFS
from tasty import constants as tc
from tasty import graphs as tg


class PointNode:

    def __init__(self, type: str, parent):
        self.type = type
        self.parent = parent
        self.children = []
        self.tags = []
        self.load_tags()

    def add_child(self, child):
        self.children.append(child)

    def load_tags(self):
        # # ignore an empty string
        # if(self.type != ""):

        self.tags = self.type.split("-")

        # remove empty strings and 'point'
        for tag in self.tags:
            if(tag == '' or tag == 'point'):
                self.tags.remove(tag)


class PointTree:
    def __init__(self, file_name: str, root_type: str):
        self.root_type = root_type
        self.file_name = file_name
        self.root = None
        self.generate_point_tree(file_name)

    def get_root(self) -> 'PointNode':
        return self.root

    def generate_point_tree(self, file_name: str):
        graph = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_10)
        f = os.path.join(os.path.dirname(__file__), file_name)
        graph.parse(f, format='turtle')

        # get root of graph from rdf graph
        root_uri = tc.PHIOT_3_9_10[self.root_type]
        count = 0
        for s, p, o in graph.triples((root_uri, RDF.type, OWL.Class)):
            count += 1
            # create new root node
            # for now passing in an empty string so that no tags are added to the root
            # eventually we may want "point" as a tag, but it's currently not in the generated shapes
            self.root = PointNode("point", None)

        # assert that there can only be one root value
        assert count == 1

        # now iterate over all items which are a subclass of "point"
        self.add_subnodes(graph, self.root, root_uri)

    def add_subnodes(self, graph, parentNode: 'PointNode', parentUri):
        for s, p, o in graph.triples((None, RDFS.subClassOf, parentUri)):
            # print(s[s.find('#')+1:])
            new_node = PointNode(s[s.find('#') + 1:], parentNode)
            parentNode.add_child(new_node)
            self.add_subnodes(graph, new_node, s)

    def determine_first_class_point_type(self, root: 'PointNode', input_tags) -> 'PointNode':
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

        # if the point does not match any of the tags, than return the root
        # print(root.parent)
        # print(self.root)
        if root.parent is self.root:
            # print("same")
            return self.root
        return root


# print("hello")
# p = PointNode("air-sensor-sp", "parent")
# print(p.tags)
# print(p.parent)

# pt = PointTree('schemas/haystack/defs_3_9_10.ttl', 'point')
# r = pt.get_root()
# print(len(r.tags))

# fcn = pt.determine_first_class_point_type(r, ["zone", "temp", "air", "sp"])
# print(fcn.type)
