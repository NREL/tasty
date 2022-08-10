from tasty import constants as tc
from tasty import graphs as tg


def save_data_to_file(data, filename):
    """
    Save the given data to the given file

    :param data: the data to be saved
    :param filename: the filepath/filename in which to save the data
    """
    with open(filename, 'w') as file:
        file.write(data)


def parse_file_to_graph(filename, schema=tc.HAYSTACK, version=tc.V3_9_10, format_type='turtle'):
    """
    Parse the data from the given file to a graph (rdflib) with the given schema.

    :param filename: the filepath/filename from which to parse
    :param schema: the schema of the graph to be created; defualt is Haystack
    :param schema: the version of the schema; defualt is v3.9.10 (Haystack)
    :param format_type: the format of the file to be read parsed; defualt is 'turtle'
    """
    g = tg.get_versioned_graph(schema, version)
    g.parse(filename, format=format_type)
    return g


def print_graph_to_file(graph, filename, format_type='turtle'):
    """
    Serialize the given graph (rdflib) to the given file with the given format.

    :param graph: the rdflib graph to serialize
    :param filename: the filepath/filename in which to save the serialized graph
    :param format_type: the format in which to serialize the graph; defualt is 'turtle'
    """
    graph.serialize(filename, format=format_type)


def print_graph(graph):
    """
    Print the given graph (rdflib) to the terminal

    :param graph: the rdflib graph to print
    """
    print(graph.serialize(format='turtle', encoding='utf-8'))
