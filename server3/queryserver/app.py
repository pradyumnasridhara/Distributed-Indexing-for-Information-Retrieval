from __future__ import print_function
from flask import Flask, json, jsonify, abort, make_response, request, url_for
from flask_cors import CORS
from datetime import datetime
from flask import render_template
import operator
import sys
import requests
import threading

from voicesearch import doVoiceSearch

app = Flask(__name__)
CORS(app)

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
	return make_response(jsonify({'error': 'Bad request'}), 400)

@app.after_request
def add_header(r):
	""" Disable caching """
	r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
	r.headers["Pragma"] = "no-cache"
	r.headers["Expires"] = "0"
	return r

servers = {}

def getServerList():
	# TODO get list of fileservers or hardcode it

	# serverList = ["localhost", "17.1.1.25", "17.1.1."]
	# serverList = ["localhost:83", "17.1.1.25:83", "17.1.1.:83"]

	serverList = ["localhost:83", "localhost:84", "localhost:85"]
	# serverList = ["localhost:83", "localhost:85"]

	for server in serverList:
		# r = requests.get("http://{}:83/getmodel".format(server))
		r = requests.get("http://{}/getmodel".format(server))
		m = r.json()["model"]
		# r = requests.get("http://{}:83/getevalscore".format(server))
		r = requests.get("http://{}/getevalscore".format(server))
		sc = r.json()["score"]
		servers[server] = {
			"model": m,
			"score": sc
		}


@app.route('/query', methods=['POST'])
def query():
	if not request.json:
		abort(400)

	if not request.json["query"]:
		abort(400)

	if not request.json["k"]:
		abort(400)

	
	queryResults = {}	# serverIP -> [(docName, similarityScore)]

	for server in servers:
		# r = requests.post("http://{}:83/retrieve".format(server), json=request.json)
		r = requests.post("http://{}/retrieve".format(server), json=request.json)
		res = r.json()
		queryResults[server] = res

	k = request.json["k"]
	combinedList = []
	for server,docs in queryResults.items():
		if len(docs) == 0:
			response = app.response_class(
				response = json.dumps([]),
				status = 200,
				mimetype = 'application/json'
			)
			return response
		sMax = max(list(map(operator.itemgetter(1), docs)))
		sMin = min(list(map(operator.itemgetter(1), docs)))
		if sMin == sMax:
			s = servers[server]["score"]
			for doc,score in docs:
				combinedList.append((server, doc, s))
		else:
			for doc,score in docs:
				s = servers[server]["score"] * (score - sMin) / (sMax - sMin)
				combinedList.append((server, doc, s))

	combinedList.sort(key=lambda x: x[2], reverse=True)
	finalResult = []
	for d in combinedList[:k]:
		finalResult.append((str(d[0]), str(d[1]), d[2]))

	result = {}
	result["finalResult"] = finalResult
	result["individualResults"] = queryResults
	
	response = app.response_class(
		response = json.dumps(result),
		status = 200,
		mimetype = 'application/json'
	)
	return response

@app.route('/voicequery', methods=['GET'])
def voiceQuery():
	query = doVoiceSearch()
	while not query:
		query = doVoiceSearch()
	
	result = {"queryString": query}

	response = app.response_class(
		response = json.dumps(result),
		status = 200,
		mimetype = 'application/json'
	)
	return response

@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
@app.route('/index', methods=['GET'])
def showHomepage():
	"""
	Will have a text box to enter query. 
	When QUERY button is clicked, it will make POST call to /query.
	Get response from it.
	
	"""
	return render_template(
		'index.html',
		title='Results',
		year=datetime.now().year,
		message='results.'
	)

if __name__ == '__main__':
	# os.chdir("./server3/queryserver")
	getServerList()
	app.run(threaded=True, debug=True, host='0.0.0.0', port=82)