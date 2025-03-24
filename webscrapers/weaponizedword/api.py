import os
import json
import requests
import numpy as np
from tqdm import tqdm
from copy import deepcopy

# an example data query
query_data = {
    'is_about_nationality': 'N',
    'is_about_ethnicity': 'N',
    'is_about_religion': 'N',
    'is_about_gender': 'N',
    'is_about_orientation': 'N',
    'is_about_disability': 'N',
    'is_about_class': 'N',
}

class weaponizedword():

    def __init__(self,  API_KEY: str):
        super(weaponizedword, self).__init__()
        self.example_query = query_data
        self.request_url = 'https://api.weaponizedword.org/lexicons/1-0/{}/'
        self.__api_key = API_KEY

        self.token = requests.post(
            str(self.request_url).format('authenticate'),
            data={'api_key': self.__api_key}
        ).json()

        self.known_endpoints = ['get_derogatory', 'get_threatening', 'get_dicriminatory', 'get_watchwords']
        self.results = []

    def update_token(self):
        self.token = requests.post(str(self.request_url).format('authenticate'), data={'api_key': self.__api_key}).json()

    def search(self, endpoint_name: str = 'get_watchwords', query_data: dict=dict(), language_id: str='eng'):
        request_url = str(self.request_url).format(endpoint_name)

        data = {
            'token': self.token['result']['token'],
            'language_id': language_id
        }

        data.update(query_data)

        response = requests.post(
            request_url,
            data=data
        ).json()

        results = deepcopy(response['result'])

        while int(response['page']) < int(response['number_of_pages']):
            data['page'] = str(int(response['page']) + 1)
            response = requests.post(
                request_url,
                data=data
            ).json()

            results += deepcopy(response['result'])

        self.results += results

    def _create_query_from_results_(self, search_fields: dict=dict()):
        query_pieces = []
        for res in self.results:
            ct = 0
            for k,v in search_fields.items():
                ct += int(res[k] == v)
            if ct == len(search_fields):
                query_pieces += [res['term']]

        return ' OR '.join(['"{}"'.format(t) for t in set(query_pieces)])

    def create_query_from_results(self, field: str, value: object, allow_repeated_terms: bool=False):
        query_pieces = []
        term_counts = np.array([[res['term'], str(res[field])] for res in self.results], dtype=object)

        for res in self.results:
            if bool(res[field]):
                if value in res[field]:
                    if allow_repeated_terms:
                        query_pieces += [res['term']]
                    else:
                        if len(set(term_counts[:,1][term_counts[:,0] == res['term']])) == 1:
                            query_pieces += [res['term']]

        return ' OR '.join(['"{}"'.format(t) for t in set(query_pieces)])

    def create_regex_from_results(self, field: str, value: object, allow_repeated_terms: bool=False):
        query_pieces = []
        term_counts = np.array([[res['term'], str(res[field])] for res in self.results], dtype=object)

        for res in self.results:
            if bool(res[field]):
                if value in res[field]:
                    if allow_repeated_terms:
                        query_pieces += [res['term']]
                    else:
                        if len(set(term_counts[:,1][term_counts[:,0] == res['term']])) == 1:
                            query_pieces += [res['term']]

        return r"({})".format('|'.join(set(query_pieces)))

    def create_query_with_keyword_fields(self, search_fields: dict=dict()):
        query_pieces = []
        for res in self.results:
            for k,v in search_fields.items():
                if v.lower() in res[k].lower():
                    query_pieces += [res['term']]

        return ' OR '.join(['"{}"'.format(t) for t in set(query_pieces)])

    def save_search(self, file_name: str='ww-search-results.json'):
        location = os.path.dirname(os.path.abspath(__file__))

        search = json.dumps(self.results, indent=4)
        with open(os.path.join(location, file_name), 'w') as f:
            f.write(search)
        f.close()

    def load_search(self, file_name: str='ww-search-results.json'):
        location = os.path.dirname(os.path.abspath(__file__))

        f = open(os.path.join(location, file_name))
        self.results = json.load(f)
        f.close()


