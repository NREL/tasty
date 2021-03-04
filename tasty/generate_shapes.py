import os
import json
from rdflib import BNode, Namespace, Literal, Graph

import tasty.graphs as tg
import tasty.constants as tc
import tasty.templates as tt


# Functions
def add_standard_tags(g: Graph, shape_map):
    count_tags = 0
    if shape_map.get('tags') is not None:
        for tag in shape['tags']:
            count_tags += 1
            potential_namespaces = tg.get_namespaces_given_term(ontology, tag)
            if tt.has_one_namespace(potential_namespaces, tag):
                tag_ns = potential_namespaces[0]
                prop_bn = BNode()
                qvs_bn = BNode()
                g.add((ns[shape['name']], tc.SH.property, prop_bn))
                g.add((prop_bn, tc.SH.path, tc.PH_3_9_9.hasTag))
                g.add((prop_bn, tc.SH.qualifiedValueShape, qvs_bn))
                g.add((prop_bn, tc.SH.qualifiedMinCount, Literal(1)))
                g.add((qvs_bn, tc.SH.hasValue, tag_ns[tag]))

        # Here we just add a minCount equal to the total number of tags
        bn = BNode()
        g.add((ns[shape['name']], tc.SH.property, bn))
        g.add((bn, tc.SH.path, tc.PH_3_9_9.hasTag))
        g.add((bn, tc.SH.minCount, Literal(count_tags)))


if __name__ == '__main__':
    files = [os.path.join(os.path.dirname(__file__), 'source_shapes', f) for f in
             os.listdir(os.path.join(os.path.dirname(__file__), 'source_shapes')) if f.endswith('.json')]

    data = {}
    for file in files:
        with open(file, 'r') as f:
            data[os.path.basename(file)] = json.loads(f.read())

    g = tg.get_versioned_graph('Haystack', '3.9.9')
    ontology = tg.load_ontology('Haystack', '3.9.9')

    for lib, lib_info in data.items():
        if lib.startswith('core'):
            prefix = data[lib]['prefix']
            ns = Namespace(data[lib]['namespace'])
            shapes = data[lib]['shapes']
            g.bind(prefix, ns)

            for shape in shapes:
                ns_shape = ns[shape['name']]
                if shape.get('tags') is not None:
                    g.add((ns_shape, tc.RDF.type, tc.SH.NodeShape))
                    add_standard_tags(g, shape)
    output = os.path.join(os.path.dirname(__file__), 'generated')
    if not os.path.isdir(output):
        os.mkdir(output)
    g.serialize(destination=os.path.join(output, 'core.ttl'), format='turtle')
