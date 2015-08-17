from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

import os
import elasticsearch

# POSSIBLE CONFIG PARAMETERS
HITS_PER_PAGE = 10

es = elasticsearch.Elasticsearch()

@login_required
def index(request):
	if 'formName' in request.POST:
		if request.POST['formName'] == 'searchForm':
			
			query = {
				'query': {
					"query_string" : {
						"query": request.POST['searchTerms'],
					}
				},
				"highlight": {
					"preTags" : ["<strong>"],
					"postTags" : ["</strong>"],
					"fields" : {
						"order": "score",
						"pageContent" : {"fragment_size" : "250", "number_of_fragments" : "3"},
					}
				}
			}

			hits = es.search(index="library", body=query)
			
			# Calculate the number of pages necessary to display the results
			# Python 2.7 compat
			numPages = int(hits['hits']['total'])/HITS_PER_PAGE
			
			try:
				if HITS_PER_PAGE/ (int(hits['hits']['total'])-(numPages * HITS_PER_PAGE)) > 0:
					numPages += 1
			except ZeroDivisionError:
				pass
			
			# pre-process hit list, as _source is a no go for django's templating system
			processedHits = []
			import pprint
			for hit in hits["hits"]["hits"]:
				
				# Im not sure why we're getting some queries without a highlight
				try:
					processedHits.append({ 'pageId':hit["_id"], 'source':hit["_source"], 'highlight':hit["highlight"] })
				except KeyError:
					processedHits.append({ 'pageId':hit["_id"], 'source':hit["_source"] })
					
			# Set the query as the currentQuery for retrieval by pagination 
			request.session['currentQuery'] = request.POST['searchTerms']
			
			return render(request, 'query.html', {'username':request.user, 'hits':processedHits, 'numPages':numPages,  'currentQuery': request.POST['searchTerms'] })
	
	if request.session.has_key('currentQuery'):
		query = {
			'query': {
				"query_string" : {
					"query": request.session["currentQuery"],
				}
			},
			"highlight": {
				"preTags" : ["<strong>"],
				"postTags" : ["</strong>"],
				"fields" : {
					"order": "score",
					"pageContent" : {"fragment_size" : "250", "number_of_fragments" : "3"},
				}
			}
		}
		
		hits = es.search(index="library", body=query)
		
		# Calculate the number of pages necessary to display the results
		# Python 2.7 compat
		numPages = int(hits['hits']['total'])/HITS_PER_PAGE
		
		try:
			if HITS_PER_PAGE/ (int(hits['hits']['total'])-(numPages * HITS_PER_PAGE)) > 0:
				numPages += 1
		except ZeroDivisionError:
			pass
		
		# pre-process hit list, as _source is a no go for django's templating system
		processedHits = []
		import pprint
		for hit in hits["hits"]["hits"]:
			
			# Im not sure why we're getting some queries without a highlight
			try:
				processedHits.append({ 'pageId':hit["_id"], 'source':hit["_source"], 'highlight':hit["highlight"] })
			except KeyError:
				processedHits.append({ 'pageId':hit["_id"], 'source':hit["_source"] })
		
		return render(request, 'query.html', {'username':request.user, 'hits':processedHits, 'numPages':numPages, 'currentQuery':request.session["currentQuery"] })

	return render(request, 'query.html', { 'username':request.user, 'currentQuery':"Search Terms" })

@login_required
def display(request, pageId):
	page = es.get(index="library", doc_type="book", id=pageId)
	
	print "page is %s" % page
	
	# Setup previous and next page values, let template fill in pagination or grey out if at max/min
	if page['_source']['pageNumber'] != 0:
		previousPage = es.search(index="library", body={
														"query" : {
																"filtered" : {
																	"filter" : {
																		"bool": {
																			"must" : [
																				{ "term" : {
																					"parentDocUUID" : page['_source']['parentDocUUID']
																					}},
																				{ "term" : { 
																					"pageNumber":page['_source']['pageNumber']-1
																				}}
																			]
																		}
																	}
																}
															}
														})
	else:
		previousPage = {"hits": {"hits": [{"_id":"#"}]}}			# Basically, set what would have been the object structure up so that the return isnt malformed
	
	nextPage = es.search(index="library", body={
												"query" : {
														"filtered" : {
															"filter" : {
																"bool": {
																	"must" : [
																		{ "term" : {
																			"parentDocUUID" : page['_source']['parentDocUUID']
																			}},
																		{ "term" : { 
																			"pageNumber":page['_source']['pageNumber']+1
																		}}
																	]
																}
															}
														}
													}
												})
	if nextPage["hits"]["total"] == 0:
		nextPage = {"hits": {"hits": [{"_id":"#"}]}}			# Basically, set what would have been the object structure up so that the return isnt malformed
	
	return render(request, 'display.html', { 'username':request.user, 'previousPage':previousPage['hits']['hits'][0]['_id'], 'nextPage':nextPage['hits']['hits'][0]['_id'], 'pageContent':page['_source']['pageContent'], 'pageLocation':os.path.join( str(page["_source"]["location"]), "pages/document-page-"+str(page["_source"]["pageNumber"])+".png")  })

@login_required
def page(request, pageNum):

	query = {
		'query': {
			"query_string" : {
				"query": request.session['currentQuery'],
			}
		},
		"highlight": {
			"preTags" : ["<strong>"],
			"postTags" : ["</strong>"],
			"fields" : {
				"order": "score",
				"pageContent" : {"fragment_size" : "250", "number_of_fragments" : "3"},
			}
		}
	}
	
	hits = es.search(index="library", body=query, size=HITS_PER_PAGE, from_=int(pageNum))
	
	# Pre-process hit list, as _source is a no go for django's templating system
	processedHits = []
	for hit in hits["hits"]["hits"]:
		processedHits.append({ 'pageId':hit["_id"], 'source':hit["_source"], 'highlight':hit["highlight"] })
	
	return render(request, 'page.html', {'username':request.user, 'hits':processedHits, 'numPages':pageNum })