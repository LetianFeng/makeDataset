import os
import sqlite3
import math

schema = [('DOI', 'TEXT', True, True),
          ('KEYWORDS', 'TEXT', False, False),
          ('REFERENCE', 'TEXT', False, False),
          ('SG_TITLE', 'TEXT', False, False),
          ('SG_ABSTRACT', 'TEXT', False, False),
          ('SG_AUTHORS', 'TEXT', False, False),
          ('SG_CONCEPTS', 'TEXT', False, False),
          ('SG_PUBLICATIONDATE', 'TEXT', False, False),
          ('SG_TYPE', 'TEXT', False, False),
          ('SG_JOURNALBRAND', 'TEXT', False, False),
          ('SP_TITLE', 'TEXT', False, False),
          ('SP_ABSTRACT', 'TEXT', False, False),
          ('SP_AUTHORS', 'TEXT', False, False),
          ('SP_CONCEPTS', 'TEXT', False, False),
          ('SP_PUBLICATIONDATE', 'TEXT', False, False),
          ('SP_TYPE', 'TEXT', False, False),
          ('SP_JOURNALBRAND', 'TEXT', False, False),
          ('CR_TITLE', 'TEXT', False, False),
          ('CR_AUTHORS', 'TEXT', False, False),
          ('CR_CONCEPTS', 'TEXT', False, False),
          ('CR_PUBLICATIONDATE', 'TEXT', False, False),
          ('CR_TYPE', 'TEXT', False, False),
          ('CR_JOURNALBRAND', 'TEXT', False, False)]


def main():
    current_path = os.path.abspath(os.path.dirname(__file__))
    project_root_path = os.path.abspath(os.path.join(current_path, '../..'))
    src_db = os.path.join(project_root_path, 'data/2016.sqlite.bak')
    tgt_db = os.path.join(project_root_path, 'data/2015.sqlite.bak')

    merge(src_db, 'ARTICLES', tgt_db, 'ARTICLES')


def count_entries(conn):
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM ARTICLES')
    count = c.fetchone()[0]
    c.close()
    return count


def merge(source_db, source_table, target_db, target_table):
    source_conn = sqlite3.connect(source_db)
    source_cursor = source_conn.cursor()
    target_conn = sqlite3.connect(target_db)
    target_cursor = target_conn.cursor()

    limit = 1000
    offset = 0
    amount = count_entries(source_conn)
    steps = int(math.ceil(amount/limit))

    for i in range(steps):
        entries = []
        for row in source_cursor.execute('SELECT * FROM {} LIMIT {} OFFSET {}'.format(source_table, limit, offset)):
            entries.append(row)
        target_cursor.executemany(
            'INSERT INTO {} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'.format(target_table), entries)
        target_conn.commit()
        if len(entries) > 0:
            offset += limit
        else:
            break

    source_cursor.close()
    source_conn.close()
    target_cursor.close()
    target_conn.close()


def insert(conn, table, values):
    c = conn.cursor()
    c.execute('INSERT INTO {} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'.format(table), values)
    c.close()
    conn.commit()


# schema is a list of lists[(column name, datatype, primary key, not null), (c, d, p, n), ...]
# each tuple represents a column
# column name and datatype are string values
# primary key and not null are True/False values
def create_table_if_not_exists(conn, name):
    columns = []
    for c, d, p, n in schema:
        column = [c, d]
        if p:
            column.append('PRIMARY KEY')
        if n:
            column.append('NOT NULL')
        column = ' '.join(column)
        columns.append(column)

    statement = 'CREATE TABLE IF NOT EXISTS {} ({});'.format(name, ', '.join(columns))

    c = conn.cursor()
    c.execute(statement)
    c.close()
    conn.commit()


if __name__ == "__main__":
    main()
