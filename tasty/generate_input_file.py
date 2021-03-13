import os
import sys

from rdflib import Graph
from rdflib.util import guess_format

import json


def generate_input_file(shapes_file, data_file, output_file, composite=True):
    with open(shapes_file, 'r') as f:
        data = json.loads(f.read())

    headers = ['entity-id', 'entity-name']
    for shape in data['shapes']:
        if composite:
            if 'shape-mixins' in shape or 'predicates' in shape:
                headers.append(shape['name'])
        else:
            headers.append(shape['name'])

    valid_file = True
    if data_file is not None and os.path.isfile(data_file):
        g = Graph()
        g.parse(sys.argv[1], format=guess_format(sys.argv[1]))
        q = """SELECT ?n ?label WHERE {
            ?n rdfs:label ?label
        }
        """
        query_response = g.query(q)
    else:
        valid_file = False

    if not output_file:
        output_file = 'input-file.csv'
    with open(output_file, 'w+') as f:
        output = ','.join(headers) + '\n'
        f.write(output)
        if valid_file:
            to_write = []
            for each in query_response:
                line = str(each[0]) + "," + str(each[1]) + ',' * (len(headers) - 2) + '\n'
                to_write.append(line)

            f.writelines(to_write)
