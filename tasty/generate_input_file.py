import os
from typing import List

from rdflib import Graph
from rdflib.util import guess_format

import json


def generate_input_file(shape_files: List, data_graph: str, output_file: str, composite: bool = True):
    """
    Generate a csv file for users to input data. The shape name column headers are added based on
    the shape files provided. entity ids and names are populated from the data file provided.
        | entity-id | entity-name | shape-name-1 | ...
        | ...id1... | ..a name..  |              | ..
    :param shape_files: paths to JSON source_shapes files to use to populate the csv headers
    :param data_graph: name of data graph to read in to populate entity-id and entity-name columns
    :param output_file: path to output file to write
    :param composite: whether to only consider more complex shapes
    :return:
    """
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
    if data_graph is not None and os.path.isfile(data_graph):
        g = Graph()
        g.parse(data_graph, format=guess_format(data_graph))
        q = """SELECT ?s ?label WHERE {
            ?s a ?o .
            OPTIONAL { ?s rdfs:label ?label }
        }
        """
        query_response = g.query(q)
    elif data_graph is None:
        print(f"No input data file provided. Proceeding fine.")
        valid_file = False
    elif not os.path.isfile(data_graph):
        print(f"Unable to find data file: {data_graph}. Proceeding fine.")
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
