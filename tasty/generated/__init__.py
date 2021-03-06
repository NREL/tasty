import os

from rdflib import Graph
from rdflib.util import guess_format

generated_dir = os.path.dirname(__file__)
core_file = os.path.join(generated_dir, 'core_v1.ttl')
core_shapes = Graph()
core_shapes.parse(core_file, format=guess_format(core_file))

core_file2 = os.path.join(generated_dir, 'core_v2.ttl')
core_shapes2 = Graph()
core_shapes2.parse(core_file2, format=guess_format(core_file2))
