import re
import os
import math
import pickle
import operator
from glob import glob
from pprint import *
from nltk.corpus import stopwords
from nltk.stem import *

def clean(text):
	text = re.sub("[^A-Za-z0-9]", " ", text)
	text = re.sub("\s\s+", " ", text)

	# stemmer = SnowballStemmer('english')
	lm = WordNetLemmatizer()
	english = stopwords.words('english')
	stopped = []
	for i in text.split(" "):
		x = i.lower()
		if x not in english and x:
			# stopped.append(stemmer.stem(x))
			stopped.append(lm.lemmatize(x))

	return stopped

def index_corpus(path, pickle_path):
	tf = {}
	idf = {}
	doc_ids = []
	doc_lengths = []
	total_docs = len(glob(path + "/*"))

	# for each file, generate word -> doc-> frequency
	for file in glob(path + "/*"):
		f = open(file, "r")
		text = clean(f.read())
		file = file.replace("\\", "/")
		doc_ids.append(file)
		fileid = doc_ids.index(file)

		doc_lengths.append(len(text))

		for word in text:
			if word in tf:
				if fileid in tf[word]:
					tf[word][fileid] += 1
				else:
					tf[word][fileid] = 1
			else:
				tf[word] = {}
				tf[word][fileid] = 1
	
	# calculate idf
	for word in tf:
		idf[word] = len(tf[word])
	for word in idf:
		idf[word] = math.log(total_docs - idf[word] + 0.5) / (idf[word] + 0.5)

	avg_doc_length = sum(doc_lengths) / len(doc_lengths)

	result = {
		"tf" : tf,
		"idf": idf,
		"doc_ids": doc_ids,
		"total_docs": total_docs,
		"doc_lengths": doc_lengths,
		"avg_doc_length": avg_doc_length
	}

	open("index.txt", "w").write(pformat(result))
	with open(pickle_path, "wb+") as pkle:
		pickle.dump(result, pkle, protocol=pickle.HIGHEST_PROTOCOL)

	return result

def bm25(query, corpus_index):
	scores = {}
	query = clean(query)
	print("Cleaned query:", query)

	k = 1.5
	b = 0.75
	
	tf =  corpus_index["tf"]
	idf =  corpus_index["idf"]
	doc_ids =  corpus_index["doc_ids"]
	total_docs =  corpus_index["total_docs"]
	doc_lengths =  corpus_index["doc_lengths"]
	avg_doc_length =  corpus_index["avg_doc_length"]

	initial_docs = []
	for word in query:
		if word in tf:
			initial_docs.extend(tf[word].keys())
	initial_docs = set(initial_docs)

	for doc_id in initial_docs:
		total = 0
		for word in query:
			if word not in tf or doc_id not in tf[word]:
				continue
			numer = tf[word][doc_id] * (k + 1) * idf[word]
			denom = tf[word][doc_id] + k * (1 - b + b * (doc_lengths[doc_id] / avg_doc_length))
			total += numer / denom
		scores[doc_ids[doc_id]] = total

	results = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)
	return results

def do_query(query, k=3):
	# os.chdir("./server2/fileserver")
	path = "data"
	pickle_path = "pkle.pickle"
	# query = "preliminary software design"

	if not os.path.isfile(pickle_path):
		corpus_index = index_corpus(path, pickle_path)
		print("Pickled...")
	else:
		with open(pickle_path, "rb") as pkle:
			corpus_index = pickle.load(pkle)
		print("Loaded from pickle...")
	
	results = bm25(query, corpus_index)
	formatted_results = [i for i in results[:k] if i[1] != 0]

	pprint(formatted_results)
	return formatted_results

if __name__ == "__main__":
	do_query("Membership is not closed", 10)
