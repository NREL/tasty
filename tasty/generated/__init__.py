import os

from rdflib import Graph
from rdflib.util import guess_format

generated_dir = os.path.dirname(__file__)
core_file = os.path.join(generated_dir, 'core.ttl')
core_shapes = Graph()
core_shapes.parse(core_file, format=guess_format(core_file))


class Shapes:
    def __init__(self):
        self.core = core_shapes

    def shapes_as_attr(self):
        q = """SELECT ?n ?tag WHERE {
            ?n a sh:NodeShape .
        }
        """
        result = self.core.query(q)
        for node in result:
            name = node[0].split('#')[1]
            self.__setattr__(name, node)
