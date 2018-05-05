from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import json
import dateutil.parser


def get_scigraph_metadata(doi):
    url = 'https://scigraph.springernature.com/api/redirect?doi={}'.format(doi)
    get_scigraph_metadata_from_url(url)


def get_scigraph_metadata_from_url(url):
    request = Request(url)
    request.add_header('Accept', 'application/ld+json')
    try:
        response = urlopen(request).read().decode('utf-8')
        objects = json.loads(response)['@graph']
    except URLError as err:
        if isinstance(err, HTTPError) and err.code == 404:
            return {}
        print(err)
        print(err.reason)
        print(type(err.reason))
        print(err.errno)
        print(type(err.errno))
        print('Retry getting entry from scigraph')
        response = urlopen(request).read().decode('utf-8')
        objects = json.loads(response)['@graph']

    entry = {}

    for obj in objects:
        obj_type = obj['@type']
        if isinstance(obj_type, str):
            if obj_type == 'owl:Class':
                entry['type'] = obj['@id']
            elif obj_type == 'sg:Article':
                load_article_info(obj, entry)
            elif obj_type == 'sg:Contribution':
                load_authors(obj, entry)
            elif obj_type == 'sg:JournalBrand':
                entry['journal_brand'] = obj['rdfs:label']
        elif isinstance(obj_type, list):
            if 'skos:Concept' in obj_type:
                load_concepts(obj, entry)

    # check_completeness(entry)
    return entry


def load_article_info(obj, entry):
    if 'sg:doi' in obj:
        entry['doi'] = obj['sg:doi']
    if 'sg:title' in obj:
        entry['title'] = obj['sg:title']
    if 'sg:abstract' in obj:
        entry['abstract'] = obj['sg:abstract']
    if 'sg:publicationDate' in obj:
        date_instance = obj['sg:publicationDate']
        if isinstance(date_instance, dict):
            entry['publication_date'] = obj['sg:publicationDate']['@value']
        elif isinstance(date_instance, list):
            dates = []
            for d in date_instance:
                dates.append(dateutil.parser.parse(d['@value']))
            date = min(dates)
            entry['publication_date'] = date.date().isoformat()
    elif 'sg:publicationYearMonth' in obj:
        entry['publication_date'] = obj['sg:publicationYearMonth']['@value']
    elif 'sg:publicationYear' in obj:
        entry['publication_date'] = obj['sg:publicationYear']['@value']


def load_concepts(obj, entry):
    if 'concepts' not in entry:
        entry['concepts'] = {}
    skos_id = obj['@id']
    skos_label = obj['skos:prefLabel']['@value']
    entry['concepts'][skos_id] = skos_label


def load_authors(obj, entry):
    if 'authors' not in entry:
        entry['authors'] = []
    if 'sg:publishedName' in obj:
        entry['authors'].append(obj['sg:publishedName'])


def check_completeness(entry):
    # print(entry)

    checklist = ['doi', 'title', 'abstract', 'authors', 'concepts', 'publication_date', 'type', 'journal_brand']
    keys = entry.keys()
    for item in checklist:
        if item not in keys:
            print(item, ' is not there!')
    # print('check done!')
