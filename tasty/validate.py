import sys
import os

import rdflib
from rdflib import Graph, SH
from rdflib.util import guess_format
from pyshacl import validate
import pandas as pd

import tasty.constants as tc
import tasty.graphs as tg
from tasty.generated import core_shapes2

# Load in data graph
f = sys.argv[1]
data_graph = Graph()
data_graph.parse(f, format=guess_format(f))

shapes_graph = core_shapes2
tasty_dir = os.path.dirname(__file__)
csv_file = os.path.join(tasty_dir, '../input-file.csv')
data = pd.read_csv(csv_file, index_col='entity-id', true_values='X').fillna(value=False)
for entity_id, vals in data.iterrows():
    for shape_name, val in vals.iteritems():
        if val is True:
            if rdflib.term.URIRef(entity_id) not in data_graph.subjects():
                print(f"Entity does not exist: {entity_id}")
            else:
                print(f"Targeting entity {entity_id} with shape {shape_name}")
                shapes_graph.add((tc.PH_SHAPES[shape_name], SH.targetNode, rdflib.term.URIRef(entity_id)))

shapes_graph.serialize('shapes.ttl', format='turtle')
ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)

conforms, results_graph, results = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)

results_graph.serialize(f"results-{os.path.basename(f)}", format='turtle')
if not conforms:
    q_warn = '''SELECT ?fn ?bad_shape WHERE {
        ?n a sh:ValidationReport .
        ?n sh:result ?vr .
        ?vr sh:focusNode ?fn .
        ?vr sh:resultSeverity sh:Warning .
        ?vr sh:sourceShape ?shape .
        ?shape sh:qualifiedValueShape ?bad_shape .
    }'''
    q_error = '''SELECT ?fn ?bad_shape WHERE {
        ?n a sh:ValidationReport .
        ?n sh:result ?vr .
        ?vr sh:focusNode ?fn .
        ?vr sh:resultSeverity sh:Violation .
        ?vr sh:sourceShape ?shape .
        ?shape sh:qualifiedValueShape ?bad_shape .
    }'''
    warnings = results_graph.query(q_warn)
    errors = results_graph.query(q_error)
    print("-" * 100)
    print(f"Warnings: {len(warnings)}")
    for warning in warnings:
        print(f"Warning on entity: {warning[0]}, triggered by shape: {warning[1]}")
    print("-" * 100)
    print(f"Errors: {len(errors)}")
    for error in errors:
        print(f"Error on entity: {error[0]}, triggered by shape: {error[1]}")
    print("-" * 100)
