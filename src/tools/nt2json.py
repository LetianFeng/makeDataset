import os
import json
from rdflib import Graph

# input parameters
file_name = '2017.nt'
n = 259640

# path settings
current_path = os.path.abspath(os.path.dirname(__file__))
data_path = os.path.join(current_path, '../../data')
nt_path = os.path.join(data_path, file_name)
tmp_path = os.path.join(data_path, 'tmp.txt')
json_path = os.path.join(data_path, file_name.replace('.nt', '.json'))

# get first n lines of the n-triple file
with open(nt_path) as nt_file:
    head = [next(nt_file) for i in range(n)]

# store it in a temporary file
with open(tmp_path, 'w') as nt_file:
    for nt in head:
        nt_file.write(nt)

# load entries and remove the temporary file
g = Graph()
g.parse(tmp_path, format='nt')
os.remove(tmp_path)

# retrieve scigraph urls and save them in a list
urls = []
for s in g.subjects():
    urls.append(str(s))

# store the list as a json-file
json_file = open(json_path, 'w')
json_file.write(json.dumps(urls))
