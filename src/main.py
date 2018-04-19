from src.tools import scigraph, springer, crossref
from urllib.error import HTTPError
import sqlite3
import json
import os

api_key = '39167b4e2411a032c6f68b771ba17795'
# api_key = '042b48a75a1efd82a47b84139210095c'
# api_key = 'b2fac16c0bbcf9351c7f207a65bb007d'
# api_key = 'c2b4c947194af768b704959206c99fe2'

expected_article_amount = 5000

current_path = os.path.abspath(os.path.dirname(__file__))
data_path = os.path.join(current_path, "../data")
db_path = os.path.join(data_path, 'articles.sqlite')
urls_path = os.path.join(data_path, 'article-urls.json')


def main():
    conn = sqlite3.connect(db_path)
    create_table(conn)

    urls = json.load(open(urls_path))
    count = 0
    length = min(expected_article_amount, len(urls))
    for url in urls:
        if count >= length:
            break

        try:
            scigraph_entry = scigraph.get_scigraph_metadata_from_url(url)
            doi = scigraph_entry['doi']
            entries = get_entries(doi, api_key)
            entries['sg'] = scigraph_entry
            insert_entries(doi, entries, conn)
        except HTTPError as err:
            if err.code == 403:
                break
            else:
                update_urls(urls, count, urls_path)
                conn.close()
                raise
        except sqlite3.IntegrityError as err:
            if err.args[0] == 'UNIQUE constraint failed: ARTICLES.DOI':
                print('entry with doi {} already exists in the db'.format(doi))
                count += 1
                continue
            else:
                raise
        except (OSError, KeyboardInterrupt):
            update_urls(urls, count, urls_path)
            conn.close()
            raise

        print('metadata of the article {} is saved in the db'.format(doi))
        count += 1

    update_urls(urls, count, urls_path)
    conn.close()


def update_urls(urls, count, urls_path):
    urls = urls[count:]
    with open(urls_path, 'w') as outfile:
        json.dump(urls, outfile)


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
    main()
