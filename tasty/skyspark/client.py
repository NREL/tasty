import requests

# wrap in client classs


# make parameters instance variables


# construct query method

def make_get_request(api_url_endpoint: str, query_string: str, format: str = 'json'):
    """
    Make a get request to a (Skyspark) api endpoint.

    :param api_url_endpoint: the url enpoint for the (Skyspark) api
    :type api_url_endpoint: str
    :param query_string: the (axon) query string to include in the request
    :type query_string: str
    :param format: the format in which the response should be returned options are
        ['json' , 'turtle' , 'csv' , 'zinc' , 'trio' , 'json-ld'] - the default is json
    :type format: str
    :return: the get response
    :rtype: requests.Response Object
    """
    if(format == 'turtle'):
        accept_type = 'text/turtle'
    elif(format == 'csv'):
        accept_type = 'text/csv'
    elif(format == 'json'):
        accept_type = 'application/json'
    elif(format == 'json-ld'):
        accept_type = 'application/ld+json'
    elif(format == 'zinc'):
        accept_type = 'text/zinc'
    elif(format == 'trio'):
        accept_type = 'text/trio'
    # making json the default format
    else:
        accept_type = 'application/json'

    return requests.get(
        api_url_endpoint,
        params={'filter': query_string},
        headers={
            'Accept': accept_type
        }
    )


def save_response(response_data, filename):
    """
    Save the response data to the given file

    :param response_data: the data to be saved
    :param filename: the filepath/filename to save the data
    """
    with open(filename, 'w') as file:
        file.write(response_data)


# axon_query_string = '(point and equipRef->navName=="UFVAV-3") or (equip and navName=="UFVAV-3")'

# api_url_endpoint = 'https://internal-apis.nrel.gov/intelligentcampus/stm_campus/read'

# response = make_get_request(api_url_endpoint, axon_query_string, 'turtle')

# print(response.status_code, end = " - ")
# if response.status_code == 200:
#     print("Sucess")
# elif response.status_code == 404:
#     print("Not Found")

# raw_skyspark_data = response.text
# print(raw_skyspark_data)
