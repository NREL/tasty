import os

from rdflib import Graph
from rdflib.util import guess_format

import tasty.constants as tc


class ShapesLoader:
    """
    Wrapper class to merge all SHACL shape files into a single RDF Graph.
    Can optionally merge only files specific to a schema, i.e. Haystack or Brick.
    """

    def __init__(self, schema=None):
        self.schema = schema
        self.root_dir = os.path.dirname(__file__)
        self.source_shapes_dir = os.path.join(self.root_dir, 'source_shapes')
        self.generated_shapes_dir = os.path.join(self.root_dir, 'generated_shapes')
        if schema:
            assert self.schema in tc.SUPPORTED_SCHEMAS.keys(), f"schema must be one of: {tc.SUPPORTED_SCHEMAS.keys()}"
            self.shacl_schema_files = [os.path.join(self.generated_shapes_dir, f) for f in
                                       os.listdir(self.generated_shapes_dir) if f.startswith(self.schema.lower())]
        else:
            self.shacl_schema_files = [os.path.join(self.generated_shapes_dir, f) for f in
                                       os.listdir(self.generated_shapes_dir)]

    def load_all_and_merge(self) -> Graph:
        all_shapes = Graph()
        for shape_file in self.shacl_schema_files:
            all_shapes.parse(shape_file, format=guess_format(shape_file))
        all_shapes.serialize('all_shapes.ttl', format='turtle')
        return all_shapes
