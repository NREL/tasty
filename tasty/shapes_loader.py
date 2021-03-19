import os
import logging

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
            to_find = f"{self.schema.lower()}_all.ttl"
            assert to_find in os.listdir(
                self.generated_shapes_dir), f"{to_find} not in {self.generated_shapes_dir}. Make sure to run 'poetry run tasty generate-shapes'"
            self.shacl_schema_all_file = os.path.join(self.generated_shapes_dir, to_find)
        else:
            logging.warning("Only able to load single schema shapes at this time.")

    def load_all_shapes(self) -> Graph:
        all_shapes = Graph()
        all_shapes.parse(self.shacl_schema_all_file, format=guess_format(self.shacl_schema_all_file))
        return all_shapes
