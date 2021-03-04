import os

import pytest
from rdflib import Namespace
from pyshacl import validate

from tasty.generated import core_shapes
from tasty import constants as tc
from tasty import graphs as tg
from tasty import templates as tt
from tests.conftest import get_single_node_validation_query, assert_remove_markers, write_csv, \
    get_parent_node_validation_query, get_severity_query

SAMPLE = Namespace('urn:sample/')
PH_SHAPES = Namespace('https://project-haystack.org/datashapes/core#')


class TestIndividualShapes:
    @pytest.mark.parametrize('shape_name, target_node', [
        [PH_SHAPES['DamperPositionCommandShape'], SAMPLE['VAV-01-DamperPositionCommand']],
        [PH_SHAPES['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor']],
        [PH_SHAPES['ZoneAirTemperatureSensorShape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor']],
        [PH_SHAPES['ZoneAirTemperatureOverrideCommandShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand']],
        [PH_SHAPES['OccupancySensorShape'], SAMPLE['VAV-01-OccupancySensor']],
        [PH_SHAPES['WindowOverrideCommandShape'], SAMPLE['VAV-01-WindowOverrideCommand']],
        [PH_SHAPES['ZoneAirTemperatureOverrideSetpointShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint']],
        [PH_SHAPES['ZoneAirCO2SensorShape'], SAMPLE['VAV-01-ZoneAirCO2Sensor']],
        [PH_SHAPES['ZoneAirCO2SetpointShape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint']],
    ])
    def test_is_valid(self, get_g36_data, get_g36_shapes, shape_name, target_node):
        # -- Setup
        data_graph = get_g36_data
        shapes_graph = get_g36_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')

        # -- Setup
        shapes_graph.add((shape_name, tc.SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms = result[0]

        # -- Assert conforms
        assert conforms

    @pytest.mark.parametrize('shape_name, target_node, remove_markers', [
        [PH_SHAPES['DamperPositionCommandShape'], SAMPLE['VAV-01-DamperPositionCommand'], ['damper']],
        [PH_SHAPES['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor'], ['discharge']],
        [PH_SHAPES['ZoneAirTemperatureSensorShape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor'], ['zone']],
        [PH_SHAPES['ZoneAirTemperatureOverrideCommandShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand'],
         ['zone']],
        [PH_SHAPES['OccupancySensorShape'], SAMPLE['VAV-01-OccupancySensor'], ['occupied']],
        [PH_SHAPES['WindowOverrideCommandShape'], SAMPLE['VAV-01-WindowOverrideCommand'], ['cmd']],
        [PH_SHAPES['ZoneAirTemperatureOverrideSetpointShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint'],
         ['temp']],
        [PH_SHAPES['ZoneAirCO2SensorShape'], SAMPLE['VAV-01-ZoneAirCO2Sensor'], ['co2']],
        [PH_SHAPES['ZoneAirCO2SetpointShape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint'], ['co2', 'sp']],
    ])
    def test_is_invalid(self, get_g36_data, get_g36_shapes, shape_name, target_node, remove_markers):
        # -- Setup
        data_graph = get_g36_data
        shapes_graph = get_g36_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, tc.SH.targetNode, target_node))
        for marker in remove_markers:
            ns = tg.get_namespaces_given_term(ont_graph, marker)
            if tt.has_one_namespace(ns, marker):
                ns = ns[0]
                data_graph.remove((target_node, tc.PH_3_9_9.hasTag, ns[marker]))

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
        assert_remove_markers(remove_markers, results_query, target_node)

        # Write output to CSV for human readability
        write_csv(results_query, output_file)


class TestG36VavCoolingOnly:
    @pytest.mark.parametrize('shape_name, target_node', [
        [PH_SHAPES['G36-VavTerminalUnitCoolingOnlyShape'], SAMPLE['VAV-01']]
    ])
    def test_is_valid(self, get_g36_data, get_g36_shapes, shape_name, target_node):
        # -- Setup
        data_graph = get_g36_data
        shapes_graph = get_g36_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, tc.SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Serialize results
        f = 'TestG36VavCoolingOnly' + '_valid.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        assert conforms

    @pytest.mark.parametrize('shape_name, target_node, remove_from_node, remove_markers, severity', [
        [
            PH_SHAPES['G36-VavTerminalUnitCoolingOnlyShape'], SAMPLE['VAV-01'], SAMPLE['VAV-01-DamperPositionCommand'],
            ['damper'], tc.SH.Violation
        ],
        [
            PH_SHAPES['G36-VavTerminalUnitCoolingOnlyShape'], SAMPLE['VAV-01'],
            SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand'],
            ['zone'], tc.SH.Warning
        ]
    ])
    def test_is_invalid(self, get_g36_data, get_g36_shapes, shape_name, target_node, remove_from_node, remove_markers,
                        severity):
        # -- Setup
        data_graph = get_g36_data
        shapes_graph = get_g36_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, tc.SH.targetNode, target_node))
        for marker in remove_markers:
            ns = tg.get_namespaces_given_term(ont_graph, marker)
            if tt.has_one_namespace(ns, marker):
                ns = ns[0]
                data_graph.remove((remove_from_node, tc.PH_3_9_9.hasTag, ns[marker]))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Serialize results
        f = 'TestG36VavCoolingOnly_' + '_'.join(remove_markers) + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert does not conform
        assert not conforms

        results_query = results_graph.query(get_parent_node_validation_query())

        violation_level = results_graph.query(get_severity_query())

        assert len(list(violation_level)) == 1
        assert (target_node, severity) in violation_level

        # Write output to CSV for human readability
        write_csv(results_query, output_file)


class TestGeneratedShapes:
    @pytest.mark.parametrize('shape_name, target_node', [
        [PH_SHAPES['DamperPositionCommandShape'], SAMPLE['VAV-01-DamperPositionCommand']],
        [PH_SHAPES['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor']],
        [PH_SHAPES['ZoneAirTemperatureSensorShape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor']],
        [PH_SHAPES['ZoneAirTemperatureOverrideCommandShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand']],
        [PH_SHAPES['OccupancySensorShape'], SAMPLE['VAV-01-OccupancySensor']],
        [PH_SHAPES['WindowOverrideCommandShape'], SAMPLE['VAV-01-WindowOverrideCommand']],
        [PH_SHAPES['ZoneAirTemperatureOverrideSetpointShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint']],
        [PH_SHAPES['ZoneAirCO2SensorShape'], SAMPLE['VAV-01-ZoneAirCO2Sensor']],
        [PH_SHAPES['ZoneAirCO2SetpointShape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint']],
    ])
    def test_is_valid(self, get_g36_data, get_g36_shapes, shape_name, target_node):
        # -- Setup
        data_graph = get_g36_data
        shapes_graph = core_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')

        # -- Setup
        shapes_graph.add((shape_name, tc.SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Assert conforms
        if not conforms:
            print(results_graph.serialize(format='turtle').decode('utf-8'))
        assert conforms

    @pytest.mark.parametrize('shape_name, target_node, remove_markers', [
        [PH_SHAPES['DamperPositionCommandShape'], SAMPLE['VAV-01-DamperPositionCommand'], ['damper']],
        [PH_SHAPES['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor'], ['discharge']],
        [PH_SHAPES['ZoneAirTemperatureSensorShape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor'], ['zone']],
        [PH_SHAPES['ZoneAirTemperatureOverrideCommandShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand'],
         ['zone']],
        [PH_SHAPES['OccupancySensorShape'], SAMPLE['VAV-01-OccupancySensor'], ['occupied']],
        [PH_SHAPES['WindowOverrideCommandShape'], SAMPLE['VAV-01-WindowOverrideCommand'], ['cmd']],
        [PH_SHAPES['ZoneAirTemperatureOverrideSetpointShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint'],
         ['temp']],
        [PH_SHAPES['ZoneAirCO2SensorShape'], SAMPLE['VAV-01-ZoneAirCO2Sensor'], ['co2']],
        [PH_SHAPES['ZoneAirCO2SetpointShape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint'], ['co2', 'sp']],
    ])
    def test_is_invalid(self, get_g36_data, get_g36_shapes, shape_name, target_node, remove_markers):
        # -- Setup
        data_graph = get_g36_data
        shapes_graph = core_shapes
        ont_graph = tg.load_ontology('Haystack', '3.9.9')
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, tc.SH.targetNode, target_node))
        for marker in remove_markers:
            ns = tg.get_namespaces_given_term(ont_graph, marker)
            if tt.has_one_namespace(ns, marker):
                ns = ns[0]
                data_graph.remove((target_node, tc.PH_3_9_9.hasTag, ns[marker]))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Serialize results
        f = '_'.join(remove_markers) + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert does not conform
        if conforms:
            print(results_graph.serialize(format='turtle').decode('utf-8'))
        assert not conforms

        results_query = results_graph.query(get_single_node_validation_query())

        # -- Assert markers correctly removed
        assert_remove_markers(remove_markers, results_query, target_node)

        # Write output to CSV for human readability
        write_csv(results_query, output_file)
