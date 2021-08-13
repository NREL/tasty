import requests

# TODO:
# make parameters instance variables
# construct query method


class SkysparkClient:
    """
    This class is a wrapper for the SkySpark web API. It is defined with a URL endpoint;
    once it is instantiated it can be used to make a get request from the API and can also
    to generate the proper axon query.
    """

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
        mapping_dict = {
            'turtle': 'text/turtle',
            'csv': 'text/csv',
            'json': 'application/json',
            'json-ld': 'application/ld+json',
            'zinc': 'text/zinc',
            'trio': 'text/trio'
        }

        if format in mapping_dict:
            accept_type = mapping_dict[format]
        else:
            accept_type = 'application/json'  # use json as default if no matches

        return requests.get(
            self.api_url_endpoint,
            params={'filter': query_string},
            headers={
                'Accept': accept_type
            }
        )

    def generate_axon_query_for_equip(self, nav_name: str):
        """
        This method generates a query for a given peice of a equipment. Given the equipment's "navName" the query string
        will query for the equipment itself and all points that have it as an equipRef.

        :nav_name: the navName (from Skyspark) of the equipment for which to generate the query
        """
        query_string = "(point and equipRef->navName==\"" + nav_name + "\") or (equip and navName==\"" + nav_name + "\")"
        return query_string
