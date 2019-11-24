import os
import re
import pickle
import math
from pprint import pprint, pformat
from nltk.stem.porter import *
from nltk.corpus import stopwords
import time

def read_documents(path):
	for fname in os.listdir(path):
		if(fname.endswith("txt")):
			f = open(path + "/" + fname)
			s = f.read()
			yield s,fname
			f.close()

def clean(text, stemmer):
	#sanitize - removes newlines, extra spaces and all characters except numbers and alphabets
	text = re.sub("[^A-Za-z0-9]", " ", text)
	text = re.sub("\s\s+", " ", text)

	english = stopwords.words('english')
	stopped = []
	for i in text.split(" "):
		x = i.lower()
		if x not in english:
			stopped.append(stemmer.stem(x))

	return stopped

def create_index(path, stemmer, pickle_path):
	#index => (doc) -> [term-> tf-idf, term2 -> tf-idf, (...)]
	index = {}
	id_to_doc = []
	doc_lengths = {}
	idf = {}

	doc_id = 0
	for text,fname in read_documents(path):
		id_to_doc.append(path + "/" + fname)
		stopped = clean(text, stemmer)
		stopped_length = len(stopped)
		index[doc_id] = {}
		for term in set(stopped):
			index[doc_id][term] = stopped.count(term)/stopped_length
			if term not in idf:
				idf[term] = 0
			idf[term] += 1
		doc_id += 1
		print("Processing", fname)

	#compute actual idf
	for term in idf:
		idf[term] = 1 + math.log((doc_id+1)/idf[term])

	for doc in index:
		doc_lengths[doc] = 0
		for term in index[doc]:
			index[doc][term] *= idf[term]
			doc_lengths[doc] += index[doc][term]**2
		doc_lengths[doc] = doc_lengths[doc]**0.5

	with open(pickle_path, "wb+") as pkle:
		pickle.dump({"index" : index, "id_to_doc" : id_to_doc, "doc_lengths": doc_lengths, "idf": idf}, pkle, protocol=pickle.HIGHEST_PROTOCOL)

	# f = open("./out/vector_idf.txt", "w+")
	# f.write(pformat(idf))
	# f.close()

	return index, id_to_doc, doc_lengths, idf

def search(query, k, index, id_to_doc, idf, doc_lengths, stemmer):
	query = clean(query, stemmer)
	query_index = {}
	len_query = len(query)
	query_length = 0
	cosine_similarity = {}

	for term in set(query):
		if term not in idf:
			query_index[term] = 0
		else:
			query_index[term] = (query.count(term) / len_query) * idf[term]
		query_length += query_index[term]**2
	query_length = query_length**0.5
	
	for doc in index:
		cosine_similarity[doc] = 0
		for term in query:
			if term in index[doc]:
				cosine_similarity[doc] += query_index[term] * index[doc][term]

		dinom = doc_lengths[doc] * query_length
		if dinom == 0:
			cosine_similarity[doc] = -1
		else:
			cosine_similarity[doc] = cosine_similarity[doc] / dinom
	
	results = []
	for doc_id in sorted(cosine_similarity, key=lambda x : cosine_similarity[x], reverse=True)[:k]:
		results.append((id_to_doc[doc_id], cosine_similarity[doc_id]))
		# results.append(id_to_doc[doc_id])
	
	return results

def query_from_file(path):
	f = open(path)
	for i in f.read().split("\n"):
		yield i
	f.close()

def do_query(query, k=3):
	# os.chdir("./server1/fileserver")
	path = "data"
	pickle_path = "pkle.pickle"
	stemmer = PorterStemmer()
	# k = 2

	indexing_time = 0
	search_time = 0

	if os.path.isfile(pickle_path):
		with open(pickle_path, "rb") as input_file:
			d = pickle.load(input_file)
			index, id_to_doc, doc_lengths, idf = d["index"], d["id_to_doc"], d["doc_lengths"], d["idf"]
		print("Index loaded from", pickle_path)
	else:
		print("Building index...")
		indexing_time = time.time()
		index, id_to_doc, doc_lengths, idf = create_index(path, stemmer, pickle_path)
		indexing_time = time.time() - indexing_time
	
	results = search(query, k, index, id_to_doc, idf, doc_lengths, stemmer)
	formatted_results = [i for i in results if i[1] > 0]

	pprint(formatted_results)
	return formatted_results

if __name__ == '__main__':
	do_query("Membership is not closed", 10)