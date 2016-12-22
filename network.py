import pandas as pd
import numpy as np
import re
import csv
from math import log
from decimal import Decimal
from ast import literal_eval
from pattern.en import singularize, pluralize

nodeDF = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/Nodes.csv", header=None, names=['ingredients'])
recDF = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/Clean_recipes.csv", header=None, names=['ingredients'])
n = nodeDF.count()['ingredients']    ## n = 2174
m = recDF.count()['ingredients']    ## m = 27341
prob_ingr = np.zeros(n)

## Compute probability of each ingredient
recDF['ingredients'] = recDF['ingredients'].str.lower()

location = []
for i, ingr in nodeDF.iterrows():
	count = 0
	occur = []
	for r, recp in recDF.iterrows():
		if ingr['ingredients'] in recp['ingredients'] or (pluralize(ingr['ingredients']) in recp['ingredients']):
			count += 1
			occur.append(r)
	if count == 0:
		print "Error: %d, %s" % (i, ingr)
	else:
		prob_ingr[i] = count*1.0 / m
		location.append(occur)

with open('prob.csv', 'wb') as myfile:
	wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
	for prob in prob_ingr:
		wr.writerow([prob])

with open('location.csv', 'wb') as myfile:
	wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
	for loc in location:
		wr.writerow([loc])


## Compute PMI and Generate Edges, threshold = 0.05
position = []
with open('/Users/Jiajia/Google Drive/Columbia/Big Data/location.csv', 'rb') as f:
    reader = csv.reader(f)
    for row in reader:       # each row is read as a list
    	position.append(literal_eval(row[0]))

prob = []
with open('/Users/Jiajia/Google Drive/Columbia/Big Data/prob.csv', 'rb') as f:
    reader = csv.reader(f)
    for row in reader:
    	prob.append(Decimal(row[0]))

PMI = np.empty([n, n])
edges = []
for i in range(n-1):
	for j in range(i+1,n):
		common = len(set(position[i]) & set(position[j]))
		jointprob = Decimal(common) / Decimal(m)
		if jointprob != 0:
			PMI[i][j] = log(jointprob/(prob[i] * prob[j]))
			PMI[j][i] = PMI[i][j]
			if PMI[i][j] > 0.05:		
				edges.append({'source':i, 'target':j})
for k in range(n):
	PMI[k][k] = -log(prob[k])

np.save('PMImatrix.npy', PMI)

edgeDF = pd.DataFrame(edges)
edgeDF.to_csv('Edges.csv', index=False, header=False)




