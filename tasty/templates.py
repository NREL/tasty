import os
from itertools import permutations
from copy import deepcopy
import pickle

from typing import List, Set, Tuple
from frozendict import frozendict
import yaml
import json
import jsonschema
from jsonschema import validate
from rdflib.namespace import Namespace
from rdflib import Graph
import time

import tasty.graphs as tg
import tasty.constants as tc
import tasty.exceptions as te


class EntityTemplate:
    all_templates = set()

    def __init__(self, entity_classes: Set, typing_properties: Set, fields: Set[Tuple[Namespace, str, dict]]):
        self.entity_classes = entity_classes
        self.typing_properties = typing_properties
        self.fields = fields
        self.register_template(self)

    @classmethod
    def register_template(cls, template):
        """
        Add the template to the set of templates available
        :param template: [EntityTemplate] the EntityTemplate to register
        :return:
        """
        cls.all_templates.add(template)

    @classmethod
    def find_with_class(cls, namespaced_class: Tuple[Namespace, str]):
        """
        Search all registered templates and return the objects with the
        class defined.
        :param namespaced_class: [Tuple[Namespace, str]] A 2-term tuple, where the str term represents the
         class to find, something like 'cur-point' or 'Discharge_Air_Flow_Sensor'
        :return: [List[EntityTemplate]] a list of EntityTemplate objects matching the description
        """
        templates = set()
        for template in cls.all_templates:
            for et in template.entity_classes:
                if et == namespaced_class:
                    templates.add(template)
        return list(templates)

    @classmethod
    def find_with_classes(cls, namespaced_classes: Set[Tuple[Namespace, str]]):
        """
        Search all registered templates and return the objects with atleast
        the classes defined.
            Example: namespaced_classes = {(NS1, cur-point), (NS1, his-point)}
            entity_classes1 = {(NS1, cur-point), (NS1, his-point), (NS1, writable-point)} -> would be added
            entity_classes2 = {(NS1, cur-point)} -> would not be added
        :param namespaced_classes: [Set[Tuple[Namespace, str]]] A set of 2-term tuples, where the str term represents the
         class to find, something like 'cur-point' or 'Discharge_Air_Flow_Sensor'
        :return: [List[EntityTemplate]] a list of EntityTemplate objects matching the description
        """
        templates = set()
        for template in cls.all_templates:
            if namespaced_classes <= template.entity_classes:
                templates.add(template)
        return list(templates)

    def get_simple_classes(self) -> Set[str]:
        """
        Just get terms, no namespaces
        :return: [Set[str]]
        """
        terms = set()
        for et in self.entity_classes:
            ns, term = et
            terms.add(term)
        return terms

    def get_simple_typing_info(self) -> Set[str]:
        """
        Get terms for the entity_class and typing_properties, no namespaces
        :return: [Set[str]]
        """
        terms = set()
        for et in self.entity_classes:
            ns, term = et
            terms.add(term)
        for tp in self.typing_properties:
            ns, term = tp
            terms.add(term)
        return terms

    def get_simple_fields(self) -> dict:
        """
        Get other_properties as hash map of keys, values, no namespaces
        :return: [dict]
        """
        fields = {}
        for field in self.fields:
            ns, term, meta = field
            fields[term] = {}
            for k, v in meta.items():
                # if tuple, the first item is the Namespace,
                # the second item is the term of interest
                # i.e. (Namespace(https://...), 'number')
                if isinstance(v, Tuple):
                    fields[term][k] = v[1]
                else:
                    fields[term][k] = v
        return fields

    def get_namespaces(self) -> Set[Namespace]:
        """
        Get all unique Namespaces for the entity template
        :return: [Set[Namespace]]
        """
        all_ns = set()
        for ec in self.entity_classes:
            ns, term = ec
            all_ns.add(ns)
        for tp in self.typing_properties:
            ns, term = tp
            all_ns.add(ns)
        for field in self.fields:
            ns, term, meta = field
            all_ns.add(ns)
            for k, v in meta.items():
                if isinstance(v, Tuple):
                    all_ns.add(v[0])
        return all_ns


class PointGroupTemplate:
    all_templates = set()

    # TODO:
    #   1. Add methodology to determine if 2 PGT's are similar / equivalent

    def __init__(self, template: dict):
        """
        Initialize a new PointGroupTemplate
        :param template: [dict] See the template.schema.json for expected keys.
        """
        self._template = template
        self._id: str = None
        self._symbol: str = None
        self._description: str = None
        self._schema_name: str = None
        self._schema_version: str = None
        self._telemetry_points: dict = None
        self.template_schema: dict = None
        self.is_valid: bool = False
        self.validation_error: str = None
        self.telemetry_point_entities: Set[EntityTemplate] = set()
        if bool(self._template):
            self.validate_template_against_schema()

    @classmethod
    def register_template(cls, template):
        cls.all_templates.add(template)

    def validate_template_against_schema(self,
                                         schema_path=os.path.join(tc.SCHEMAS_DIR, 'template.schema.json')) -> None:
        self.template_schema = load_template_schema(path_to_file=schema_path)
        self.is_valid, self.validation_error = validate_template_against_schema(self._template, self.template_schema)
        if not self.is_valid:
            raise te.TemplateValidationError(self.validation_error)

    def populate_template_basics(self) -> None:
        """
        Only populate template if valid
        :return:
        """
        if self.is_valid:
            self._id = self._template['id']  # str
            self._symbol = self._template['symbol']  # str
            self._description = self._template['description']  # str
            self._schema_name = self._template['schema_name']  # str
            self._schema_version = self._template['version']  # str
            self._telemetry_points = self._template['telemetry_point_types']  # dict (yaml object)
            self.register_template(self)
        else:
            print("Template is not valid. Template basics not populated, nor is template registered to all_templates.")

    def populate_telemetry_templates(self) -> None:
        self.telemetry_point_entities = resolve_telemetry_points_to_entity_templates(self._telemetry_points,
                                                                                     self._schema_name,
                                                                                     self._schema_version)

    def add_telemetry_point_to_template(self, entity_template: EntityTemplate) -> None:
        """
        Update the set of telemetry_point_entities with a new EntityTemplate
        :param entity_template: [EntityTemplate] a new entity to add to this point group
        :return:
        """
        if isinstance(entity_template, EntityTemplate):
            self.telemetry_point_entities.add(entity_template)

    def write(self, file_path: str) -> None:
        """
        Write the _template data to the file as yaml.
        :param file_path: [str] full/path/to/file.yaml
        :return:
        """
        if self.is_valid:
            if not os.path.isdir(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, 'w+') as f:
                yaml.dump(self._template, f)
        else:
            print("Template is not valid. Will not be written to disk.")

    def pickle(self, file_path: str) -> None:
        """
        Pickle the current template
        :param file_path: [str] full/path/to/file.yaml
        :return:
        """
        if self.is_valid:
            if not os.path.isdir(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, 'wb+') as f:
                pickle.dump(self, f)
        else:
            print("Template is not valid. Will not be pickled.")


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


def resolve_telemetry_points_to_entity_templates(telemetry_point_types: dict, schema_name: str, version: str) -> Set[
        EntityTemplate]:
    """
    Resolve each telemetry point (a key in the dict) to an EntityTemplate and return the set of created entity templates.
    Used in the PointGroupTemplate validator
    :param telemetry_point_types: [dict]
    :param schema_name: [str] One of the supported Schema names, see tasty/schemas/template.schema.json
    :param version:
    :return:
    """
    ont = tg.load_ontology(schema_name, version)
    entity_templates = set()
    print(telemetry_point_types)
    for typing_metadata, properties in telemetry_point_types.items():
        ns_terms = get_namespaced_terms(ont, typing_metadata)
        ns_fields = get_namespaced_terms(ont, properties)
        if schema_name == 'Haystack':
            structured_terms = hget_entity_classes(ont, ns_terms)
            if len(structured_terms['fields']) > 0:
                print(f"The following fields were found but will not be used: {structured_terms['fields']}.")
            et = EntityTemplate(structured_terms['classes'], structured_terms['markers'], ns_fields)
        elif schema_name == 'Brick':
            et = EntityTemplate(ns_terms, set(), ns_fields)
        entity_templates.add(et)

    return set(entity_templates)


def get_namespaced_terms(ontology: Graph, terms: [str, dict]) -> Set:
    """
    TODO: document function
    :param ontology: [Graph] A loaded ontology
    :param terms: [str] A Brick class, such as 'Discharge_Air_Temperature_Sensor' a set of Haystack tags,
                    such as 'discharge-air-temp-sensor-point', or a dict of fields, such as:
                    {field1: {_kind: number}, field2: {val: cfm}}
    :return:
    """
    valid_namespaced_terms = set()
    if isinstance(terms, str):
        candidate_terms = set(terms.split("-"))
        for candidate in candidate_terms:
            ns = tg.get_namespaces_given_term(ontology, candidate)
            if has_one_namespace(ns, candidate):
                valid_namespaced_terms.add((ns[0], candidate))
    elif isinstance(terms, dict):
        for candidate, meta in terms.items():
            candidate_ns = tg.get_namespaces_given_term(ontology, candidate)
            if has_one_namespace(candidate_ns, candidate):

                # Create a deepcopy so as to not impact original template
                meta_copy = deepcopy(meta)
                if isinstance(meta, dict) and '_kind' in meta.keys():
                    meta_ns = tg.get_namespaces_given_term(ontology, meta_copy['_kind'])
                    if has_one_namespace(meta_ns, meta['_kind']):
                        meta_copy['_kind'] = (meta_ns[0], meta['_kind'])
                        valid_namespaced_terms.add((candidate_ns[0], candidate, frozendict(meta_copy)))
                elif isinstance(meta, (int, float, bool, str)):
                    valid_namespaced_terms.add((candidate_ns[0], candidate, frozendict({'val': meta})))

    return valid_namespaced_terms


def has_one_namespace(ns, candidate):
    if len(ns) == 1:
        return True
    elif len(ns) == 0:
        raise te.TermNotFoundError(
            f"Candidate '{candidate}' not found in any namespaces in the provided ontology")
    else:
        raise te.MultipleTermsFoundError(
            f"Candidate '{candidate}' found in multiple namespaces: {[x[0] for x in ns]}")


def hget_entity_classes(ontology, candidates):
    # Begin by finding entity subclasses
    q = f"SELECT ?e WHERE {{ ?e rdfs:subClassOf* ph:entity }}"
    match = ontology.query(q)
    current_subclasses = [m[0] for m in match]
    dont_search = [tc.RDF, tc.OWL, tc.RDFS, tc.SKOS, tc.SH, tc.XML, tc.XMLS]
    namespaces = [Namespace(uri) for prefix, uri in ontology.namespaces() if Namespace(uri) not in dont_search]

    # The following creates permutations of all lengths
    # and finds all that are in current_subclasses.  It
    # tests it using each namespace found in the ontology
    # It is expensive but works.
    # namespaces = [a, b]
    # only_terms = [cur, point]
    #   a:cur subclass* of entity? False
    #   b:cur subclass* of entity? False
    #   a:point subclass* of entity? True
    #   a:cur-point subclass* of entity? True
    #   b:cur-point subclass* of entity? False
    #   ...
    classes = set()
    only_terms = set([t for ns, t in candidates])
    added_candidates = set()
    st = time.time()
    for n in range(1, len(candidates)):
        perm = permutations(only_terms, n)
        for p in list(perm):
            new_candidate = '-'.join(p)
            for ns in namespaces:
                if ns[new_candidate] in current_subclasses:
                    classes.add((ns, new_candidate))
                    for each_term_used in p:
                        added_candidates.add(each_term_used)
    total_time = time.time() - st
    print(f"Permutation time: {total_time:.2f} seconds")
    # This logic figures out which terms were not used in
    # the classes and separates those out.
    not_classes = only_terms - added_candidates
    not_class_candidates = set()
    for term in not_classes:
        for c in candidates:
            ns, t = c
            if term == t:
                not_class_candidates.add(c)
    # Finally, we ensure that all of these are still atleast 'typing'
    # properties and not expected to have literals or scalars
    q = f"SELECT ?e WHERE {{ ?e rdfs:subClassOf* ph:marker }}"
    match = ontology.query(q)
    markers = set([m[0] for m in match])
    present_markers = set()
    fields = set()
    for tag in not_class_candidates:
        ns, t = tag
        if ns[t] in markers:
            present_markers.add(tag)
        else:
            fields.add((ns, t, frozendict({'val': None})))

    # This logic determines which of the classes are subclasses of eachother
    # and only keeps the lowest subclass in each 'branch',
    # i.e. cur-point, writable-p)oint, point => keeps cur-point, writable-point
    to_remove = set()
    for c in classes:
        ns, t = c
        prefix = get_prefix(ontology.namespaces(), c)
        q = f"SELECT ?e WHERE {{ ?e rdfs:subClassOf* {prefix}:{t} }}"
        match = ontology.query(q)
        current_subclasses = set([m[0] for m in match])

        # Need to remove current class from subclasses
        current_subclasses.discard(ns[t])
        for c2 in classes:
            ns2, t2 = c2
            if ns2[t2] in current_subclasses:
                to_remove.add(c)
    classes = classes - to_remove
    structured = {
        'classes': classes,
        'markers': present_markers,
        'fields': fields
    }
    return structured


def get_prefix(namespaces, term):
    ns, t = term
    for namespace in namespaces:
        prefix, uri = namespace
        if uri.encode() == ns.encode():
            return prefix
    return None
