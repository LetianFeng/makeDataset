from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import json


def get_springer_metadata(doi, api_key):
    url = 'http://api.springer.com/metadata/json?q=doi:{}&api_key={}'.format(doi, api_key)

    request = Request(url)
    request.add_header('Accept', 'application/json')
    try:
        response = urlopen(request).read().decode('utf-8')
        obj = json.loads(response)
    except Exception as err:
        if isinstance(err, HTTPError) and err.code == 404:
            return {}
        raise

    entry = {}

    load_record(obj['records'], entry)
    if len(entry) > 0:
        load_facet(obj['facets'], entry)

    # check_completeness(entry)
    return entry


def load_record(record, entry):
    if len(record) == 0:
        return

    record = record[0]
    if 'identifier' in record:
        entry['doi'] = record['identifier'].replace('doi:', '')
    if 'title' in record:
        entry['title'] = record['title']
    if 'abstract' in record:
        entry['abstract'] = record['abstract']
    if 'publicationDate' in record:
        entry['publication_date'] = record['publicationDate']
    if 'publicationName' in record:
        entry['journal_brand'] = record['publicationName']

    if 'creators' in record:
        authors = record['creators']
        if len(authors) > 0:
            al = []
            for author in authors:
                al.append(author['creator'])
            entry['authors'] = al


def load_facet(facet, entry):
    for obj in facet:
        name = obj['name']
        if name == 'type':
            entry['type'] = obj['values'][0]['value']
        if name == 'keyword':
            for keyword in obj['values']:
                if 'keywords' not in entry:
                    entry['keywords'] = []
                entry['keywords'].append(keyword['value'])
        if name == 'subject':
            for subject in obj['values']:
                if 'concepts' not in entry:
                    entry['concepts'] = []
                entry['concepts'].append(subject['value'])


def check_completeness(entry):
    # print(entry)

    checklist = ['doi', 'title', 'abstract', 'authors', 'concepts', 'publication_date', 'type', 'journal_brand',
                 'keywords']
    keys = entry.keys()
    for item in checklist:
        if item not in keys:
            print(item, ' is not there!')
    # print('check done!')
