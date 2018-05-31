# makeDataset
This little program is used to gather metadata from 3 different scholarly publication APIs: SciGraph, Springer &amp; CrossRef.

The current input is a json list of scigraph urls, the program resolves firstly the DOI from the SciGraph-response, and then requests metadata from the other 2 APIs based on the DOI.

Please specify your configurations in the 'config.json', especially the `springer_key`, without a valid key, this program cannot work at all. The config file should have the following format:

```json
{
    "springer_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "daily_amount": 5000,
    "retry": 1,
    "url_path": "path/to/urls.json",
    "db_path": "path/to/database.sqlite"
}
```


The program is currently still in development, the next feature is:
1. add feature --verbose and --log
2. get metadata from 3 different APIs based on DOI instead of SciGraph-url
