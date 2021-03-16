from copy import deepcopy
from uuid import uuid4

from rdflib import Namespace, RDF

import tasty.graphs as tg
import tasty.constants as tc


class Instance:
    def __init__(self, data, namespace: Namespace = None):
        self._type_uri = data[0]
        self._type_docs = data[1]
        self._namespace = namespace
        self._id = None
        self.node = None
        self.graph = None

    def __str__(self):
        return str(self._type_uri)

    def type_uri(self) -> str:
        return self.__str__()

    def type_docs(self) -> str:
        return str(self._type_docs)

    def deep_copy(self):
        return deepcopy(self)

    def gen_uuid(self) -> None:
        if self._id is None:
            self._id = uuid4()
        return self._id

    def set_namespace(self, ns: [str, Namespace]):
        assert isinstance(ns, (str, Namespace)), "ns must be a string or Namespace type"
        if isinstance(ns, str):
            self._namespace = Namespace(ns)
        else:
            self._namespace = ns
        return True

    def bind_to_graph(self, g):
        assert self._id is not None, f"_id must be defined, run gen_uuid() to generate a random id"
        assert self._namespace is not None, f"_namespace must be defined, run set_namespace()"
        self.graph = g
        if self.node is None:
            self.node = self._namespace[str(self._id)]
        self.graph.add((self.node, RDF.type, self._type_uri))
        return True

    # def sync(self):


class EntityDefs:
    def __init__(self, schema, version):
        self.version = version
        self.ontology = tg.load_ontology(schema, version)
        self.namespaces = list(self.ontology.namespaces())
        self.query: str = None
        self.result: str = None

    def bind(self):
        """
        Create an attribute for each type of thing
        :return:
        """
        assert self.query is not None, 'A query string must be defined'
        self.result = self.ontology.query(self.query)
        for node in self.result:
            name = node[0].split('#')[1]
            self.__setattr__(name.replace('-', '_'), Instance(node))

    def find(self, to_find, case_sensitive=False):
        if case_sensitive:
            if isinstance(to_find, str):
                return [x for x in self.__dict__.keys() if to_find in x]
            elif (isinstance(to_find, list)):
                return [x for x in self.__dict__.keys() if any(y in self.__dict__.keys() for y in to_find)]
        else:
            lower = {}
            for x in self.__dict__.keys():
                lower[x.lower()] = x
            if isinstance(to_find, str):
                return [lower[x] for x in lower.keys() if to_find.lower() in x]
            elif isinstance(to_find, list):
                return [lower[x] for x in lower.keys() if all(y.lower() in x for y in to_find)]


class HaystackPointDefs(EntityDefs):
    def __init__(self, version):
        super().__init__(tc.HAYSTACK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* phIoT:point .
            ?n rdfs:comment ?doc .
        }'''


class HaystackEquipDefs(EntityDefs):
    def __init__(self, version):
        super().__init__(tc.HAYSTACK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* phIoT:equip .
            ?n rdfs:comment ?doc .
        }'''


class BrickPointDefs(EntityDefs):
    def __init__(self, version):
        super().__init__(tc.BRICK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* brick:Point .
            ?n rdfs:label ?doc .
        }'''


class BrickEquipmentDefs(EntityDefs):
    def __init__(self, version):
        super().__init__(tc.BRICK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* brick:Equipment .
            ?n rdfs:label ?doc .
        }'''
