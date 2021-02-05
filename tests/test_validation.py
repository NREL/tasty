import os
import csv

import pytest
from rdflib import Namespace
from pyshacl import validate

from tasty import constants as tc
from tasty import graphs as tg

SAMPLE = Namespace('urn:sample/')
EXAMPLE = Namespace('https://project-haystack.org/datashapes#')


def test_occupancy_mode_binary(get_occupancy_mode_data, get_occupancy_mode_shapes):
    # -- Setup
    data_graph = get_occupancy_mode_data
    shapes_graph = get_occupancy_mode_shapes
    ont_graph = tg.load_ontology('Haystack', '3.9.9')

    # -- Setup - we target AHU-01-Point-02
    shapes_graph.add((EXAMPLE.OccupancyModeBinary, tc.SH.targetNode, SAMPLE['AHU-01-Point-02']))

    result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
    conforms = result[0]

    # -- Assert conforms
    assert conforms


def test_occupancy_mode_standby(get_occupancy_mode_data, get_occupancy_mode_shapes):
    # -- Setup
    data_graph = get_occupancy_mode_data
    shapes_graph = get_occupancy_mode_shapes
    ont_graph = tg.load_ontology('Haystack', '3.9.9')

    # -- Setup - we target AHU-01-Point-01
    shapes_graph.add((EXAMPLE.OccupancyModeStandby, tc.SH.targetNode, SAMPLE['AHU-01-Point-01']))

    result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
    conforms = result[0]

    # -- Assert conforms
    assert conforms


def test_ahu_occupancy_shape(get_occupancy_mode_data, get_occupancy_mode_shapes):
    # -- Setup
    data_graph = get_occupancy_mode_data
    shapes_graph = get_occupancy_mode_shapes
    ont_graph = tg.load_ontology('Haystack', '3.9.9')

    # -- Setup - we target AHU-01
    shapes_graph.add((EXAMPLE.AhuOccupancyShape, tc.SH.targetNode, SAMPLE['AHU-01']))

    result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
    conforms = result[0]

    # -- Assert conforms
    assert conforms


@pytest.mark.parametrize('remove_markers', [
    ['occupied'],
    ['sp'],
    ['occupied', 'sp']
])
def test_invalid_occupancy_mode_binary(get_occupancy_mode_data, get_occupancy_mode_shapes, remove_markers):
    # -- Setup
    data_graph = get_occupancy_mode_data
    shapes_graph = get_occupancy_mode_shapes
    ont_graph = tg.load_ontology('Haystack', '3.9.9')
    validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
    if not os.path.isdir(validate_dir):
        os.mkdir(validate_dir)

    # -- Setup - we target AHU-01-Point-02
    point = SAMPLE['AHU-01-Point-02']
    shapes_graph.add((EXAMPLE.OccupancyModeBinary, tc.SH.targetNode, point))

    # -- Remove markers
    for marker in remove_markers:
        data_graph.remove((point, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9[marker]))
    result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
    conforms, results_graph, results = result

    # -- Serialize results
    f = '_'.join(remove_markers) + '_remove.ttl'
    output_file = os.path.join(validate_dir, f)
    results_graph.serialize(output_file, format='turtle')

    # -- Assert does not conform
    assert not conforms

    # -- This query returns us a triple that looks like:
    #    (focus_node, path, missing_value)
    q = ''' SELECT ?focus ?path ?val WHERE {
        ?vr a sh:ValidationReport .
        ?vr sh:result ?r .
        ?r sh:focusNode ?focus .
        ?r sh:resultPath ?path .
        ?r sh:sourceShape ?shape .
        ?shape sh:qualifiedValueShape ?vs .
        ?vs sh:hasValue ?val .
        }
    '''
    results_query = results_graph.query(q)
    print(f"Remove: {remove_markers}")
    for row in results_query:
        assert len(results_query) == len(remove_markers)
        for marker in remove_markers:
            # subject should always be the point
            assert row[0] == point
            # predicate should always be hasTag
            assert row[1] == tc.PH_3_9_9.hasTag
            # object should be the removed marker
            assert row[2] in [tc.PHIOT_3_9_9[m] for m in remove_markers]
    with open(output_file.replace('.ttl', '.csv'), 'w+') as f:
        writer = csv.writer(f)
        for row in results_query:
            writer.writerow(row)
