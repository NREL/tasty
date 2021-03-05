import os
import sys

from rdflib import Graph
from rdflib.util import guess_format

import json

my_dir = os.path.dirname(__file__)
core_shape_file = os.path.join(my_dir, 'source_shapes', 'core_v2.json')

with open(core_shape_file, 'r') as f:
    data = json.loads(f.read())

headers = ['entity-id', 'entity-name']
for shape in data['shapes']:
    headers.append(shape['name'])

if len(sys.argv) == 2:
    g = Graph()
    g.parse(sys.argv[1], format=guess_format(sys.argv[1]))
    q = """SELECT ?n ?label WHERE {
        ?n rdfs:label ?label
    }
    """
    query_response = g.query(q)

with open('input-file.csv', 'w+') as f:
    output = ','.join(headers) + '\n'
    f.write(output)
    if len(sys.argv) == 2:
        to_write = []
        for each in query_response:
            line = str(each[0]) + "," + str(each[1]) + ',' * (len(headers) - 2) + '\n'
            to_write.append(line)

        f.writelines(to_write)
