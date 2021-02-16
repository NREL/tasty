import os

import pytest
from rdflib import Namespace, Literal
from pyshacl import validate

from tasty import constants as tc
from tasty import graphs as tg
from tests.conftest import get_single_node_validation_query, assert_remove_markers, write_csv, \
    get_parent_node_validation_query, get_min_count_validation_query

SAMPLE = Namespace('urn:sample/')
EXAMPLE = Namespace('https://project-haystack.org/datashapes#')


class TestOccupancyModeBinary:

    def test_is_valid(self, get_occupancy_mode_data, get_occupancy_mode_shapes):
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

    @pytest.mark.parametrize('remove_markers', [
        ['occupied'],
        ['sp'],
        ['occupied', 'sp']
    ])
    def test_is_invalid(self, get_occupancy_mode_data, get_occupancy_mode_shapes, remove_markers):
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

        # -- Remove markers and run validation
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

        results_query = results_graph.query(get_single_node_validation_query())

        # -- Assert markers correctly removed
        assert_remove_markers(remove_markers, results_query, point)

        # Write output to CSV for human readability
        write_csv(results_query, output_file)


class TestOccupancyModeStandby:

    def test_is_valid(self, get_occupancy_mode_data, get_occupancy_mode_shapes):
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

    @pytest.mark.parametrize('remove_markers', [
        ['occ'],
        ['occ', 'sp']
    ])
    def test_is_invalid(self, get_occupancy_mode_data, get_occupancy_mode_shapes, remove_markers):
        # -- Setup
        data_graph = get_occupancy_mode_data
        shapes_graph = get_occupancy_mode_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup - we target AHU-01-Point-01
        point = SAMPLE['AHU-01-Point-01']
        shapes_graph.add((EXAMPLE.OccupancyModeStandby, tc.SH.targetNode, point))

        # -- Remove markers and run validation
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

        results_query = results_graph.query(get_single_node_validation_query())

        # -- Assert markers correctly removed
        assert_remove_markers(remove_markers, results_query, point)

        # Write output to CSV for human readability
        write_csv(results_query, output_file)


class TestAhuOccupancyShape:
    def test_is_valid(self, get_occupancy_mode_data, get_occupancy_mode_shapes):
        # -- Setup
        data_graph = get_occupancy_mode_data
        shapes_graph = get_occupancy_mode_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup - we target AHU-01
        shapes_graph.add((EXAMPLE.AhuOccupancyShape, tc.SH.targetNode, SAMPLE['AHU-01']))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms = result[0]

        # -- Assert conforms
        assert conforms

    # Remove 'point' tag from AHU-01-Point-01
    def test_invalid_child_point_shape(self, get_occupancy_mode_data, get_occupancy_mode_shapes):
        # -- Setup
        data_graph = get_occupancy_mode_data
        shapes_graph = get_occupancy_mode_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup - we target AHU-01
        equip = SAMPLE['AHU-01']
        shapes_graph.add((EXAMPLE.AhuOccupancyShape, tc.SH.targetNode, equip))

        # -- Setup - we remove a tag from
        point = SAMPLE['AHU-01-Point-01']
        data_graph.remove((point, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9['point']))
        conforms, results_graph, results = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)

        # -- Serialize results
        f = 'TestAhuOccupancyShape' + '_test_invalid_child_point_shape' + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        assert not conforms

        results_query = results_graph.query(get_parent_node_validation_query())

        assert len(list(results_query)) == 1
        assert (equip, tc.PHIOT_3_9_9['equipRef'], tc.SH.QualifiedMinCountConstraintComponent, EXAMPLE.OccupancyModeStandby) in results_query

        # Write output to CSV for human readability
        write_csv(results_query, output_file)

    # Remove 'point' tag from AHU-01-Point-01
    # Remove 'sp' tag from AHU-01-Point-02
    def test_multiple_invalid_child_point_shapes(self, get_occupancy_mode_data, get_occupancy_mode_shapes):
        # -- Setup
        data_graph = get_occupancy_mode_data
        shapes_graph = get_occupancy_mode_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup - we target AHU-01
        equip = SAMPLE['AHU-01']
        shapes_graph.add((EXAMPLE.AhuOccupancyShape, tc.SH.targetNode, equip))

        # -- Setup - we remove a tag
        # Triggers: OccupancyModeStandby
        point1 = SAMPLE['AHU-01-Point-01']
        data_graph.remove((point1, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9['point']))

        # -- Setup - we remove a tag
        # Triggers: OccupancyModeBinary
        point2 = SAMPLE['AHU-01-Point-02']
        data_graph.remove((point2, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9['sp']))

        conforms, results_graph, results = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)

        # -- Serialize results
        f = 'TestAhuOccupancyShape' + '_test_multiple_invalid_child_point_shapes' + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        assert not conforms

        results_query = results_graph.query(get_parent_node_validation_query())

        # -- Assert constraints fail as expected
        assert len(list(results_query)) == 2
        assert (equip, tc.PHIOT_3_9_9['equipRef'], tc.SH.QualifiedMinCountConstraintComponent, EXAMPLE.OccupancyModeStandby) in results_query
        assert (equip, tc.PHIOT_3_9_9['equipRef'], tc.SH.QualifiedMinCountConstraintComponent, EXAMPLE.OccupancyModeBinary) in results_query

        # Write output to CSV for human readability
        write_csv(results_query, output_file)

    # Add point (AHU-01-Point-03) conforming to the OccupancyModeBinary shape
    def test_multiple_valid_child_point_shapes(self, get_occupancy_mode_data, get_occupancy_mode_shapes):
        # -- Setup
        data_graph = get_occupancy_mode_data
        shapes_graph = get_occupancy_mode_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup - we target AHU-01
        equip = SAMPLE['AHU-01']
        shapes_graph.add((EXAMPLE.AhuOccupancyShape, tc.SH.targetNode, equip))

        # -- Setup - create new point conforming to OccupancyModeBinary
        point = SAMPLE['AHU-01-Point-03']
        data_graph.add((point, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9.point))
        data_graph.add((point, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9.occupied))
        data_graph.add((point, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9.sp))
        data_graph.add((point, tc.PHIOT_3_9_9.equipRef, equip))

        conforms, results_graph, results = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)

        # -- Serialize results
        f = 'TestAhuOccupancyShape' + '_test_multiple_valid_child_point_shapes' + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        assert not conforms

        results_query = results_graph.query(get_parent_node_validation_query())

        # -- Assert constraints fail as expected
        assert len(list(results_query)) == 1
        assert (equip, tc.PHIOT_3_9_9['equipRef'], tc.SH.QualifiedMaxCountConstraintComponent, EXAMPLE.OccupancyModeBinary) in results_query

        # Write output to CSV for human readability
        write_csv(results_query, output_file)

    # Add point (AHU-01-Point-03) conforming to the OccupancyModeBinary shape
    def test_disjoint_shapes_requirement(self, get_occupancy_mode_data, get_occupancy_mode_shapes):
        # -- Setup
        data_graph = get_occupancy_mode_data
        shapes_graph = get_occupancy_mode_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup - we target AHU-01
        equip = SAMPLE['AHU-01']
        shapes_graph.add((EXAMPLE.AhuOccupancyShape, tc.SH.targetNode, equip))

        # -- Setup - remove the AHU-01-Point-02
        point = SAMPLE['AHU-01-Point-02']
        data_graph.remove((point, tc.RDF.type, tc.PHIOT_3_9_9.point))
        data_graph.remove((point, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9.point))
        data_graph.remove((point, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9.occupied))
        data_graph.remove((point, tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9.sp))
        data_graph.remove((point, tc.PHIOT_3_9_9.equipRef, equip))

        # -- Setup - add the occupied tag to AHU-01-Point-02
        data_graph.add((SAMPLE['AHU-01-Point-01'], tc.PH_3_9_9.hasTag, tc.PHIOT_3_9_9.occupied))

        print(data_graph.serialize(format='turtle'))

        conforms, results_graph, results = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)

        # -- Serialize results
        f = 'TestAhuOccupancyShape' + '_test_disjoint_shapes_requirement' + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        assert not conforms

        results_query_shapes = results_graph.query(get_parent_node_validation_query())
        results_query_count = results_graph.query(get_min_count_validation_query())

        all_results = list(results_query_shapes) + list(results_query_count)

        # Write output to CSV for human readability
        write_csv(all_results, output_file)

        # -- Assert constraints fail as expected
        assert len(list(results_query_shapes)) == 2
        assert (equip, tc.PHIOT_3_9_9['equipRef'], tc.SH.QualifiedMinCountConstraintComponent, EXAMPLE.OccupancyModeBinary) in results_query_shapes
        assert (equip, tc.PHIOT_3_9_9['equipRef'], tc.SH.QualifiedMinCountConstraintComponent, EXAMPLE.OccupancyModeStandby) in results_query_shapes

        # -- Assert constraints fail as expected
        assert len(list(results_query_count)) == 1
        assert (equip, tc.PHIOT_3_9_9['equipRef'], tc.SH.MinCountConstraintComponent, Literal("Less than 2 values on sample:AHU-01->[ sh:inversePath phIoT:equipRef ]")) in results_query_count
