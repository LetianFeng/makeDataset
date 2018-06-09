#!/usr/bin/python3

import argparse
from tools import scigraph, springer, crossref, database
from urllib.error import HTTPError, URLError
import sqlite3
import json
import os
import time

current_path = os.path.abspath(os.path.dirname(__file__))
project_root_path = os.path.join(current_path, '..')


def main(args):
    config = read_updated_config(args)
    key = config['springer_key']
    daily_amount = config['daily_amount']
    retry = config['retry']
    verbose = config['verbose']

    conn = sqlite3.connect(config['db_path'])
    database.create_table_if_not_exists(conn, 'ARTICLES')

    urls = json.load(open(config['url_path']))
    total_amount = len(urls)

    existed = database.count_entries(conn)
    urls = urls[existed:-1]

    for url in urls:
        try:
            values = get_metadata_values_to_insert(url, key, retry, verbose)
        except KeyboardInterrupt:
            print('Keyboard Interrupt')
            break
        except Exception as err:
            if isinstance(err, HTTPError) and err.code == 403:
                print('Springer key expires')
                break
            else:
                conn.close()
                raise

        database.insert(conn, 'ARTICLES', values)
        daily_amount -= 1

        if daily_amount > -1:
            print('{} {} is saved, {} entries left'.format(time.strftime('%Y-%m-%d %H:%M:%S'), values[0], daily_amount))
        else:
            print('daily amount is reached')
            break

    existed = database.count_entries(conn)

    if total_amount == existed:
        print('Congratulations! All metadata fetched!')
    else:
        print('{} of {} fetched'.format(existed, total_amount))

    conn.close()


def read_updated_config(args):
    config_file = os.path.join(project_root_path, 'config.json')
    with open(config_file) as file:
        config = json.load(file)
    config['url_path'] = os.path.join(project_root_path, config['url_path'])
    config['db_path'] = os.path.join(project_root_path, config['db_path'])

    if args.daily_amount:
        config['daily_amount'] = args.daily_amount

    config['verbose'] = args.verbose

    return config


def get_metadata(url, key, n, verbose):
    doi = None
    scigraph_entry = None
    springer_entry = None
    crossref_entry = None

    # try n times
    for i in range(n + 1):
        try:
            if scigraph_entry is None:
                scigraph_entry = scigraph.get_scigraph_metadata_from_url(url)
                doi = scigraph_entry['doi']
                if verbose:
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), 'got scigraph entry, doi {}'.format(doi))
        except Exception as err:
            if i < n:
                # Server Internal Error at SciGraph side
                if isinstance(err, HTTPError) and (err.code == 500 or err.code == 504):
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), err, 'try again')
                    continue
                elif isinstance(err, URLError):
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), err, 'try again')
                    continue
            raise

    for i in range(n + 1):
        if springer_entry is not None and crossref_entry is not None:
            break
        try:
            if springer_entry is None:
                springer_entry = springer.get_springer_metadata(doi, key)
                if verbose:
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), 'got springer entry')
            if crossref_entry is None:
                crossref_entry = crossref.get_crossref_metadata(doi)
                if verbose:
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), 'got crossref entry')
        except Exception as err:
            if i < n:
                # Server Internal Error at SciGraph side
                if isinstance(err, HTTPError) and (err.code == 500 or err.code == 504):
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), err, 'try again')
                    continue
                elif isinstance(err, URLError):
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), err, 'try again')
                    continue
            raise

    return doi, scigraph_entry, springer_entry, crossref_entry


def assign_if_exist_in_dict(s, d):
    if s in d:
        return json.dumps(d[s])
    else:
        return 'NULL'


def get_metadata_values_to_insert(url, key, retry, verbose):
    # get metadata from 3 APIs: scigraph, springer, crossref
    doi, sg, sp, cr = get_metadata(url, key, retry, verbose)

    # extract values we need for our database
    doi = json.dumps(doi)
    keywords = assign_if_exist_in_dict('keywords', sp)
    reference = assign_if_exist_in_dict('reference', cr)

    sg_title = assign_if_exist_in_dict('title', sg)
    sg_abstract = assign_if_exist_in_dict('abstract', sg)
    sg_authors = assign_if_exist_in_dict('authors', sg)
    sg_concepts = assign_if_exist_in_dict('concepts', sg)
    sg_publication_date = assign_if_exist_in_dict('publication_date', sg)
    sg_type = assign_if_exist_in_dict('type', sg)
    sg_journal_brand = assign_if_exist_in_dict('journal_brand', sg)

    sp_title = assign_if_exist_in_dict('title', sp)
    sp_abstract = assign_if_exist_in_dict('abstract', sp)
    sp_authors = assign_if_exist_in_dict('authors', sp)
    sp_concepts = assign_if_exist_in_dict('concepts', sp)
    sp_publication_date = assign_if_exist_in_dict('publication_date', sp)
    sp_type = assign_if_exist_in_dict('type', sp)
    sp_journal_brand = assign_if_exist_in_dict('journal_brand', sp)

    cr_title = assign_if_exist_in_dict('title', cr)
    cr_authors = assign_if_exist_in_dict('authors', cr)
    cr_concepts = assign_if_exist_in_dict('concepts', cr)
    cr_publication_date = assign_if_exist_in_dict('publication_date', cr)
    cr_type = assign_if_exist_in_dict('type', cr)
    cr_journal_brand = assign_if_exist_in_dict('journal_brand', cr)

    # make a tuple of those values according to the schema in database.py
    values = (doi, keywords, reference,
              sg_title, sg_abstract, sg_authors, sg_concepts, sg_publication_date, sg_type, sg_journal_brand,
              sp_title, sp_abstract, sp_authors, sp_concepts, sp_publication_date, sp_type, sp_journal_brand,
              cr_title, cr_authors, cr_concepts, cr_publication_date, cr_type, cr_journal_brand)

    return values


if __name__ == "__main__":
    # parse arguments, update configurations
    parser = argparse.ArgumentParser()
    parser.add_argument('--daily_amount', default=None, type=int,
                        help='daily access limit of the application key of the Springer API')
    parser.add_argument("--verbose", help="increase output verbosity",
                        action="store_true")
    main(parser.parse_args())
