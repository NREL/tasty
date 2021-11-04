import brickschema
from brickschema.merge import merge_type_cluster
from brickschema.namespaces import BRICK
from rdflib import Namespace

BLDG = Namespace("http://example.org/building/")

def validate(g):
    valid, _, report = g.validate()
    if not valid:
        raise Exception(report)

g1 = brickschema.Graph().load_file("../nrel/mediumOffice_brick.ttl")
#validate(g1)

g2 = brickschema.Graph().load_file("../pnnl/mediumOffice_brick.ttl")
#validate(g2)

G = merge_type_cluster(g1, g2, BLDG, similarity_threshold=0.1)
validate(G)
G.serialize("merged.ttl", format="ttl")
