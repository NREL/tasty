import os

from typing import List, Set, Tuple
import yaml
import json
import jsonschema
from jsonschema import validate
from rdflib.namespace import Namespace
from rdflib import Graph

import tasty.graphs as tg
import tasty.constants as tc
import tasty.exceptions as te


class EntityTemplate:
    def __init__(self, entity_type: Set, typing_properties: Set, properties: dict):
        self.entity_type = entity_type
        self.typing_properties = typing_properties
        self.other_properties = properties

    def get_entity_type(self) -> Set[str]:
        """
        Just get terms, no namespaces
        :return: [Set[str]]
        """
        terms = set()
        for et in self.entity_type:
            ns, term = et
            terms.add(term)
        return terms

    def get_typing_info(self) -> Set[str]:
        """
        Get terms for the entity_type and typing_properties, no namespaces
        :return: [Set[str]]
        """
        terms = set()
        for et in self.entity_type:
            ns, term = et
            terms.add(term)
        for tp in self.typing_properties:
            ns, term = tp
            terms.add(term)
        return terms

    def get_other_properties(self) -> dict:
        """
        Get other_properties as hash map of keys, values, no namespaces
        :return: [dict]
        """
        properties = {}
        for k, v in self.other_properties.items():
            ns, term = k
            properties[term] = v
        return properties

    def get_all_metadata_simple(self) -> dict:
        """
        Get hash map of all metadata, no namespaces
        :return: [dict]
        """
        meta = self.get_other_properties()
        typing_info = self.get_typing_info()
        for info in typing_info:
            meta[info] = None
        return meta

    def get_namespaces(self) -> Set[Namespace]:
        """
        Get all unique Namespaces for the entity template
        :return: [Set[Namespace]]
        """
        all_ns = set()
        for et in self.entity_type:
            ns, term = et
            all_ns.add(ns)
        for tp in self.typing_properties:
            ns, term = tp
            all_ns.add(ns)
        for op in self.other_properties:
            ns, term = op
            all_ns.add(ns)
        return all_ns


class PointGroupTemplate:
    def __init__(self, template: dict):
        self.template = template
        self.template_schema: dict = None
        self.is_valid: bool = False
        self.validation_error: str = None
        self.id: str = None
        self.symbol: str = None
        self.description: str = None
        self.schema: str = None
        self.version: str = None
        self.telemetry_points: dict = None
        self.telemetry_point_entities: List[EntityTemplate] = None
        self.validate_template_against_schema()

    def validate_template_against_schema(self, schema_path=os.path.join(tc.SCHEMAS_DIR, 'template.schema.json')) -> None:
        self.template_schema = load_template_schema(path_to_file=schema_path)
        self.is_valid, self.validation_error = validate_template_against_schema(self.template, self.schema)
        if not self.is_valid:
            raise te.TemplateValidationError(self.validation_error)

    def populate_template_basics(self) -> None:
        """
        Only populate template if valid
        :return:
        """
        if self.is_valid:
            self.id = self.template['id']
            self.symbol = self.template['symbol']
            self.description = self.template['description']
            self.schema = self.template['schema']
            self.version = self.template['version']
            self.telemetry_points = self.template['telemetry_point_types']

    def populate_telemetry_templates(self) -> None:
        self.telemetry_point_entities = resolve_telemetry_points_to_entity_templates(self.telemetry_points, self.schema, self.version)

# class TemplateLibrary:
#     def __init__(self):
#         self.name_space: str
#         self.templates: List[Template] = []
#
#     def add_templates(self, templates: List[Template]):
#         for t in templates:
#             self.templates.append(t)
#
#     def add_template(self, template: Template):
#         self.templates.append(template)


def validate_template_against_schema(instance: dict, schema: dict) -> Tuple[bool, str]:
    """
    Validate a single template against the template schema
    :param instance: [dict] the template to validate
    :param schema: [dict] the schema to validate against
    :return:
    """
    try:
        validate(instance, schema)
        return True, 'No errors'
    except jsonschema.exceptions.ValidationError as err:
        return False, err.message


def load_template_file(path_to_file: str) -> List[dict]:
    """
    Read in a template file and return templates
    :param path_to_file: [str]
    :return:
    """
    if not os.path.isfile(path_to_file):
        raise FileNotFoundError
    with open(path_to_file, 'r') as fp:
        templates = yaml.load(fp, Loader=yaml.FullLoader)
    return templates


def load_template_schema(path_to_file: str) -> dict:
    """
    Load in the template schema and return
    :param path_to_file: [str]
    :return:
    """
    if not os.path.isfile(path_to_file):
        raise FileNotFoundError
    with open(path_to_file, 'r') as fp:
        schema = json.load(fp)
    return schema


def resolve_telemetry_points_to_entity_templates(telemetry_point_types: dict, schema: str, version: str) -> List[
        EntityTemplate]:
    ont = tg.load_ontology(schema, version)
    entity_templates: List = []
    for point_type, properties in telemetry_point_types.items():
        if schema == 'Haystack':
            valid_namespaced_terms = _get_namespaced_terms(ont, point_type)
            entity_types, typing_properties = _haystack_get_entities_and_typing_properties(ont, valid_namespaced_terms)
            other_properties = _haystack_get_other_properties(ont, properties)
        entity_templates.append(EntityTemplate(entity_types, typing_properties, other_properties))
    return entity_templates


def _get_namespaced_terms(ontology: Graph, terms: str) -> Set[Tuple[Namespace, str]]:
    """
    Return a (Namespace, term) for each candidate term, delimited by '-'
    :param ontology: [Graph] A loaded ontology
    :param terms: [str] A Brick class, such as 'Discharge_Air_Temperature_Sensor' or a set of Haystack tags,
                    formatted as 'discharge-air-temp-sensor-point'
    :return:
    """
    valid_namespaced_terms = set()
    candidate_terms = set(terms.split("-"))
    for candidate in candidate_terms:
        ns = tg.get_namespaces_given_term(ontology, candidate)
        if len(ns) == 1:
            ns = ns[0]
            valid_namespaced_terms.add((ns, candidate))
        elif len(ns) == 0:
            raise te.TermNotFoundError(f"Candidate '{candidate}' not found in any namespaces in the provided ontology")
        else:
            raise te.MultipleTermsFoundError(
                f"Candidate '{candidate}' found in multiple namespaces: {[x[0] for x in ns]}")
    return valid_namespaced_terms


def _haystack_get_entities_and_typing_properties(ontology: Graph, valid_namespaced_terms: Set[Tuple[Namespace, str]]) -> \
        Set[
            Tuple[Namespace, str]]:
    """
    Return all tags which subclass from an entity
    :param ontology:
    :param valid_namespaced_terms:
    :return:
    """
    q = """SELECT ?e WHERE {?e rdfs:subClassOf* ph:entity}"""
    match = ontology.query(q)
    all_entities = [m[0] for m in match]
    valid_entities = set()
    typing_properties = set()
    for tag in valid_namespaced_terms:
        ns, t = tag
        if ns[t] in all_entities:
            valid_entities.add(tag)
        else:
            typing_properties.add(tag)
    return valid_entities, typing_properties


def _haystack_get_other_properties(ontology: Graph, properties: dict) -> dict:
    other_properties = {}
    for k, v in properties.items():
        ns_term = list(_get_namespaced_terms(ontology, k))
        ns_term = ns_term[0]
        print(ns_term)
        other_properties[ns_term] = v
    return other_properties
