import os
import sys
import json

# constants, configure to match your environment
HOST = 'http://localhost:9200'
INDEX = 'medicalLibrary'
TYPE = 'book'

import elasticsearch
es = elasticsearch.Elasticsearch()  # use default of localhost, port 9200

if __name__ == '__main__':


	for each in os.listdir(sys.argv[1]):
		if os.path.splitext(each)[1].lower() == str(sys.argv[2]):
			with open(os.path.join(sys.argv[1], each) ) as f:
				page = f.read()
			
			outputJson = { "title": "article",
							"page": "blank",
							"content": page }
			
			print "Indexing %s" % each
			es.index(index='library', doc_type='bookHOCR', body=json.dumps(outputJson))