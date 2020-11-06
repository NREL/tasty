import os

from rdflib import Namespace

POINT_GROUP = 'point-group-template'
ENTITY_TYPE = 'entity-template'
SYSTEM_TYPE = 'system-template'

TEMPLATE_TYPES = (POINT_GROUP, ENTITY_TYPE, SYSTEM_TYPE)

OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
SH = Namespace(f"http://www.w3.org/ns/shacl#")

# Define versioned Brick Namespaces
BRICK_1_1 = Namespace("https://brickschema.org/schema/1.1/Brick#")
TAG_1_1 = Namespace("https://brickschema.org/schema/1.1/BrickTag#")
BSH_1_1 = Namespace("https://brickschema.org/schema/1.1/BrickShape#")

# Define versioned Haystack Namespaces
PH_3_9_9 = Namespace("https://project-haystack.org/def/ph/3.9.9#")
PHICT_3_9_9 = Namespace("https://project-haystack.org/def/phIct/3.9.9#")
PHSCIENCE_3_9_9 = Namespace("https://project-haystack.org/def/phScience/3.9.9#")
PHIOT_3_9_9 = Namespace("https://project-haystack.org/def/phIoT/3.9.9#")

SUPPORTED_SCHEMAS = {
    'Brick': ['1.1'],
    'Haystack': ['3.9.9']
}

SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schemas')
