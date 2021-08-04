from tasty import constants as tc
from tasty import graphs as tg


def save_data_to_file(data, filename):
    """
    Save the response data to the given file

    :param response_data: the data to be saved
    :param filename: the filepath/filename to save the data
    """
    with open(filename, 'w') as file:
        file.write(data)


def parse_file_to_graph(file, schema=tc.HAYSTACK, version=tc.V3_9_10, format_type='turtle'):
    g = tg.get_versioned_graph(schema, version)
    g.parse(file, format=format_type)
    return g


def print_graph_to_file(g, filename, format_type='turtle'):
    g.serialize(filename, format=format_type)


def print_graph(g):
    print(g.serialize(format='turtle').decode('utf-8'))
