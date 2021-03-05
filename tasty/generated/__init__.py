import os

from rdflib import Graph
from rdflib.util import guess_format

generated_dir = os.path.dirname(__file__)
core_file = os.path.join(generated_dir, 'core.ttl')
core_shapes = Graph()
core_shapes.parse(core_file, format=guess_format(core_file))

core_file2 = os.path.join(generated_dir, 'core_v2.ttl')
core_shapes2 = Graph()
core_shapes2.parse(core_file2, format=guess_format(core_file2))


# class Shapes:
#     def __init__(self):
#         self.core = core_shapes
#
#     def shapes_as_attr(self):
#         q = """SELECT ?n ?tag WHERE {
#             ?n a sh:NodeShape .
#         }
#         """
#         result = self.core.query(q)
#         for node in result:
#             name = node[0].split('#')[1]
#             self.__setattr__(name, node)
