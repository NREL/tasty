import os

import pytest
from rdflib import Namespace, SH
from pyshacl import validate

from tasty import constants as tc
from tasty import graphs as tg


NAMESPACE = Namespace('urn:sample/')
SHAPE = 'NREL_VAV_SD_HW_Reheat_Shape'
SAMPLE = 'NREL-VAV-HW-Reheat-01'
TTL_FILE_PREFIX = 'TestNRELVavElecReheat'


class TestNRELVavElecReheat:

    @pytest.mark.parametrize('shape_name, target_node', [
        [tc.PH_SHAPES_NREL[SHAPE], NAMESPACE[SAMPLE]]
    ])
    def test_is_valid(self, get_haystack_nrel_data, get_haystack_all_generated_shapes, shape_name, target_node):
        # -- Setup
        data_graph = get_haystack_nrel_data
        shapes_graph = get_haystack_all_generated_shapes
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Serialize results
        f = TTL_FILE_PREFIX + '_valid.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        if not conforms:
            # serialize shapes graph for debugging
            shapes_graph.serialize(TTL_FILE_PREFIX + '-test_is_valid.ttl', format='turtle')
        assert conforms
