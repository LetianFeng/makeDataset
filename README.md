# makeDataset
This little program is used to gather metadata from 3 different scholarly publication APIs: SciGraph, Springer &amp; CrossRef.

The current input is a json list of scigraph urls, the program resolves firstly the DOI from the SciGraph-response, 
and then requests metadata from the other 2 APIs based on the DOI.

The program is currently still in development, there are still many issues to be fixed and automation to be done:
  1. Handle the socket exception about hostname cannot be resolved;
  2. Change springer keys as a input file or a list of arguements;
  3. Integrate the function to transform a [official n-triple file](http://scigraph.springernature.com/explorer/downloads/) 
  to a scigraph-url json list;
  4. etc.

Currently, I'm getting metadata for 2016, once it is done, I'll give an link to share.
