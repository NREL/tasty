import os

import pytest
from rdflib import Namespace, SH
from pyshacl import validate

import tasty.graphs
from tasty import constants as tc
from tasty import graphs as tg
from tests.conftest import get_single_node_validation_query, assert_remove_markers, write_csv, \
    get_parent_node_validation_query, get_severity_query, get_source_shape_query, run_another

SAMPLE = Namespace('urn:sample/')


class TestHandcraftedIndividualShapes:
    @pytest.mark.parametrize('shape_name, target_node', [
        [tc.PH_SHAPES_V1['DamperPositionCommandShape'], SAMPLE['VAV-01-DamperPositionCommand']],
        [tc.PH_SHAPES_V1['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureSensorShape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureOverrideCommandShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand']],
        [tc.PH_SHAPES_V1['OccupancySensorShape'], SAMPLE['VAV-01-OccupancySensor']],
        [tc.PH_SHAPES_V1['WindowOverrideCommandShape'], SAMPLE['VAV-01-WindowOverrideCommand']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureOverrideSetpointShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint']],
        [tc.PH_SHAPES_V1['ZoneAirCO2SensorShape'], SAMPLE['VAV-01-ZoneAirCO2Sensor']],
        [tc.PH_SHAPES_V1['ZoneAirCO2SetpointShape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint']],
    ])
    def test_is_valid(self, get_haystack_g36_data, get_haystack_g36_shapes, shape_name, target_node):
        # -- Setup
        data_graph = get_haystack_g36_data
        shapes_graph = get_haystack_g36_shapes
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms = result[0]

        # -- Assert conforms
        assert conforms

    @pytest.mark.parametrize('shape_name, target_node, remove_markers', [
        [tc.PH_SHAPES_V1['DamperPositionCommandShape'], SAMPLE['VAV-01-DamperPositionCommand'], ['damper']],
        [tc.PH_SHAPES_V1['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor'], ['discharge']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureSensorShape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor'], ['zone']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureOverrideCommandShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand'],
         ['zone']],
        [tc.PH_SHAPES_V1['OccupancySensorShape'], SAMPLE['VAV-01-OccupancySensor'], ['occupied']],
        [tc.PH_SHAPES_V1['WindowOverrideCommandShape'], SAMPLE['VAV-01-WindowOverrideCommand'], ['cmd']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureOverrideSetpointShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint'],
         ['temp']],
        [tc.PH_SHAPES_V1['ZoneAirCO2SensorShape'], SAMPLE['VAV-01-ZoneAirCO2Sensor'], ['co2']],
        [tc.PH_SHAPES_V1['ZoneAirCO2SetpointShape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint'], ['co2', 'sp']],
    ])
    def test_is_invalid(self, get_haystack_g36_data, get_haystack_g36_shapes, shape_name, target_node, remove_markers):
        # Set version for constants
        tc.set_default_versions(haystack_version=tc.V3_9_9)

        # -- Setup
        data_graph = get_haystack_g36_data
        shapes_graph = get_haystack_g36_shapes
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))
        for marker in remove_markers:
            ns = tg.get_namespaces_given_term(ont_graph, marker)
            if tasty.graphs.has_one_namespace(ns, marker):
                ns = ns[0]
                data_graph.remove((target_node, tc.PH_DEFAULT.hasTag, ns[marker]))

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
        assert_remove_markers(remove_markers, results_query, target_node, ont_graph)

        # Write output to CSV for human readability
        write_csv(results_query, output_file)


class TestHandcraftedG36VavCoolingOnly:
    @pytest.mark.parametrize('shape_name, target_node', [
        [tc.PH_SHAPES_V1['G36-VavTerminalUnitCoolingOnlyShape'], SAMPLE['VAV-01']]
    ])
    def test_is_valid(self, get_haystack_g36_data, get_haystack_g36_shapes, shape_name, target_node):
        # -- Setup
        data_graph = get_haystack_g36_data
        shapes_graph = get_haystack_g36_shapes
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))

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
            tc.PH_SHAPES_V1['G36-VavTerminalUnitCoolingOnlyShape'], SAMPLE['VAV-01'],
            SAMPLE['VAV-01-DamperPositionCommand'],
            ['damper'], SH.Violation
        ],
        [
            tc.PH_SHAPES_V1['G36-VavTerminalUnitCoolingOnlyShape'], SAMPLE['VAV-01'],
            SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand'],
            ['zone'], SH.Warning
        ]
    ])
    def test_is_invalid(self, get_haystack_g36_data, get_haystack_g36_shapes, shape_name, target_node, remove_from_node,
                        remove_markers,
                        severity):
        # Set version for constants
        tc.set_default_versions(haystack_version=tc.V3_9_9)

        # -- Setup
        data_graph = get_haystack_g36_data
        shapes_graph = get_haystack_g36_shapes
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))
        for marker in remove_markers:
            ns = tg.get_namespaces_given_term(ont_graph, marker)
            if tasty.graphs.has_one_namespace(ns, marker):
                ns = ns[0]
                data_graph.remove((remove_from_node, tc.PH_DEFAULT.hasTag, ns[marker]))

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


class TestGeneratedSinglePointShapesV1:
    @pytest.mark.parametrize('shape_name, target_node', [
        [tc.PH_SHAPES_V1['DamperPositionCommandShape'], SAMPLE['VAV-01-DamperPositionCommand']],
        [tc.PH_SHAPES_V1['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureSensorShape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureOverrideCommandShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand']],
        [tc.PH_SHAPES_V1['OccupancySensorShape'], SAMPLE['VAV-01-OccupancySensor']],
        [tc.PH_SHAPES_V1['WindowOverrideCommandShape'], SAMPLE['VAV-01-WindowOverrideCommand']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureOverrideSetpointShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint']],
        [tc.PH_SHAPES_V1['ZoneAirCO2SensorShape'], SAMPLE['VAV-01-ZoneAirCO2Sensor']],
        [tc.PH_SHAPES_V1['ZoneAirCO2SetpointShape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint']],
    ])
    def test_is_valid(self, get_haystack_g36_data, get_haystack_core_generated_shapes_v1, shape_name, target_node):
        # Set version for constants
        tc.set_default_versions(haystack_version=tc.V3_9_9)

        # -- Setup
        data_graph = get_haystack_g36_data
        shapes_graph = get_haystack_core_generated_shapes_v1
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Assert conforms
        if not conforms:
            print(results_graph.serialize(format='turtle').decode('utf-8'))
        assert conforms

    @pytest.mark.parametrize('shape_name, target_node, remove_markers', [
        [tc.PH_SHAPES_V1['DamperPositionCommandShape'], SAMPLE['VAV-01-DamperPositionCommand'], ['damper']],
        [tc.PH_SHAPES_V1['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor'], ['discharge']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureSensorShape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor'], ['zone']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureOverrideCommandShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand'],
         ['zone']],
        [tc.PH_SHAPES_V1['OccupancySensorShape'], SAMPLE['VAV-01-OccupancySensor'], ['occupied']],
        [tc.PH_SHAPES_V1['WindowOverrideCommandShape'], SAMPLE['VAV-01-WindowOverrideCommand'], ['cmd']],
        [tc.PH_SHAPES_V1['ZoneAirTemperatureOverrideSetpointShape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint'],
         ['temp']],
        [tc.PH_SHAPES_V1['ZoneAirCO2SensorShape'], SAMPLE['VAV-01-ZoneAirCO2Sensor'], ['co2']],
        [tc.PH_SHAPES_V1['ZoneAirCO2SetpointShape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint'], ['co2', 'sp']],
    ])
    def test_is_invalid(self, get_haystack_g36_data, get_haystack_core_generated_shapes_v1, shape_name, target_node,
                        remove_markers):
        # Set version for constants
        tc.set_default_versions(haystack_version=tc.V3_9_9)

        # -- Setup
        data_graph = get_haystack_g36_data
        shapes_graph = get_haystack_core_generated_shapes_v1
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))
        for marker in remove_markers:
            ns = tg.get_namespaced_term(ont_graph, marker)
            if ns:
                data_graph.remove((target_node, tc.PH_DEFAULT.hasTag, ns))

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
        assert_remove_markers(remove_markers, results_query, target_node, ont_graph)

        # Write output to CSV for human readability
        write_csv(results_query, output_file)


class TestGeneratedSinglePointShapesV2:
    @pytest.mark.parametrize('shape_name, target_node', [
        [tc.PH_SHAPES_V2['damper-cmd-shape'], SAMPLE['VAV-01-DamperPositionCommand']],

        # This isn't necessary since it is now not a shape but a strict type
        # [tc.PH_SHAPES_V2['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor']]

        [tc.PH_SHAPES_V2['zone-air-temp-sensor-shape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor']],
        [tc.PH_SHAPES_V2['zone-air-temp-override-cmd-shape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand']],
        [tc.PH_SHAPES_V2['occupancy-sensor-shape'], SAMPLE['VAV-01-OccupancySensor']],
        [tc.PH_SHAPES_V2['window-override-cmd-shape'], SAMPLE['VAV-01-WindowOverrideCommand']],
        [tc.PH_SHAPES_V2['zone-air-temp-override-sp-shape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint']],
        [tc.PH_SHAPES_V2['zone-air-co2-sensor-shape'], SAMPLE['VAV-01-ZoneAirCO2Sensor']],
        [tc.PH_SHAPES_V2['zone-air-co2-sp-shape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint']],
    ])
    def test_is_valid(self, get_haystack_g36_data_v2, get_haystack_core_generated_shapes_v2, shape_name, target_node):
        # -- Setup
        data_graph = get_haystack_g36_data_v2
        shapes_graph = get_haystack_core_generated_shapes_v2
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Assert conforms
        if not conforms:
            print(results_graph.serialize(format='turtle').decode('utf-8'))
        assert conforms

    @pytest.mark.parametrize('shape_name, target_node, remove_markers', [
        [tc.PH_SHAPES_V2['damper-cmd-shape'], SAMPLE['VAV-01-DamperPositionCommand'], ['damper']],

        # This isn't necessary since it is now not a shape but a strict type
        # [tc.PH_SHAPES_V2['DischargeAirFlowSensorShape'], SAMPLE['VAV-01-DischargeAirFlowSensor']]

        [tc.PH_SHAPES_V2['zone-air-temp-sensor-shape'], SAMPLE['VAV-01-ZoneAirTemperatureSensor'], ['zone']],
        [tc.PH_SHAPES_V2['zone-air-temp-override-cmd-shape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand'],
         ['zone']],
        [tc.PH_SHAPES_V2['occupancy-sensor-shape'], SAMPLE['VAV-01-OccupancySensor'], ['occupied']],
        [tc.PH_SHAPES_V2['window-override-cmd-shape'], SAMPLE['VAV-01-WindowOverrideCommand'], ['cmd']],
        [tc.PH_SHAPES_V2['zone-air-temp-override-sp-shape'], SAMPLE['VAV-01-ZoneAirTemperatureOverrideSetpoint'],
         ['zone']],
        [tc.PH_SHAPES_V2['zone-air-co2-sensor-shape'], SAMPLE['VAV-01-ZoneAirCO2Sensor'], ['co2']],
        [tc.PH_SHAPES_V2['zone-air-co2-sp-shape'], SAMPLE['VAV-01-ZoneAirCO2Setpoint'], ['co2']],
    ])
    def test_is_invalid(self, get_haystack_g36_data_v2, get_haystack_core_generated_shapes_v2, shape_name, target_node, remove_markers):
        # Set version for constants
        tc.set_default_versions(haystack_version=tc.V3_9_10)

        # -- Setup
        data_graph = get_haystack_g36_data_v2
        shapes_graph = get_haystack_core_generated_shapes_v2
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))
        for marker in remove_markers:
            ns_term = tg.get_namespaced_term(ont_graph, marker)
            if ns_term:
                data_graph.remove((target_node, tc.PH_DEFAULT.hasTag, ns_term))

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
        assert_remove_markers(remove_markers, results_query, target_node, ont_graph)

        # Write output to CSV for human readability
        write_csv(results_query, output_file)


class TestGeneratedEquipmentPointShapesV2:
    @pytest.mark.parametrize('shape_name, target_node', [
        # VAV-01 should be valid against the base and cooling only
        [tc.PH_SHAPES_V2['G36-Base-VAV-Shape'], SAMPLE['VAV-01']],
        [tc.PH_SHAPES_V2['G36-CoolingOnly-VAV-Shape'], SAMPLE['VAV-01']],

        # VAV-02 should be valid against the base and hot water reheat
        [tc.PH_SHAPES_V2['G36-Base-VAV-Shape'], SAMPLE['VAV-02']],
        [tc.PH_SHAPES_V2['G36-HotWaterReheat-VAV-Shape'], SAMPLE['VAV-02']],

        # VAV-03 should be valid against the base, hw reheat, and hw reheat w/fdbk
        [tc.PH_SHAPES_V2['G36-Base-VAV-Shape'], SAMPLE['VAV-03']],
        [tc.PH_SHAPES_V2['G36-HotWaterReheat-VAV-Shape'], SAMPLE['VAV-03']],
        [tc.PH_SHAPES_V2['HotWaterReheatFdbk-VAV-Shape'], SAMPLE['VAV-03']],
    ])
    def test_is_valid(self, get_haystack_g36_data_v2, get_haystack_core_generated_shapes_v2, shape_name, target_node):
        # -- Setup
        data_graph = get_haystack_g36_data_v2
        shapes_graph = get_haystack_core_generated_shapes_v2
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        str_name = str(shape_name)
        str_name = str_name.split('#')[1]
        target_name = str(target_node)
        target_name = target_name.split(str(SAMPLE))[1]

        # -- Serialize results
        f = f"Mixin_{str_name}_{target_name}" + '_valid.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        assert conforms

    @pytest.mark.parametrize('shape_name, target_node, remove_from_node, remove_markers, num_runs', [
        [
            tc.PH_SHAPES_V2['G36-CoolingOnly-VAV-Shape'], SAMPLE['VAV-01'],
            SAMPLE['VAV-01-DamperPositionCommand'], ['damper'], 2
        ],
        [
            tc.PH_SHAPES_V2['G36-CoolingOnly-VAV-Shape'], SAMPLE['VAV-01'],
            SAMPLE['VAV-01-ZoneAirTemperatureOverrideCommand'], ['zone'], 2
        ],
        [
            tc.PH_SHAPES_V2['G36-CoolingOnly-VAV-Shape'], SAMPLE['VAV-02'],
            SAMPLE['VAV-02-ZoneAirTemperatureOverrideCommand'], ['zone'], 2
        ],
        # Removes a tag on a point required by G36-Base-VAV-Shape (2 hops)
        [
            tc.PH_SHAPES_V2['HotWaterReheatFdbk-VAV-Shape'], SAMPLE['VAV-03'],
            SAMPLE['VAV-03-ZoneAirTemperatureOverrideCommand'], ['zone'], 3
        ]
    ])
    def test_is_invalid(self, get_haystack_g36_data_v2, get_haystack_core_generated_shapes_v2, shape_name, target_node,
                        remove_from_node,
                        remove_markers, num_runs):
        # Set version for constants
        tc.set_default_versions(haystack_version=tc.V3_9_10)

        # -- Setup
        data_graph = get_haystack_g36_data_v2
        shapes_graph = get_haystack_core_generated_shapes_v2
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))
        for marker in remove_markers:
            ns = tg.get_namespaces_given_term(ont_graph, marker)
            if tasty.graphs.has_one_namespace(ns, marker):
                ns = ns[0]
                data_graph.remove((remove_from_node, tc.PH_DEFAULT.hasTag, ns[marker]))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Serialize results
        f = 'TestMixins_' + '_'.join(remove_markers) + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert does not conform
        assert not conforms

        # Grab easy to read info
        str_name = str(shape_name)
        str_name = str_name.split('#')[1]
        target_name = str(target_node)
        target_name = target_name.split(str(SAMPLE))[1]

        # Here we iterate through to add target nodes
        # based on
        for run in range(num_runs - 1):
            print(f"Iteration {run} on {str_name}")
            conforms, results_graph, results = run_another(results_graph, shapes_graph, data_graph, ont_graph)

        # -- Serialize results
        f = f"Mixin_{str_name}_{target_name}" + '_'.join(remove_markers) + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert does not conform
        assert not conforms
