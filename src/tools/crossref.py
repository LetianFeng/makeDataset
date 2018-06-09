from urllib.request import urlopen, Request
from urllib.error import HTTPError
import json


def load_publication_date(message):
    if 'published-online' in message:
        date = message['published-online']['date-parts'][0]
    elif 'published-print' in message:
        date = message['published-print']['date-parts'][0]

    return str.join('-', [str(d) for d in date])


def get_crossref_metadata(doi):
    url = 'https://api.crossref.org/works/{}'.format(doi)

    request = Request(url)
    request.add_header('Accept', 'application/json')
    try:
        response = urlopen(request, timeout=2).read().decode('utf-8')
        obj = json.loads(response)
    except Exception as err:
        if isinstance(err, HTTPError) and err.code == 404:
            return {}
        raise

    entry = {}

    message = obj['message']
    if 'DOI' in message:
        entry['doi'] = message['DOI']
    if 'title' in message:
        if len(message['title']) > 0:
            entry['title'] = message['title'][0]
    if 'subject' in message:
        entry['concepts'] = message['subject']
    if 'published-online' in message or 'published-print' in message:
        entry['publication_date'] = load_publication_date(message)
    if 'type' in message:
        entry['type'] = message['type']
    if 'container-title' in message:
        entry['journal_brand'] = message['container-title'][0]
    if 'author' in message:
        load_authors(message['author'], entry)
    if 'reference' in message:
        load_reference(message['reference'], entry)

    # check_completeness(entry)
    return entry


def load_authors(authors, entry):
    if len(authors) > 0:
        author_list = []
        for author in authors:
            if 'name' in author:
                name = author['name']
            elif 'given' in author and 'family' in author:
                name = "{} {}".format(author['given'], author['family'])
            elif 'given' in author:
                name = author['given']
            elif 'family' in author:
                name = author['family']
            else:
                name = None
            if name is not None:
                author_list.append(name)
        entry['authors'] = author_list


def load_reference(objs, entry):
    if len(objs) > 0:
        d = {}
        for obj in objs:
            if 'unstructured' in obj:
                key = obj['unstructured']
                if 'DOI' in obj:
                    val = obj['DOI']
                else:
                    val = ''
                d[key] = val
        entry['reference'] = d


def check_completeness(entry):
    print(entry)

    checklist = ['doi', 'title', 'authors', 'concepts', 'publication_date', 'type', 'journal_brand', 'reference']
    keys = entry.keys()
    for item in checklist:
        if item not in keys:
            print(item, ' is not there!')
    # print('check done!')
