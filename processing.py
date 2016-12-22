import findspark
findspark.init()

from pyspark import SparkContext, SparkConf
from pyspark import RDD
from pyspark.sql import SparkSession, SQLContext
from pyspark.sql.types import *
from pyspark.sql.functions import udf, lower, col, split
from pyspark.ml.feature import Tokenizer, RegexTokenizer, StopWordsRemover, NGram
from pyspark.ml.feature import HashingTF, IDF, CountVectorizer
import pandas as pd
import re
import csv
from nltk.corpus import stopwords
from nltk import pos_tag, word_tokenize
from nltk.stem.porter import *

conf = SparkConf().setAppName("PySpark Recipe Generation Project")
sc = SparkContext(conf=conf)

spark = SparkSession \
    .builder \
    .appName("PySpark Recipe Generation Project") \
    .config("spark.some.config.option", "some-value") \
    .getOrCreate()

schema = StructType([
    StructField("id", IntegerType()),
    StructField("made_it_count", IntegerType()),
    StructField("rating", DoubleType()),
    StructField("time", IntegerType()),
    StructField("title", StringType()),
    StructField("direction", StringType()),
    StructField("ingredient", StringType())
])

df = spark.read.csv("/Users/Jiajia/Google Drive/Columbia/Big Data/Recipes.csv", header=True, schema=schema)
#print df.count()
#df.printSchema()
#df.show()
df.ingredient = df.select(split(df.ingredient, ',').alias('ingredient'))     
df.ingredient = df.select(lower(df.ingredient).alias('ingredient'))

## Identify Ingredients
# units: http://www.recipetips.com/kitchen-tips/t--482/units-of-measure.asp
stemmer = PorterStemmer()
units = ['tsp','teaspoon','cup','gill','drop','tbsp','tablespoon','pt','pint','dash',
		'oz','ounce','fl oz','fluid','qt','quart','gram','gal','gallon','lb','pound',
		'pottle','peck','bushel','pinch','degrees F','degrees C','inch','package', 
		'piece','can','bunch','jar','liter','milliliter','bottle']
units = [stemmer.stem(i) for i in units]

# keep only nouns and adjectives
recingr = []
for ingrow in df.select('ingredient','id').collect(): 
	try:
		ingred = ingrow.ingredient
		print ingred
		text = word_tokenize(ingred)
		tagged = pos_tag(text)
		newingred = ' '.join([i[0] for i in tagged if i[1] in ['NN','NNS','NNPS','NNP','JJ',',']])
		newingred = re.sub(r'(\d+)|(\d*/?\d*)', '', newingred)
		newingred = ' '.join([i for i in newingred.split(' ') if stemmer.stem(i) not in units])	
		inglist = newingred.split(',')
		inglist = [i.strip(' ') for i in inglist]
		recingr.append(inglist)
	except:
		continue

# remove empty strings in the ingredient list
recingr_new = []
pureingr = []
for ingl in recingr:
	for ing in ingl:
		if ing != '':
			pureingr.append(ing)
		else:
			ingl.remove(ing)
	newingl = ','.join(ingl).encode('utf8')
	recingr_new.append(newingl)


## Wordcount for Ingredients
ingRDD = sc.parallelize(pureingr)
ingCount = ingRDD.map(lambda x: (x,1)).reduceByKey(lambda x,y: x+y).map(lambda (k,v): (v,k)).sortByKey(False)

## Select Top 3K Nodes Appearing over 3 times among the recipes
popCount = ingCount.collect()[0:3000]
popingr = [i[1].encode('utf8') for i in popCount if i[0] > 2]   

with open('raw_nodes.csv', 'wb') as myfile:
	wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
	for node in popingr:
		wr.writerow([node])

with open('recipe_ingred.csv', 'wb') as myfile2:
	wr2 = csv.writer(myfile2, quoting=csv.QUOTE_ALL)
	for row in recingr_new:
		wr2.writerow([row])
		
		
## Futher Cleaning (part of ingredients were manually selected/removed)
nodeDF = pd.read_csv("/Users/Jiajia/Google Drive/Columbia/Big Data/raw_nodes.csv", header=None, names=['ingredients'])

# remove irrelevant words not detected in previous steps
anywhere = ['miniature','halves','solid pack','optional','container','skewer']
for i in range(nodeDF.count()):
	nodeDF.ingredients.iloc[i] = re.sub('(%s)' % '|'.join(anywhere), '', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('\s{2,}', ' ', nodeDF.ingredients.iloc[i]).strip(' ')	

# convert all words to singular form; modify mis-converted words
for i in range(nodeDF.count()):
	nodeDF.ingredients.iloc[i] = singularize(nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('olife', 'olive', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('flmy', 'flour', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('pastum', 'pasta', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('spaghettus', 'spaghetti', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('tamarus', 'tamari', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('Velveetum', 'Velveeta', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('fetum', 'feta', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('Vidalium', 'Vidalia', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('gras', 'grass', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('asparaguss', 'asparagus', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('chily', 'chile', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('polentum', 'polenta', nodeDF.ingredients.iloc[i])
	nodeDF.ingredients.iloc[i] = re.sub('pancettum', 'pancetta', nodeDF.ingredients.iloc[i])

# convert ingredients to lower case and remove duplicates
nodeDF['ingredients'] = nodeDF['ingredients'].str.lower()
nodeDF = nodeDF.drop_duplicates()
nodeDF.index = range(nodeDF.count())

nodeDF.to_csv('Nodes.csv', encoding='utf8', index=True, header=False)


