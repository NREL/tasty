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
    # TODO: consider renaming - maybe this isn't as similar to a Template as the others
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


class BaseTemplate:
    def __init__(self, template: dict):
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

    def validate_template_against_schema(self,
                                         schema_path=os.path.join(tc.SCHEMAS_DIR, 'template.schema.json')) -> None:
        """
        Validate self._template (dict) against the JSON schema.
        :param schema_path: [str] full/path/to/schema.json
        :return:
        """
        self.template_schema = load_template_schema(path_to_file=schema_path)
        self.is_valid, self.validation_error = validate_template_against_schema(self._template,
                                                                                self.template_schema)
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
        else:
            print(
                "[tasty.templates.BaseTemplate] Template is not valid. Template basics not populated, nor is template registered to all_templates.")


class EquipmentTemplate(BaseTemplate):
    """
    Template for a piece of equipment based on a class definition from Project Haystack or Brick Schema.
    The 'base class' is defined by the 'extends' key in the template.  This must resolve to:
    - Haystack: rdfs:subClassOf* phIoT:equip
    - Brick: rdfs:subClassOf* brick:Equipment
    The Equipment template defines expected telemetry point types to associate with it, either through:
        - a PointGroupTemplate symbol (i.e. SD).
        - a telemetry_point_type definition (i.e. SD).
    """
    all_templates = set()

    def __init__(self, template: dict):
        super().__init__(template)
        self._extends: str = None
        self.extends: Tuple[Namespace, str] = None
        self.point_group_templates: Set[PointGroupTemplate] = set()
        self.telemetry_point_entities: Set[EntityTemplate] = set()
        if bool(self._template):
            self.validate_template_against_schema()

    @classmethod
    def register_template(cls, template):
        """
        Register the template to make it available externally.
        :param template: [EquipmentTemplate]
        :return:
        """
        if isinstance(template, EquipmentTemplate):
            cls.all_templates.add(template)
        else:
            raise te.TemplateRegistrationError(
                f"Can only register an EquipmentTemplate.  Attempted to register a {type(template)}")

    def resolve_extends(self) -> None:
        """
        Resolve the value of 'extends' to a valid equipment class.
        Sets self.extends = (Namespace, term) when found.
        :return:
        """
        if 'extends' not in self._template.keys():
            self.is_valid = False
            raise te.TemplateValidationError(f"Equipment Template with ID: {self._id} must define an 'extends' key.")
        else:
            self._extends = self._template['extends']
            ont = tg.load_ontology(self._schema_name, self._schema_version)
            ns_terms = get_namespaced_terms(ont, self._extends)
            if self._schema_name == 'Haystack':
                structured_terms = hget_entity_classes(ont, ns_terms)
                classes = structured_terms['classes']
                if len(classes) != 1:
                    raise te.MultipleTermsFoundError(
                        "Equipment definitions should only extend a single Haystack class"
                    )
                equipment_class = list(classes)[0]
                q = """SELECT ?e WHERE {{ ?e rdfs:subClassOf* phIoT:equip }}"""
            elif self._schema_name == 'Brick':
                if len(ns_terms) != 1:
                    raise te.MultipleTermsFoundError(
                        "Equipment definitions should only extend a single Brick class"
                    )
                equipment_class = list(ns_terms)[0]
                q = """SELECT ?e WHERE {{ ?e rdfs:subClassOf* brick:Equipment }}"""
            match = ont.query(q)
            equip_subclasses = [m[0] for m in match]
            ns, t = equipment_class
            if ns[t] not in equip_subclasses:
                raise te.TemplateValidationError(
                    f"Equipment Template with ID: {self._id} cannot extend {self._extends}. It does not match based on the query: {q}")
            else:
                self.extends = equipment_class

    # def resolve_telemetry_point_types(self):
    #     available_pgts = PointGroupTemplate.


class PointGroupTemplate(BaseTemplate):
    all_templates = set()  # type: set

    # TODO:
    #   1. Add methodology to determine if 2 PGT's are similar / equivalent
    #   Class Methods:
    #       2. find_with_entities(Set(EntityTemplates)) -> return PGTs
    #       3. find_with_symbol(symbol) -> return PGTs
    def __init__(self, template: dict):
        """
        Initialize a new PointGroupTemplate
        :param template: [dict] See the template.schema.json for expected keys.
        """
        super().__init__(template)
        self.telemetry_point_entities: Set[EntityTemplate] = set()
        if bool(self._template):
            self.validate_template_against_schema()

    @classmethod
    def register_template(cls, template) -> None:
        """
        Register the template to make it available externally.
        :param template: [PointGroupTemplate]
        :return:
        """
        if isinstance(template, PointGroupTemplate):
            cls.all_templates.add(template)
        else:
            raise te.TemplateRegistrationError(
                f"Can only register a PointGroupTemplate.  Attempted to register a {type(template)}")

    @classmethod
    def find_given_symbol_schema_version(cls, symbol, schema_version, schema_name):
        """
        Find all PointGroupTemplates with the given characteristics.
        This should *hopefully* resolve to just 1, although not guaranteed.
        TODO: decide if a unique combination of [symbol, schema_version, schema_name] should
            occur only once.  Initial thought is YES.
        :param symbol: [str]
        :param schema_version: [str]
        :param schema_name: [str]
        :return: [List[PointGroupTemplate]]
        """
        found_templates = []
        for pgt in cls.all_templates:
            if pgt._symbol == symbol and pgt._schema_version == schema_version and pgt._schema_name == schema_name:
                found_templates.append(pgt)
        return found_templates

    @classmethod
    def find_given_symbol(cls, symbol):
        """
        Find all PointGroupTemplates with the given symbol.
        This will likely return multiple, as symbols themselves may only be unique
        in the context of a given [symbol, schema, version] set
        :param symbol: [str]
        :return: [List[PointGroupTemplate]]
        """
        found_templates = []
        for pgt in cls.all_templates:
            if pgt._symbol == symbol:
                found_templates.append(pgt)
        return found_templates

    def populate_template_basics(self) -> None:
        """
        See BaseTemplate.populate_template_basics
        Registers the Class if valid.
        :return:
        """
        super().populate_template_basics()
        if self.is_valid:
            self.register_template(self)

    def resolve_telemetry_point_types(self) -> None:
        """
        Wrapper around: resolve_telemetry_points_to_entity_templates.
        Uses keys found in the template to run.
        :return:
        """
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
            print("[tasty.templates.PointGroupTemplate] Template is not valid. Will not be written to disk.")

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
            print("[tasty.templates.PointGroupTemplate] Template is not valid. Will not be pickled.")


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
    for typing_metadata, properties in telemetry_point_types.items():
        ns_terms = get_namespaced_terms(ont, typing_metadata)
        ns_fields = get_namespaced_terms(ont, properties)
        if schema_name == 'Haystack':
            structured_terms = hget_entity_classes(ont, ns_terms)
            if len(structured_terms['fields']) > 0:
                print(
                    f"[tasty.templates.resolve_telemetry_point_to_entity_templates] The following fields were found but will not be used: {structured_terms['fields']}.")
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
    """
    Run after tg.get_namespaces_given_term to validate only a single ns was found
    :param ns: [List[Namespace]]
    :param candidate: [str]
    :return:
    """
    if len(ns) == 1:
        return True
    elif len(ns) == 0:
        raise te.TermNotFoundError(
            f"Candidate '{candidate}' not found in any namespaces in the provided ontology")
    else:
        raise te.MultipleTermsFoundError(
            f"Candidate '{candidate}' found in multiple namespaces: {[x[0] for x in ns]}")


def hget_entity_classes(ontology, candidates):
    """
    Given a 'string-of-haystack-tags', determine valid classes, markers, and fields.  See return.
    :param ontology: [Graph] a loaded ontology
    :param candidates: [str] a '-' delimited string, where each term is a haystack concept to figure out
    :return: [dict[str, Set]] The returned dict has structure as follows:
        {
            A set of namespaced valid entity classes
            'classes': {(Namespace, term), (Namespace, term) ...},

            A set of namespaced valid markers NOT used in entity class typing.  These must subClass* from ph:marker
            'markers': {(Namespace, term), ...}

            A set of namespaced fields.  These are terms that are NOT markers, but are Datatype Properties.
            The third term in the tuple always specifies a 'val' of None (i.e. just expect the property to be defined)
            'fields': {(Namespace, term, frozendict({'val': None})), ...}
        }
    """
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
    for n in range(1, len(candidates) + 1):
        perm = list(permutations(only_terms, n))
        for p in perm:
            new_candidate = '-'.join(p)
            for ns in namespaces:
                if ns[new_candidate] in current_subclasses:
                    classes.add((ns, new_candidate))
                    for each_term_used in p:
                        added_candidates.add(each_term_used)
    total_time = time.time() - st
    print(f"[tasty.templates.hget_entity_classes] Permutation time: {total_time:.2f} seconds")
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
    """
    Return the prefix for the term given namespaces in the ontology.
    :param namespaces: [List[Namespace]]
    :param term: [str] term
    :return: [str] if found, the prefix
    :return: [None] if not found
    """
    ns, t = term
    for namespace in namespaces:
        prefix, uri = namespace
        if uri.encode() == ns.encode():
            return prefix
    return None
