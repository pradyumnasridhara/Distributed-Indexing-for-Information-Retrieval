from __future__ import print_function
from flask import Flask, json, jsonify, abort, make_response, request, url_for
from flask_cors import CORS
from datetime import datetime
from flask import render_template
import operator
import sys
import requests
import threading

from vector_space import do_query

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

@app.route('/retrieve', methods=['POST'])
def retrieve():
	if not request.json:
		abort(400)

	if not request.json["query"]:
		abort(400)

	if not request.json["k"]:
		abort(400)

	result = {}
	# TODO invoke IR model and get top k results as {docName: similarityScore} and return
	k = request.json["k"]
	query = request.json["query"]

	result = do_query(query, k)

	response = app.response_class(
		response = json.dumps(result),
		status = 200,
		mimetype = 'application/json'
	)
	return response

@app.route('/getdocument/<string:docName>', methods=['GET'])
def getDocument(docName):

	print("DOCNAME: ", docName)

	docName = docName.replace("+", "/")

	f = open(docName, "r")
	s = f.read()
	f.close()

	return s.replace("\n", "<br>")

@app.route('/getmodel', methods=['GET'])
def getModel():
	result = {"model": "VectorSpaceModel"}	# make this non-hardcoded (or maybe not)

	response = app.response_class(
		response = json.dumps(result),
		status = 200,
		mimetype = 'application/json'
	)
	return response

@app.route('/getevalscore', methods=['GET'])
def getEvalScore():
	result = {"score": 1.0}	# make this non-hardcoded (or maybe not)

	response = app.response_class(
		response = json.dumps(result),
		status = 200,
		mimetype = 'application/json'
	)
	return response

if __name__ == '__main__':
	# os.chdir("./server1/fileserver")
	app.run(threaded=True, debug=True, host='0.0.0.0', port=83)