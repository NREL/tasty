import os
from itertools import permutations
from copy import deepcopy
import uuid

from typing import List, Set, Tuple
from frozendict import frozendict
import yaml
import json
import jsonschema
from jsonschema import validate
from rdflib import Graph, Namespace, RDF, OWL, RDFS, SKOS, SH, XMLNS, XSD
import time

import tasty.graphs as tg
import tasty.constants as tc
import tasty.exceptions as te


# TODO: consider renaming - maybe this isn't as similar to a Template as the others
class EntityTemplate:
    instances = set()  # type: Set[EntityTemplate]

    # TODO: maybe there is a better way to do this with __hash__?
    def __new__(cls, entity_classes, schema_name, schema_version, typing_properties, properties):
        """
        We only create a new object if an 'equivalent' object doesn't already exist.
        If the equivalent object does exist, we return that instead.
        :param entity_classes:
        :param typing_properties:
        :param properties:
        :param schema_name:
        :param schema_version:
        :return: [EntityTemplate]
        """
        equivalent = cls.get_equivalent(entity_classes, schema_name, schema_version, typing_properties, properties)
        if equivalent:
            print(f"{__name__}.{__class__.__name__} Equivalent EntityTemplate already exists and was returned.")
            return equivalent
        else:
            return super().__new__(cls)

    def __init__(self, entity_classes: Set[Tuple[Namespace, str]], schema_name: str, schema_version: str,
                 typing_properties: Set,
                 properties: Set[Tuple[Namespace, str, dict]]):
        self.entity_classes = entity_classes
        self.schema_name = schema_name
        self.schema_version = schema_version
        self.typing_properties = typing_properties
        self.properties = properties
        self.is_valid = False
        self.validate_data()
        if self.is_valid:
            print(f"{__name__}.{__class__.__name__} created and is valid: {self.schema_name}, {self.schema_version}, {self.get_simple_classes()}")
            self.register_template(self)

    @classmethod
    def get_equivalent(cls, entity_classes: Set, schema_name: str, schema_version: str, typing_properties: Set,
                       properties: Set[Tuple[Namespace, str, dict]]):
        has_equivalent = False
        for et in cls.instances:
            if (
                    et.entity_classes == entity_classes
                    and et.typing_properties == typing_properties
                    and et.properties == properties
                    and et.schema_name == schema_name
                    and et.schema_version == schema_version
            ):
                has_equivalent = et
        return has_equivalent

    @classmethod
    def register_template(cls, template):
        """
        Add the template to the set of templates available
        :param template: [EntityTemplate] the EntityTemplate to register
        :return:
        """
        cls.instances.add(template)

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
        for template in cls.instances:
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
        for template in cls.instances:
            if namespaced_classes <= template.entity_classes:
                templates.add(template)
        return list(templates)

    def validate_data(self):
        # Check entity_classes
        if not isinstance(self.entity_classes, set) or len(self.entity_classes) == 0:
            raise ValueError("entity_classes must be a set and have atleast one item.")
        elif len(self.entity_classes) > 0:
            for ec in self.entity_classes:
                if not isinstance(ec, Tuple):
                    raise ValueError("each element in entity_classes must be a Tuple")
                elif not len(ec) == 2:
                    raise ValueError("each Tuple in entity_classes must have 2 elements")
                elif not isinstance(ec[0], Namespace) or not isinstance(ec[1], str):
                    raise ValueError("each element in entity_classes must contain a (Namespace, str) tuple")

        # Check schema_name
        if not isinstance(self.schema_name, str):
            raise ValueError("schema_name must be a string")
        elif not bool(self.schema_name):
            raise ValueError("schema_name must be non-empty")

        # Check schema_version
        if not isinstance(self.schema_version, str):
            raise ValueError("schema_version must be a string")
        elif not bool(self.schema_version):
            raise ValueError("schema_version must be non-empty")

        self.is_valid = True

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

    def get_simple_properties(self) -> dict:
        """
        Get other_properties as hash map of keys, values, no namespaces
        :return: [dict]
        """
        properties = {}
        for field in self.properties:
            ns, term, meta = field
            properties[term] = {}
            for k, v in meta.items():
                # if tuple, the first item is the Namespace,
                # the second item is the term of interest
                # i.e. (Namespace(https://...), 'number')
                if isinstance(v, Tuple):
                    properties[term][k] = v[1]
                else:
                    properties[term][k] = v
        return properties

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
        for field in self.properties:
            ns, term, meta = field
            all_ns.add(ns)
            for k, v in meta.items():
                if isinstance(v, Tuple):
                    all_ns.add(v[0])
        return all_ns


class BaseTemplate:
    _instance_ids = set()

    def __new__(cls, **kwargs):
        if 'id' in kwargs:
            template_id = kwargs['id']
            # Throws ValueError if not valid UUID
            uid = uuid.UUID(str(template_id))
            if not uid.version == 4:
                raise te.TastyError(
                    f"{__name__}.{__class__.__name__} ID must be valid UUID4, got: {template_id} - version: {uid.version}")
            if template_id in cls._instance_ids:
                raise te.TastyError(f"{__name__}.{__class__.__name__} with ID: {template_id} already exists.")
            else:
                cls._instance_ids.add(template_id)
                return super().__new__(cls)
        else:
            raise te.TastyError(f"{__name__}.{__class__.__name__} must have an ID")

    def __init__(self, **kwargs):
        # Required kwargs
        self._template = kwargs
        self._id: str = None
        self._symbol: str = None
        self._template_type: str = None
        self._schema_name: str = None
        self._schema_version: str = None

        # Not required kwargs
        self._description: str = None
        self._telemetry_points: dict = {}

        # Others
        self.template_schema: dict = None
        self.is_valid: bool = False
        self.validation_error: str = None

    @staticmethod
    def has_minimum_keys(template):
        required = set(['id', 'symbol', 'template_type', 'schema_name', 'version'])
        if required <= set(template.keys()):
            return True
        else:
            return False

    def validate_template_against_schema(self,
                                         schema_path=os.path.join(tc.SCHEMAS_DIR, 'template.schema.json'),
                                         template_type=None) -> None:
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
        else:
            if self._template['template_type'] != template_type:
                raise te.TemplateValidationError(
                    f"template_type must be: {template_type}"
                )

    def populate_template_basics(self) -> None:
        """
        Only populate template if valid
        :return:
        """
        if self.is_valid:
            self._id = self._template['id']  # str
            self._symbol = self._template['symbol']  # str
            self._template_type = self._template['template_type']  # str
            self._schema_name = self._template['schema_name']  # str
            self._schema_version = self._template['version']  # str

            # Not required
            self._description = self._template.get('description', '')  # str
            self._telemetry_points = self._template.get('telemetry_point_types', {})  # dict (yaml object)
        else:
            print(
                "[tasty.templates.BaseTemplate] Template is not valid. Template basics not populated, nor is template registered to instances.")


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
    instances = set()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extends: str = None
        self.extends: Tuple[Namespace, str] = None
        self.fully_resolved = False
        self.point_group_templates: Set[PointGroupTemplate] = set()
        self.telemetry_point_entity_templates: Set[EntityTemplate] = set()
        if self.has_minimum_keys(self._template):
            self.validate_template_against_schema(template_type='equipment-template')

    @classmethod
    def register_template(cls, template):
        """
        Register the template to make it available externally.
        :param template: [EquipmentTemplate]
        :return:
        """
        if isinstance(template, EquipmentTemplate):
            cls.instances.add(template)
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

    def resolve_telemetry_point_types(self):
        ont = tg.load_ontology(self._schema_name, self._schema_version)
        for point_type_or_symbol, data in self._telemetry_points.items():
            if isinstance(data, type(None)):
                available_pgts = PointGroupTemplate.find_given_symbol_schema_version(point_type_or_symbol,
                                                                                     self._schema_name,
                                                                                     self._schema_version)
                if len(available_pgts) == 0:
                    print(
                        f"[tasty.templates.EquipmentTemplate] No PointGroupTemplate found for {self._schema_name}, {self._schema_version}, {point_type_or_symbol}. Make sure PGTs have been loaded")
                elif len(available_pgts) > 1:
                    te.TastyError(
                        f"""Multiple PointGroupTemplates with: symbol ({point_type_or_symbol}),
                        schema: ({self._schema_name}), version: ({self._schema_version}) found.
                        Unable to resolve for EquipmentTemplate ID: {self._id}
                        """
                    )
                else:
                    pgt = available_pgts[0]
                    print(f"[tasty.templates.EquipmentTemplate] Found PointGroupTemplate with id: {pgt._id}")
                    self.point_group_templates.add(pgt)
            elif isinstance(data, dict):
                et = resolve_to_entity_template(ont, point_type_or_symbol, data, self._schema_name,
                                                self._schema_version)
                if et:
                    self.telemetry_point_entity_templates.add(et)
        total_to_resolve = len(self.telemetry_point_entity_templates) + len(self.point_group_templates)
        if total_to_resolve == len(self._telemetry_points):
            print(f"[tasty.templates.EquipmentTemplate] Fully Resolved")
            self.fully_resolved = True

    def get_all_points_as_entity_templates(self) -> Set[EntityTemplate]:
        to_return = set()
        for pgt in self.point_group_templates:
            for et in pgt.telemetry_point_entity_templates:
                to_return.add(et)
        for et in self.telemetry_point_entity_templates:
            to_return.add(et)
        return to_return


class PointGroupTemplate(BaseTemplate):
    instances = set()  # type: Set[PointGroupTemplate]

    # TODO:
    #   1. Add methodology to determine if 2 PGT's are similar / equivalent
    #   Class Methods:
    #       2. find_with_entities(Set(EntityTemplates)) -> return PGTs
    #       ~~3. find_with_symbol(symbol) -> return PGTs~~

    def __init__(self, **kwargs):
        """
        Initialize a new PointGroupTemplate
        :param template: [dict] See the template.schema.json for expected keys.
        """
        super().__init__(**kwargs)
        self.telemetry_point_entity_templates: Set[EntityTemplate] = set()
        if self.has_minimum_keys(self._template):
            self.validate_template_against_schema(template_type='point-group-template')

    @classmethod
    def register_template(cls, template) -> None:
        """
        Register the template to make it available externally.
        :param template: [PointGroupTemplate]
        :return:
        """
        if isinstance(template, PointGroupTemplate):
            cls.instances.add(template)
        else:
            raise te.TemplateRegistrationError(
                f"Can only register a PointGroupTemplate.  Attempted to register a {type(template)}")

    @classmethod
    def find_given_symbol_schema_version(cls, symbol, schema_name, schema_version):
        """
        Find all PointGroupTemplates with the given characteristics.
        This should *hopefully* resolve to just 1, although not guaranteed.
        TODO: decide if a unique combination of [symbol, schema_version, schema_name] should
            occur only once.  Initial thought is YES.
        :param symbol: [str]
        :param schema_name: [str]
        :param schema_version: [str]
        :return: [List[PointGroupTemplate]]
        """
        found_templates = []
        for pgt in cls.instances:
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
        for pgt in cls.instances:
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
        self.telemetry_point_entity_templates = resolve_telemetry_points_to_entity_templates(self._telemetry_points,
                                                                                             self._schema_name,
                                                                                             self._schema_version)

    def add_telemetry_point_to_template(self, entity_template: EntityTemplate) -> None:
        """
        Update the set of telemetry_point_entity_templates with a new EntityTemplate
        :param entity_template: [EntityTemplate] a new entity to add to this point group
        :return:
        """
        if isinstance(entity_template, EntityTemplate):
            self.telemetry_point_entity_templates.add(entity_template)

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
        et = resolve_to_entity_template(ont, typing_metadata, properties, schema_name, version)
        if et:
            entity_templates.add(et)
    return set(entity_templates)


def resolve_to_entity_template(ont, typing_metadata, properties, schema_name, version):
    et = False
    ns_terms = get_namespaced_terms(ont, typing_metadata)
    ns_properties = get_namespaced_terms(ont, properties)
    if schema_name == 'Haystack':
        structured_terms = hget_entity_classes(ont, ns_terms)
        if len(structured_terms['properties']) > 0:
            print(
                f"[tasty.templates.resolve_to_entity_template] The following properties were found but will not be used: {structured_terms['properties']}.")
        et = EntityTemplate(structured_terms['classes'], schema_name, version, structured_terms['markers'], ns_properties)
    elif schema_name == 'Brick':
        et = EntityTemplate(ns_terms, schema_name, version, set(), ns_properties)
    return et


def get_namespaced_terms(ontology: Graph, terms: [str, dict]) -> Set:
    """
    TODO: document function
    :param ontology: [Graph] A loaded ontology
    :param terms: [str] A Brick class, such as 'Discharge_Air_Temperature_Sensor' a set of Haystack tags,
                    such as 'discharge-air-temp-sensor-point', or a dict of properties, such as:
                    {field1: {_kind: number}, field2: {val: cfm}}
    :return:
    """
    valid_namespaced_terms = set()
    if isinstance(terms, str):
        candidate_terms = set(terms.split("-"))
        for candidate in candidate_terms:
            ns = tg.get_namespaces_given_term(ontology, candidate)
            if tg.has_one_namespace(ns):
                valid_namespaced_terms.add((ns[0], candidate))
            else:
                return False
    elif isinstance(terms, dict):
        for candidate, meta in terms.items():
            candidate_ns = tg.get_namespaces_given_term(ontology, candidate)
            if tg.has_one_namespace(candidate_ns):
                # Create a deepcopy so as to not impact original template
                meta_copy = deepcopy(meta)
                if isinstance(meta, dict) and '_kind' in meta.keys():
                    meta_ns = tg.get_namespaces_given_term(ontology, meta_copy['_kind'])
                    if tg.has_one_namespace(meta_ns):
                        meta_copy['_kind'] = (meta_ns[0], meta['_kind'])
                        valid_namespaced_terms.add((candidate_ns[0], candidate, frozendict(meta_copy)))
                    else:
                        return False
                elif isinstance(meta, (int, float, bool, str)):
                    valid_namespaced_terms.add((candidate_ns[0], candidate, frozendict({'val': meta})))

    return valid_namespaced_terms


def hget_entity_classes(ontology, candidates):
    """
    Given a 'string-of-haystack-tags', determine valid classes, markers, and properties.  See return.
    :param ontology: [Graph] a loaded ontology
    :param candidates: [str] a '-' delimited string, where each term is a haystack concept to figure out
    :return: [dict[str, Set]] The returned dict has structure as follows:
        {
            A set of namespaced valid entity classes
            'classes': {(Namespace, term), (Namespace, term) ...},

            A set of namespaced valid markers NOT used in entity class typing.  These must subClass* from ph:marker
            'markers': {(Namespace, term), ...}

            A set of namespaced properties.  These are terms that are NOT markers, but are Datatype Properties.
            The third term in the tuple always specifies a 'val' of None (i.e. just expect the property to be defined)
            'properties': {(Namespace, term, frozendict({'val': None})), ...}
        }
    """
    # Begin by finding entity subclasses
    q = f"SELECT ?e WHERE {{ ?e rdfs:subClassOf* ph:entity }}"
    match = ontology.query(q)
    current_subclasses = [m[0] for m in match]
    dont_search = [RDF, OWL, RDFS, SKOS, SH, XMLNS, XSD]
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
    properties = set()
    for tag in not_class_candidates:
        ns, t = tag
        if ns[t] in markers:
            present_markers.add(tag)
        else:
            properties.add((ns, t, frozendict({'val': None})))

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
        'properties': properties
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
