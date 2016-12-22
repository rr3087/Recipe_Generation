import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv
from math import log
from decimal import Decimal
from ast import literal_eval
from pattern.en import singularize, pluralize

## Feature Selection: Dimension Reduction with SVD 
PMI = np.load('PMImatrix.npy')
U, s, V = np.linalg.svd(PMI, full_matrices=False)
S = np.diag(s)
n = S.shape[0]
total = np.trace(np.linalg.matrix_power(S, 2))

# k = 300, 71% energy retained
k = 300
for i in range(n-k):
	S[n-i-1][n-i-1] = 0
percent = np.trace(np.linalg.matrix_power(S, 2)) / total
print percent

reducedS = S[:k,:k]
reducedV = V[:k, ]
factor = np.dot(np.linalg.inv(reducedS), reducedV)
np.save('SVDfactor_k300.npy', factor)

'''
# plot dimension vs percentage of energy retained
pct = []
s2 = []
for k in np.arange(40, 800, 20): 
	Sigma = S.copy()
	for i in range(n-k):
		Sigma[n-i-1][n-i-1] = 0
	percent = np.trace(np.linalg.matrix_power(Sigma, 2)) / total
	pct.append(percent)
#print pct
#print Sigma
k = np.arange(40, 800, 20)
plt.plot(k, pct, marker='o')
plt.show()
'''

## Incorporate Network Features into Original Dataset
nodeDF = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/Nodes.csv", header=None, names=['id','ingredients'])

occurin = []
with open('/Users/Jiajia/Google Drive/Columbia/Big Data/location.csv', 'rb') as f:
    reader = csv.reader(f)
    for row in reader:       # each row is read as a list
    	occurin.append(literal_eval(row[0]))

# binary representation
recDF = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/Clean_recipes.csv", header=None, names=['ingredients'])
m = recDF.count()['ingredients']    
ingFeature = np.zeros((m, n))
for i in range(n):
	for loc in occurin[i]:
		ingFeature[loc, i] = 1

# centralities
ctrDF = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/features.csv")
betweenness = np.dot(ingFeature, np.array(ctrDF['betweenness.centrality'], dtype=pd.Series))
eigenvector = np.dot(ingFeature, np.array(ctrDF['eigen.centrality'], dtype=pd.Series))

# reduced features: k dimensions
reducedPMI = np.transpose(np.dot(factor, np.transpose(ingFeature)))

colname = ["PMIfeature" + str(i) for i in range(1, k+1)]
featureDF = pd.DataFrame(reducedPMI, columns=colname)
featureDF['btw.centrality'] = pd.Series(betweenness)
featureDF['eigen.centrality'] = pd.Series(eigenvector)

myrecipes = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/Recipes.csv")
myrecipes = myrecipes[['made_it_count', 'rating']]
myrecipes = myrecipes.join(featureDF)
print myrecipes.head(5)

myrecipes.to_csv('features_k300.csv', encoding='utf8')

