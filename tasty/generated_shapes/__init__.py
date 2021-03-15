import os

from rdflib import Graph
from rdflib.util import guess_format

generated_dir = os.path.dirname(__file__)


def load_all_shapes_and_merge():
    g = Graph()
    files = [os.path.join(generated_dir, f) for f in os.listdir(generated_dir) if f.endswith('.ttl')]
    for file in files:
        g.parse(file, format=guess_format(file))
    return g
