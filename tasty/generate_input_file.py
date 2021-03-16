import os

from rdflib import Graph
from rdflib.util import guess_format

import json


def generate_input_file(shape_files, data_file, output_file, composite=True):
    headers = ['entity-id', 'entity-name']

    for shape_file in shape_files:
        with open(shape_file, 'r') as f:
            data = json.loads(f.read())

        prefix = data['prefix']
        for shape in data['shapes']:
            if composite:
                if 'shape-mixins' in shape or 'predicates' in shape:
                    headers.append(prefix + ':' + shape['name'])
            else:
                headers.append(prefix + ':' + shape['name'])

    valid_file = True
    if data_file is not None and os.path.isfile(data_file):
        g = Graph()
        g.parse(data_file, format=guess_format(data_file))
        q = """SELECT ?s ?label WHERE {
            ?s a ?o .
            OPTIONAL { ?s rdfs:label ?label }
        }
        """
        query_response = g.query(q)
    elif data_file is None:
        print(f"No input data file provided. Proceeding fine.")
        valid_file = False
    elif not os.path.isfile(data_file):
        print(f"Unable to find data file: {data_file}. Proceeding fine.")
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
