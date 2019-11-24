import re
import os
import math
import pickle
import operator
from glob import glob
from pprint import *
from nltk.stem import *
from functools import reduce
from nltk.corpus import stopwords

def clean(text):
	text = re.sub("[^A-Za-z0-9]", " ", text)
	text = re.sub("\s\s+", " ", text)

	# stemmer = SnowballStemmer('english')
	lm = WordNetLemmatizer()
	english = stopwords.words('english')
	stopped = []
	for i in text.split(" "):
		x = i.lower()
		if x and x not in english:
			# stopped.append(stemmer.stem(x))
			stopped.append(lm.lemmatize(x))

	return stopped

def compute_index(path, pickle_path):
	V = 0
	doc_ids = []

	#bigrams, unigrams => word(s) -> doc_id -> frequency
	bigrams = {}
	unigrams = {}

	# for each file, generate word -> doc-> frequency
	for doc_id,file in enumerate(glob(path + "/*")):
		f = open(file, "r")
		text = clean(f.read())
		file = file.replace("\\", "/")
		doc_ids.append(file)

		for i,word in enumerate(text):
			if word not in unigrams:
				unigrams[word] = {}
				unigrams[word][doc_id] = 1
			elif doc_id not in unigrams[word]:
				unigrams[word][doc_id] = 1
			else:
				unigrams[word][doc_id] += 1
			if i < len(text) - 1:
				biword = word + " " + text[i+1]
				if biword not in bigrams:
					bigrams[biword] = {}
					bigrams[biword][doc_id] = 1
				elif doc_id not in bigrams[biword]:
					bigrams[biword][doc_id] = 1
				else:
					bigrams[biword][doc_id] += 1

	V = len(unigrams)
	
	result = {
		"V": V,
		"bigrams": bigrams,
		"unigrams": unigrams,
		"doc_ids": doc_ids
	}

	open("index.txt", "w").write(pformat(result))
	with open(pickle_path, "wb+") as pkle:
		pickle.dump(result, pkle, protocol=pickle.HIGHEST_PROTOCOL)

	return result

def ngrams(query, corpus_index):
	query = clean(query)
	V = corpus_index["V"]
	doc_ids = corpus_index["doc_ids"]
	bigrams = corpus_index["bigrams"]
	unigrams = corpus_index["unigrams"]

	probs = {}

	initial_docs = []
	for term in query:
		if term in unigrams:
			initial_docs.extend(list(unigrams[term].keys()))
		for bigram in bigrams:
			if term in bigram:
				initial_docs.extend(list(bigrams[bigram]))
	initial_docs = set(initial_docs)

	for doc_id in initial_docs:
		p = 0
		for i,term in enumerate(query[1:]):
			biword = query[i] + " " + term
			if biword in bigrams and doc_id in bigrams[biword]:
				p += math.log((bigrams[biword][doc_id] + 1) / (unigrams[term][doc_id] + V))
		probs[doc_ids[doc_id]] = -1/p if p != 0 else 0

	results = sorted(probs.items(), key=operator.itemgetter(1), reverse=True)

	return results

def do_query(query, k=3):
	# os.chdir("./server3/fileserver")
	path = "data"
	pickle_path = "pkle.pickle"

	if not os.path.isfile(pickle_path):
		corpus_index = compute_index(path, pickle_path)
		print("Pickled...")
	else:
		with open(pickle_path, "rb") as pkle:
			corpus_index = pickle.load(pkle)
		print("Loaded from pickle...")

	open("index.txt", "w").write(pformat(corpus_index))
	results = ngrams(query, corpus_index)
	formatted_results = [i for i in results[:k] if i[1] != 0]

	pprint(formatted_results)
	return formatted_results

if __name__ == '__main__':
	do_query("operating systems", 4)