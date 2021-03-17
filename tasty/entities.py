from copy import deepcopy
from uuid import uuid4, UUID
from typing import List, Union

from rdflib import Namespace, RDF, Graph, URIRef, Literal

import tasty.graphs as tg
import tasty.constants as tc


class EntityType:
    """
    A generic entity type, identified via its type_uri. This should be
    considered as an instance of a first class type from one of the ontologies,
    i.e. a point, ahu, etc.
    """

    def __init__(self, type_uri: URIRef, type_docs: Literal, namespace: Namespace = None):
        self._type_uri = type_uri
        self._type_docs = type_docs
        self._namespace = namespace
        self._id: UUID = None
        self.node: URIRef = None
        self.graph: Graph = None

    def __str__(self):
        return str(self._type_uri)

    def type_uri(self) -> str:
        return self.__str__()

    def type_docs(self) -> str:
        return str(self._type_docs)

    def deep_copy(self) -> 'EntityType':
        """Return a deep copy of the current self"""
        return deepcopy(self)

    def gen_uuid(self) -> UUID:
        """
        Generate a random uuid for this instance
        :return: the uuid
        """
        if self._id is None:
            self._id = uuid4()
        return self._id

    def set_namespace(self, ns: Union[str, Namespace]) -> bool:
        """
        Set the _namespace for this specific entity.
        :param ns:
        :return: a bool indicating success
        """
        assert isinstance(ns, (str, Namespace)), "ns must be a string or Namespace type"
        if isinstance(ns, str):
            self._namespace = Namespace(ns)
        else:
            self._namespace = ns
        return True

    def set_node_name(self):
        """Sets the node name based on the _id and _namespace if not yet set"""
        assert self._id is not None, f"_id must be defined, run gen_uuid() to generate a random id"
        assert self._namespace is not None, f"_namespace must be defined, run set_namespace()"
        if self.node is None:
            self.node = self._namespace[str(self._id)]

    def bind_to_graph(self, g: Graph) -> bool:
        """
        Adds a triple representing itself to the graph.
        :param g: the graph to add the triple to
        :return: a bool indicating success
        """
        self.graph = g
        self.set_node_name()
        self.graph.add((self.node, RDF.type, self._type_uri))
        return True


class EntityDefs:
    """
    A base class giving access to first class ontological types
    via simple attributes.
    """

    def __init__(self, schema: str, version: str) -> None:
        """
        :param schema: see load_ontology for supported values
        :param version: see load_ontology for supported values
        """
        self.version = version
        self.ontology = tg.load_ontology(schema, version)
        self.namespaces = list(self.ontology.namespaces())
        self.query: str = None
        self.result: str = None

    def bind(self) -> None:
        """
        Create an attribute for each first class type. The value of each
        attribute is an EntityType.
        :return:
        """
        assert self.query is not None, 'A query string must be defined'
        self.result = self.ontology.query(self.query)
        for node in self.result:
            name = node[0].split('#')[1]
            self.__setattr__(name.replace('-', '_'), EntityType(node[0], node[1]))

    def find(self, to_find: Union[str, list], case_sensitive=False) -> List:
        """
        Given a string or list of strings, return attributes of the class
        (corresponding to first class entities) where the string(s) are present.
        :param to_find:
        :param case_sensitive: match case in the search
        :return: a list of attribute names matching the search
        """
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
    """
    A class with attributes corresponding to first class Haystack point types
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.HAYSTACK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* phIoT:point .
            ?n rdfs:comment ?doc .
        }'''


class HaystackEquipDefs(EntityDefs):
    """
    A class with attributes corresponding to first class Haystack equipment types
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.HAYSTACK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* phIoT:equip .
            ?n rdfs:comment ?doc .
        }'''


class BrickPointDefs(EntityDefs):
    """
    A class with attributes corresponding to first class Brick point types.
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.BRICK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* brick:Point .
            ?n rdfs:label ?doc .
        }'''


class BrickEquipmentDefs(EntityDefs):
    """
    A class with attributes corresponding to first class Brick equipment types.
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.BRICK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* brick:Equipment .
            ?n rdfs:label ?doc .
        }'''
