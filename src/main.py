#!/usr/bin/python3

import sys
import argparse
from tools import scigraph, springer, crossref
from urllib.error import HTTPError
import sqlite3
import json
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument('--daily_amount', default=15000, type=int, help='daily access limit of the application key of the Springer API')
parser.add_argument('--key', default='39167b4e2411a032c6f68b771ba17795', type=str, help='the application key of the Springer API')
total_article_amount = 349877

current_path = os.path.abspath(os.path.dirname(__file__))
data_path = os.path.join(current_path, '../data')
db_path = os.path.join(data_path, 'articles.sqlite')
urls_path = os.path.join(data_path, 'article-urls.json')


def main(argv):
    args = parser.parse_args(argv[1:])

    conn = sqlite3.connect(db_path)
    create_table(conn)

    urls = json.load(open(urls_path))
    count = 0

    for url in urls:
        try:
            scigraph_entry = scigraph.get_scigraph_metadata_from_url(url)
            doi = scigraph_entry['doi']
            entries = get_entries(doi, args.key)
            entries['sg'] = scigraph_entry
            insert_entries(doi, entries, conn)
            count += 1
            if count < args.daily_amount:
                print('{}, {} is saved, {} entries left'.format(time.strftime('%Y-%m-%d %H:%M:%S'), doi, args.daily_amount - count))
            else:
                break
        except (Exception, KeyboardInterrupt) as err:
            if isinstance(err, sqlite3.IntegrityError) and err.args[0] == 'UNIQUE constraint failed: ARTICLES.DOI':
                existed = count_entries(conn)
                count = len(urls) - (total_article_amount - existed)

            conn.close()
            if count > 0:
                update_urls(urls, count, urls_path)
                
            if isinstance(err, KeyboardInterrupt):
                return
            elif isinstance(err, HTTPError) and err.code == 403:
                print('Springer key expires')
                return
            raise

    conn.close()
    print('Congratulations! All metadata fetched!')


def count_entries(conn):
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM ARTICLES')
    count = c.fetchone()[0]
    c.close()
    return count


def update_urls(urls, count, urls_path):
    urls = urls[count:]
    with open(urls_path, 'w') as outfile:
        json.dump(urls, outfile)
    print('urls in the input file is updated')


def get_entries(doi, api_key):
    # scigraph_entry = scigraph.get_scigraph_metadata(doi)
    springer_entry = springer.get_springer_metadata(doi, api_key)
    crossref_entry = crossref.get_crossref_metadata(doi)

    # return {'sg': scigraph_entry, 'sp': springer_entry, 'cr': crossref_entry}
    return {'sp': springer_entry, 'cr': crossref_entry}


def create_table(conn):
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


def insert_entries(doi, entries, conn):
    sg = entries['sg']
    sp = entries['sp']
    cr = entries['cr']

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
    main(sys.argv)
