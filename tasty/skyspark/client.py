import requests

# TODO:
# make parameters instance variables
# construct query method


class SkysparkClient:

    # -- Class Constructor --
    def __init__(self, api_url_endpoint):
        self.api_url_endpoint = api_url_endpoint

    def make_get_request(self, query_string: str, format: str = 'json'):
        """
        Make a get request to a (Skyspark) api endpoint. Note that the query string must be a valid
        'axon' query.

        :param query_string: the (axon) query string to include in the request
        :type query_string: str
        :param format: the format in which the response should be returned options are
            ['json' , 'turtle' , 'csv' , 'zinc' , 'trio' , 'json-ld'] - the default is json
        :type format: str
        :return: the get response
        :rtype: requests.Response Object
        """

        # set "Accept" header value based on specified format
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
        else:
            accept_type = 'application/json'  # use json if no other matches

        return requests.get(
            self.api_url_endpoint,
            params={'filter': query_string},
            headers={
                'Accept': accept_type
            }
        )
