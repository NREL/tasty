
def save_response(response_data, filename):
    """
    Save the response data to the given file

    :param response_data: the data to be saved
    :param filename: the filepath/filename to save the data
    """
    with open(filename, 'w') as file:
        file.write(response_data)
