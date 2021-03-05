import os

from rdflib import Namespace

POINT_GROUP = 'point-group-template'
ENTITY_TYPE = 'entity-template'
SYSTEM_TYPE = 'system-template'

TEMPLATE_TYPES = (POINT_GROUP, ENTITY_TYPE, SYSTEM_TYPE)

# Haystack relevant constants
HAYSTACK = 'Haystack'
V3_9_9 = '3.9.9'
V3_9_10 = '3.9.10'

# Brick relevant constants
BRICK = 'Brick'
V1_1 = '1.1'

# Standard namespaces
XML = Namespace("http://www.w3.org/1998/namespace#")
XMLS = Namespace("http://www.w3.org/2001/XMLSchema#")

# Define versioned Brick Namespaces
BRICK_1_1 = Namespace("https://brickschema.org/schema/1.1/Brick#")
TAG_1_1 = Namespace("https://brickschema.org/schema/1.1/BrickTag#")
BSH_1_1 = Namespace("https://brickschema.org/schema/1.1/BrickShape#")

# Define versioned Haystack Namespaces
# 3.9.9
PH_3_9_9 = Namespace("https://project-haystack.org/def/ph/3.9.9#")
PHICT_3_9_9 = Namespace("https://project-haystack.org/def/phIct/3.9.9#")
PHSCIENCE_3_9_9 = Namespace("https://project-haystack.org/def/phScience/3.9.9#")
PHIOT_3_9_9 = Namespace("https://project-haystack.org/def/phIoT/3.9.9#")

# 3.9.10
PH_3_9_10 = Namespace("https://project-haystack.org/def/ph/3.9.10#")
PHICT_3_9_10 = Namespace("https://project-haystack.org/def/phIct/3.9.10#")
PHSCIENCE_3_9_10 = Namespace("https://project-haystack.org/def/phScience/3.9.10#")
PHIOT_3_9_10 = Namespace("https://project-haystack.org/def/phIoT/3.9.10#")

# Haystack Datashapes
PH_SHAPES = Namespace("https://project-haystack.org/datashapes/core#")
PH_CUSTOM = Namespace("https://project-haystack.org/def/custom#")

PH_DEFAULT = None
PHICT_DEFAULT = None
PHSCIENCE_DEFAULT = None
PHIOT_DEFAULT = None
BRICK_DEFAULT = None
TAG_DEFAULT = None
BSH_DEFAULT = None

SUPPORTED_SCHEMAS = {
    BRICK: [V1_1],
    HAYSTACK: [V3_9_9, V3_9_10]
}

SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schemas')


def set_default_versions(haystack_version=V3_9_10, brick_version=V1_1):
    global PH_DEFAULT, PHICT_DEFAULT, PHSCIENCE_DEFAULT, PHIOT_DEFAULT, BRICK_DEFAULT, TAG_DEFAULT, BSH_DEFAULT
    assert haystack_version in SUPPORTED_SCHEMAS[HAYSTACK], f"{haystack_version} must be one of {SUPPORTED_SCHEMAS[HAYSTACK]}"
    assert brick_version in SUPPORTED_SCHEMAS[BRICK], f"{brick_version} must be one of {SUPPORTED_SCHEMAS[BRICK]}"

    PH_DEFAULT = Namespace(f"https://project-haystack.org/def/ph/{haystack_version}#")
    PHICT_DEFAULT = Namespace(f"https://project-haystack.org/def/phIct/{haystack_version}#")
    PHSCIENCE_DEFAULT = Namespace(f"https://project-haystack.org/def/phScience/{haystack_version}#")
    PHIOT_DEFAULT = Namespace(f"https://project-haystack.org/def/phIoT/{haystack_version}#")

    if brick_version == V1_1:
        BRICK_DEFAULT = BRICK_1_1
        TAG_DEFAULT = TAG_1_1
        BSH_DEFAULT = BSH_1_1
    else:
        BRICK_DEFAULT = Namespace("https://brickschema.org/schema/Brick#")
        TAG_DEFAULT = Namespace("https://brickschema.org/schema/BrickTag#")
        BSH_DEFAULT = Namespace("https://brickschema.org/schema/BrickShape#")


set_default_versions()
