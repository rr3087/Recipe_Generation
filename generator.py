import pandas as pd
import numpy as np
import re
import json
from pattern.en import singularize, pluralize
import networkx as nx
from itertools import *

from pyspark import SparkContext, SparkConf
from pyspark.mllib.tree import GradientBoostedTrees, GradientBoostedTreesModel
from pyspark.mllib.util import MLUtils


def double_check(w):
	for i in nodeDF['ingredients'][nodeDF['ingredients'].str.contains(w)]:
		print "Regarding '%s', do you mean '%s'? (yes or no)" % (w, i)
		answer = raw_input(prompt)
		if answer == "yes":
			return nodeDF[nodeDF['ingredients'] == i].index.tolist()


def reader(w):
	''' look up user input in the ingredient list '''
	specials = ['olive', 'flour', 'pasta', 'spaghetti', 'tamari', 'Velveeta', 
				'feta', 'Vidalia', 'grass', 'asparagus', 'chile']
	if w in specials:
		id = nodeDF[nodeDF['ingredients'] == w].id.tolist()
	else:
		id = nodeDF[nodeDF['ingredients'] == singularize(w)].id.tolist()
	
	if id:
		return id[0]
	else:
		id_singular = double_check(singularize(w))
		if id_singular:
			return id_singular[0]
		id = double_check(w)
		if id:
			return id[0]


def get_index(ingredients):
	''' output an index list for all ingredients'''
	index = []
	for ingr in ingredients.split(','):
		id = reader(ingr)
		if id is None:
			print "Sorry! I can't read '%s'." % ingr
			return
		else:
			index.append(id)
	return index


def get_cliques(nodes, cliques):
	#get the maximal cliques for a list of nodes
	vcliques=[c for c in cliques if set(nodes) < set(c)]
	return vcliques


def k_shortest_paths(G, source, target, k):
    return list(islice(nx.shortest_simple_paths(G, source, target), k))


def binary(data): 
	n = nodeDF.count()['ingredients']
	ingFeature = np.zeros(n)
	for ing in data:
		ingFeature[ing] = 1
	#print ingFeature
	return ingFeature


def get_rating(data, model):
	ingFeature = binary(data)
	pmi = np.transpose(np.dot(factor, np.transpose(ingFeature)))
	betweenness = np.dot(ingFeature, np.array(ctrDF['betweenness.centrality'], dtype=pd.Series))
	eigenvector = np.dot(ingFeature, np.array(ctrDF['eigen.centrality'], dtype=pd.Series))

	features = [betweenness, eigenvector]
	features.extend(pmi)

	data = sc.parallelize(features)
	predictions = model.predict(data.map(lambda x: x.features)).collect()
	return predictions


def clean_output(clist):

	print "Check out this recipe: "
	print "***********************"
	recipe = nodeDF['ingredients'][clist].tolist()
	history = []
	for i in range(len(recipe)):
		if recipe[i] not in history:
			synonym = [recipe[i]]
			for j in range(i+1,len(recipe)):
				if any((recipe[j] in x) | (x in recipe[j]) for x in synonym):
					synonym.append(recipe[j])
			if len(synonym) > 1:
				print " or ".join(synonym)	
				history.extend(synonym)
		
	for ingr in recipe:
		if ingr not in history:
			print ingr

	print "Do you like this recipe? (yes or no)"
	

def Generator(nodes):
	# no such ingredients
	if not nodes: 
		return

	clist = get_cliques(nodes, cliques)

	# novel combinations: the combination does not form a clique
	if not clist:		
		for i in range(len(nodes)-1):
			pathlist = k_shortest_paths(G, source=nodes[i], target=nodes[i+1], k=100)
			# keep paths with length <= 3
			for path in pathlist:
				if len(path) > 3:
					pathlist.remove(path)
			if len(pathlist) == 0:
				print "Oops! That doesn't look like a good combination."
				return

			midnodes = [p[1] for p in pathlist]

			count = 0
			while True:
				r = np.random.randint(0, len(pathlist))
				subset = [nodes[0], midnodes[r]]
				subclist = get_cliques(subset, cliques)

				if (not subclist) or (count == 5):
					print "Sorry we can't find a recipe you like."
					return
				count += 1

				k = np.random.randint(0, len(subclist))
				cintsc = list(set(subclist[k]) & set(midnodes))

				for i in range(len(nodes)):					
					cintsc.append(nodes[i])
	
				rating = get_rating(cintsc, model)
				print rating
				#if rating < 4.3:
				#	continue

				# output recipes with ratings >= 4.3
				clean_output(cintsc)

				fdback = raw_input(prompt)
				if fdback == "yes":						
					print "Yay!"
					return

	# common combinations
	else:
		while True:
			r = np.random.randint(0, len(clist))
			rdclique = clist[r]

			rating = get_rating(rdclique, model)
			print rating
			if rating < 4.3:
				continue

			clean_output(rdclique)
			

			fdback = raw_input(prompt)
			if fdback == "yes":
				print "Yay!"
				return
		
			
if __name__ == '__main__':
	
	print "Initializing ..."	

	nodeDF = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/Nodes.csv", header=None, names=['id','ingredients'])
	factor = np.load('SVDfactor_k60.npy')
	ctrDF = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/features.csv")
	G = nx.read_weighted_edgelist("Edges.csv", delimiter=',', create_using=nx.Graph(), nodetype=int)
	#print nx.info(G)
	
	#cliques = list(nx.find_cliques(G))
	#with open("cliques", "w") as f:
	#	json.dump(cliques, f)

	conf = SparkConf().setAppName("PySpark Recipe Generation Project")
	sc = SparkContext(conf=conf)
	model = GradientBoostedTreesModel.load(sc, "SGBT")

	with open("cliques") as f:
		cliques = json.load(f)

	print "Welcome! This is a recipe generator."
	print "What would you like to have today? We create recipes to your taste!"
	
	prompt = "> "
	
	while True:
		print ('Please tell us 1 or 2 ingredients you would like in the recipe, '
			   'seperated by comma (no space after comma):')
		ingred = raw_input(prompt)

		nodes = get_index(ingred)
		Generator(nodes)

		print "Want to try anything else? (yes or no)"	
		repeat = raw_input(prompt)
		if repeat == "no":
			print "Thank you for using this generator!"
			print "Logging out..."
			break

