from copy import deepcopy
from uuid import uuid4, UUID
from typing import List, Union, Set
import logging

from rdflib import Namespace, RDF, Graph, URIRef, Literal

import tasty.graphs as tg
import tasty.constants as tc
from tasty.shapes_generator import ShapesGenerator


class RefType:
    def __init__(self, type_uri: URIRef, type_docs: Literal):
        self._type_uri = type_uri
        self._type_docs = type_docs


class SimpleShape:
    def __init__(self, data, schema, version):
        self.name = data.get('name')
        self.type = data.get('type')
        self.schema = schema
        self.version = version
        self.tags = data.get('tags')
        self.tags_custom = data.get('tags-custom')
        self.docs_query = f'''SELECT ?docs {{ {URIRef(self.type).n3()} rdfs:comment ?docs . }}'''
        self.docs: str = ''

    def cast_to_entity(self, id=None) -> 'EntityType':
        ont = tg.load_ontology(self.schema, self.version)
        docs = ont.query(self.docs_query)
        if docs:
            docs = list(docs)
            self.docs = docs[0][0]
        et = EntityType(self.type, self.docs, self.schema, self.version)
        if self.tags:
            et.add_tags(self.tags, ont)
        if self.tags_custom:
            et.add_tags(self.tags_custom, ont)
        if id:
            et.set_id(id)
        return et

    def apply(self, equip_id, namespace, parent, equip_ref):
        entity = self.cast_to_entity(f"{equip_id}-{self.name}")
        entity.set_namespace(namespace)
        entity.add_relationship(equip_ref, parent)
        entity.sync()


class CompositeShape:
    def __init__(self, data, schema, version):
        self.name = data.get('name')
        self.type = data.get('type')
        self.schema = schema
        self.version = version
        self.shapes = data.get('shapes')
        self.shape_mixins = data.get('shape-mixins')
        self.required_shapes = data.get('requires')
        self.optional_shapes = data.get('optional')
        self.docs_query = f'''SELECT ?docs {{ {URIRef(self.type).n3()} rdfs:comment ?docs . }}'''
        self.docs: str = ''

    def cast_to_entity(self, id=None) -> 'EntityType':
        ont = tg.load_ontology(self.schema, self.version)
        docs = ont.query(self.docs_query)
        if docs:
            docs = list(docs)
            self.docs = docs[0][0]
        et = EntityType(self.type, self.docs, self.schema, self.version)
        if id:
            et.set_id(id)
        return et

    def apply_shape_mixins(self, equip_id, namespace, ref, entity, optional_points=False):
        if self.shape_mixins:
            for composite_shape in self.shape_mixins:
                if composite_shape.required_shapes:
                    for point in composite_shape.required_shapes:
                        point.apply(equip_id, namespace, entity, ref)
                if optional_points and composite_shape.optional_shapes:
                    for point in composite_shape.optional_shapes:
                        point.apply(equip_id, namespace, entity, ref)
        else:
            print('No mixins found for this composite shape')


class ShapesWrapper:
    def __init__(self, schema, version):
        self.sg = ShapesGenerator(schema, version)

    def bind(self):
        for file, file_data in self.sg.source_shapes_by_file.items():
            for shape in file_data['shapes']:
                keys = set(shape.keys())
                composite_shapes = {'predicates', 'shape-mixins'}
                simple_shapes = {'name', 'types'}
                if keys.intersection(composite_shapes):
                    continue
                if simple_shapes <= keys and len(shape.get('types')) == 1:
                    data = {
                        'name': shape['name'],
                        'type': tg.get_namespaced_term(self.sg.ontology, shape['types'][0])
                    }
                    if shape.get('tags'):
                        data['tags'] = shape.get('tags')
                    if shape.get('tags-custom'):
                        data['tags-custom'] = shape.get('tags-custom')

                    self.__setattr__(shape['name'].replace('-', '_'),
                                     SimpleShape(data, self.sg.schema, self.sg.version))

    def bind_composite(self):
        for file, file_data in self.sg.source_shapes_by_file.items():
            for shape in file_data['shapes']:
                keys = set(shape.keys())
                composite_shapes = {'predicates', 'shape-mixins'}
                if keys.intersection(composite_shapes):
                    data = self.evaluate_shape(shape)
                    self.__setattr__(data['name'].replace('-', '_'),
                                     CompositeShape(data, self.sg.schema, self.sg.version))

    def evaluate_shape(self, shape):
        data = {'name': shape['name']}
        if 'shape-mixins' in shape.keys() and 'predicates' not in shape.keys():
            # Composite shape with only mixins
            try:
                data['type'] = tg.get_namespaced_term(self.sg.ontology, shape['types'][0])
            except BaseException:
                # TODO: add functionality to infer type from mixins
                data['type'] = tg.get_namespaced_term(self.sg.ontology, 'point')
            data['shape-mixins'] = self.add_shapes(shape['shape-mixins'])
        else:
            # Composite shape with Required and Optional
            for category in shape['predicates'].keys():
                data['shapes'] = shape['predicates'][category][0]['shapes']
                try:
                    data['type'] = tg.get_namespaced_term(self.sg.ontology,
                                                          shape['predicates'][category][0]['types'][0])
                except BaseException:
                    data['type'] = tg.get_namespaced_term(self.sg.ontology, 'point')
                data[category] = self.add_shapes(data['shapes'])
        return data

    def add_shapes(self, shapes):
        shape_list = []
        for shape in shapes:
            try:
                s = self.__getattribute__(shape.replace('-', '_'))
                shape_list.append(s)
            except BaseException:
                continue
        return shape_list


class EntityType:
    """
    A generic entity type, identified via its type_uri. This should be
    considered as an instance of a first class type from one of the ontologies,
    i.e. a point, ahu, etc.
    """

    def __init__(self, type_uri: URIRef, type_docs: Literal, schema, version, namespace: Namespace = None):
        self._type_uri = type_uri
        self._type_docs = type_docs
        self._namespace = namespace
        self._id: UUID = None
        self.node: URIRef = None
        self.graph: Graph = None
        self.schema = schema
        self.version = version
        self.tags: Set = set()
        self.tags_custom: Set = set()
        self.relationships: Set = set()

        if schema == tc.HAYSTACK:
            self._custom_namespace = tc.PH_CUSTOM
        elif schema == tc.BRICK:
            self._custom_namespace = tc.BRICK_CUSTOM

    def __str__(self):
        return str(self._type_uri)

    def type_uri(self) -> str:
        return self.__str__()

    def type_docs(self) -> str:
        return str(self._type_docs)

    def deep_copy(self) -> 'EntityType':
        """Return a deep copy of the current self"""
        return deepcopy(self)

    def set_id(self, new_id=None) -> UUID:
        """
        Set the id or generate a
        :return: the uuid
        """
        if new_id is None and self._id is None:
            self._id = uuid4()
        elif new_id and self._id is None:
            self._id = new_id
        else:
            print(f"id already set, can't override.")
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

    def add_tags(self, tags: List[str], ontology: Graph):
        assert isinstance(tags, list)
        for t in tags:
            ns_term = tg.get_namespaced_term(ontology, t)
            if ns_term:
                self.tags.add(ns_term)
            else:
                logging.warning(f"{t} not found. adding under custom namespace as: {self._custom_namespace[t]}")
                self.tags_custom.add(self._custom_namespace[t])

    def add_relationship(self, predicate: RefType, obj: 'EntityType'):
        if obj.graph and self.graph:
            assert obj.graph is self.graph, f"Objects cannot be bound to a different graph, cannot add"
            obj.set_node_name()
            self.set_node_name()
        elif obj.graph:
            self.bind_to_graph(obj.graph)
            print(f"Bound {self.node} to graph")
        elif self.graph:
            obj.bind_to_graph(self.graph)
            print(f"Bound {obj.node} to graph")
        else:
            print("Atleast one of the nodes must be bound to a graph")
            return False
        self.relationships.add((predicate, obj))

    def sync(self):
        self.set_node_name()
        if not self.graph:
            return False
        # Make sure all the objects have node names set
        for pred, obj in self.relationships:
            self.graph.add((self.node, pred._type_uri, obj.node))
            obj.sync()
        if self.schema == tc.HAYSTACK:
            for tag in self.tags:
                self.graph.add((self.node, tc.PH_DEFAULT.hasTag, tag))
            for tag in self.tags_custom:
                self.graph.add((self.node, tc.PH_DEFAULT.hasTag, tag))


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
        self.schema = schema
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
            self.__setattr__(name.replace('-', '_'), EntityType(node[0], node[1], self.schema, self.version))

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


class HaystackRefDefs(EntityDefs):
    """
    A class with attributes corresponding to Haystack object properties
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.HAYSTACK, version)
        self.query = '''SELECT ?r ?doc WHERE {
            ?r a owl:ObjectProperty .
            ?n rdfs:comment ?doc .
        }'''

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
            self.__setattr__(name.replace('-', '_'), RefType(node[0], node[1]))


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

class BrickZoneDefs(EntityDefs):
    """
    A class with attributes corresponding to first class Brick equipment types.
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.BRICK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* brick:Zone .
            ?n rdfs:label ?doc .
        }'''

class BrickLocationDefs(EntityDefs):
    """
    A class with attributes corresponding to first class Brick equipment types.
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.BRICK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* brick:Location .
            ?n rdfs:label ?doc .
        }'''

class BrickRefDefs(EntityDefs):
    """
    A class with attributes corresponding to Haystack object properties
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.BRICK, version)
        self.query = '''SELECT ?r ?doc WHERE {
            ?r a owl:ObjectProperty .
            ?n skos:definition ?doc .
        }'''

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
            self.__setattr__(name.replace('-', '_'), RefType(node[0], node[1]))

class BrickGasDefs(EntityDefs):
    """
    A class with attributes corresponding to first class Brick equipment types.
    Attributes are only added upon calling the 'bind' method.
    """

    def __init__(self, version):
        super().__init__(tc.BRICK, version)
        self.query = '''SELECT ?n ?doc WHERE {
            ?n rdfs:subClassOf* brick:Gas .
            ?n rdfs:label ?doc .
        }'''
