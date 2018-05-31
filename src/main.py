#!/usr/bin/python3

import sys
import argparse
from tools import scigraph, springer, crossref
from urllib.error import HTTPError
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

    conn = sqlite3.connect(config['db_path'])
    create_table_if_not_exists(conn)

    urls = json.load(open(config['url_path']))
    total_amount = len(urls)

    existed = count_entries(conn)
    urls = urls[existed:-1]

    for url in urls:
        doi = 'getting doi from scigraph API'
        try:
            scigraph_entry = scigraph.get_scigraph_metadata_from_url(url)
            doi = scigraph_entry['doi']
            springer_entry = springer.get_springer_metadata(doi, key)
            crossref_entry = crossref.get_crossref_metadata(doi)
            insert_entries(conn, doi, scigraph_entry, springer_entry, crossref_entry)
            daily_amount -= 1
            if daily_amount > -1:
                print('{} {} is saved, {} entries left'.format(time.strftime('%Y-%m-%d %H:%M:%S'), doi, daily_amount))
            else:
                print('daily amount is reached')
                break
        except HTTPError as err:
            conn.close()
            if err.code == 403:
                print('Springer key expires')
                return
            raise
        except (Exception, KeyboardInterrupt):
            print(doi)
            conn.close()
            raise

    if total_amount == count_entries(conn):
        print('Congratulations! All metadata fetched!')

    conn.close()


def read_updated_config(args):
    config_file = os.path.join(project_root_path, 'config.json')
    with open(config_file) as file:
        config = json.load(file)
    config['url_path'] = os.path.join(project_root_path, config['url_path'])
    config['db_path'] = os.path.join(project_root_path, config['db_path'])

    if args.daily_amount:
        config['daily_amount'] = args.daily_amount

    return config


def count_entries(conn):
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM ARTICLES')
    count = c.fetchone()[0]
    c.close()
    return count


def create_table_if_not_exists(conn):
    # create the table
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ARTICLES
                 (DOI               TEXT PRIMARY KEY NOT NULL,
                 KEYWORDS           TEXT,
                 REFERENCE          TEXT,
                 SG_TITLE           TEXT,
                 SG_ABSTRACT        TEXT,
                 SG_AUTHORS         TEXT,
                 SG_CONCEPTS        TEXT,
                 SG_PUBLICATIONDATE TEXT,
                 SG_TYPE            TEXT,
                 SG_JOURNALBRAND    TEXT,
                 SP_TITLE           TEXT,
                 SP_ABSTRACT        TEXT,
                 SP_AUTHORS         TEXT,
                 SP_CONCEPTS        TEXT,
                 SP_PUBLICATIONDATE TEXT,
                 SP_TYPE            TEXT,
                 SP_JOURNALBRAND    TEXT,
                 CR_TITLE           TEXT,
                 CR_AUTHORS         TEXT,
                 CR_CONCEPTS        TEXT,
                 CR_PUBLICATIONDATE TEXT,
                 CR_TYPE            TEXT,
                 CR_JOURNALBRAND    TEXT);''')
    c.close()
    conn.commit()


def assign_if_exist_in_dict(s, d):
    if s in d:
        return json.dumps(d[s])
    else:
        return 'NULL'


def insert_entries(conn, doi, sg, sp, cr):
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

    c = conn.cursor()
    c.execute("INSERT INTO ARTICLES VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (doi, keywords, reference,
               sg_title, sg_abstract, sg_authors, sg_concepts, sg_publication_date, sg_type, sg_journal_brand,
               sp_title, sp_abstract, sp_authors, sp_concepts, sp_publication_date, sp_type, sp_journal_brand,
               cr_title, cr_authors, cr_concepts, cr_publication_date, cr_type, cr_journal_brand))
    c.close()
    conn.commit()


if __name__ == "__main__":
    # parse arguments, update configurations
    parser = argparse.ArgumentParser()
    parser.add_argument('--daily_amount', default=None, type=int,
                        help='daily access limit of the application key of the Springer API')
    parser.add_argument("--verbose", help="increase output verbosity",
                        action="store_true")
    main(parser.parse_args())
