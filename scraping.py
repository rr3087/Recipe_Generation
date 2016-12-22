from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import scrapy
import sys
import time
import csv
import lxml.html
import unicodedata
import time
import numpy as np
import pymongo
import pandas as pd
import re

## Data Scraping

def recipe_list(br):
	for page in np.arange(1, 3000):
		print page
		br.get('http://allrecipes.com/recipes/?grouping=all&page=' + str(page))
		section = br.find_element_by_id("grid")
		urls = section.find_elements(By.CLASS_NAME, "favorite")
		id = []
		for i, e in enumerate(urls):
			id.append(e.get_attribute('data-id'))	
			urls[i] = 'https://allrecipes.com/recipe/' + str(id[i])

		urls = np.unique(urls)
		id = np.unique(id)
		for i, url in enumerate(urls):
			br.get(url)
			scrape_recipe(br, id[i])

def scrape_recipe(br, idnumber):
	## recipe info
	try:
		rtitle = br.find_element_by_tag_name('h1').text
	except:
		rtitle = 'NA'
	
	# xpath: locate elements in XML
	try:
		br.find_element_by_xpath('//div[contains(@class,"ui-dialog") and @aria-describedby="dialogContent2"]//button[@title="Close"]').click()
	except:
		print 'no popup'

	try:
		starrating = br.find_element_by_class_name('rating-stars').get_attribute('data-ratingstars')  #unicode
	except:
		starrating = 'NA'
		
	# ignore unpopular recipes 
	try:
		madeitcount = br.find_element_by_class_name('made-it-count').text
		if int(madeitcount) < 5:
			print 'unpopular recipe'
			return
	except:
		return
			
	try:
		totalTime = br.find_element_by_xpath('//time[@itemprop = "totalTime"]').text
	except:
		totalTime = 'NA'
		
	recoutput = idnumber+'\t'+rtitle+'\t'+starrating+'\t'+madeitcount+'\t'+totalTime
	print recoutput

	## ingredient info
	try:
		ingred = br.find_elements_by_class_name("checkList__item")
		ingredients = []
		print "Number of ingredients: %d" % (len(ingred)-1)
		for x in np.arange(len(ingred)-1):     #return an array
			ingredients.append(str(ingred[x].text.encode('utf8', 'ignore')))
		listingr = []
		for ingr in ingredients:
			listingr.append(ingr)
	except:
		listingr = []

	ingroutput = '\n'.join(listingr)
	#print ingroutput + '\n'

	## cooking directions
	try:
		directions = br.find_element_by_class_name("recipe-directions__list")
		direction = str(directions.text.encode('utf8', 'ignore'))
	except: 
		direction = ''
	
	recipe = {'id': idnumber, 'title': rtitle.encode('utf8', 'ignore'), 'rating': starrating, 'made_it_count': madeitcount, 'time': totalTime}
	ingred = {'id': idnumber, 'ingredient': listingr, 'direction': direction}
	collection1.insert(recipe)
	collection2.insert(ingred)

if __name__ == '__main__':

	## Store data in MongoDB
	try:
		connection = pymongo.MongoClient()
		print "Connected successfully!!!"
	except pymongo.errors.ConnectionFailure, e:
		print "Could not connect to MongoDB: %s" % e 

	db = connection['allrecipes']
	collection1 = db['recipes']
	collection2 = db['ingredients']
	
	browser = webdriver.Chrome("/Users/Jiajia/Downloads/chromedriver")
	recipe_list(browser) 

	## General data cleaning

	df1 = pd.DataFrame(list(collection1.find()))
	df1 = df1.set_index('id')
	df2 = pd.DataFrame(list(collection2.find()))
	df2 = df2.set_index('id')

	#convert times to minutes
	def convtomin(time):
	    if time == 'NA':
	        return ''
	    if re.search('d', time):
	        days = int(re.findall('(\d+) d', time)[0])
	    else:
	        days = 0
	    if re.search('h', time):
	        hours = int(re.findall('(\d+) h', time)[0])
	    else:
	        hours = 0    
	    if re.search('m', time):
	        minutes = int(re.findall('(\d+) m', time)[0])
	    else:
	        minutes = 0
	    return minutes + hours*60 + days*60*24

	#convert made it counter from units of K's into thousands
	def convcount(madecount):
		if madecount == 'NA':
			return ''
		if re.search('K', madecount):
			madecount = re.sub('K', '000', madecount)
		return int(madecount)
  
	#convert counter from K's to thousands and convert times into minutes
	df1.made_it_count = map(convcount, df1.made_it_count)
	df1.time = map(convtomin, df1.time)

	df = pd.merge(df1.iloc[:, 1:], df2.iloc[:, 1:], right_index=True, left_index=True)
	#remove duplicates
	df = df.groupby(level=0).last()
	#remove unpopular recipes
	df = df[df.made_it_count >= 5]

	#remove line breaks and useless punchmarks
	def clean_word(w):
		w = re.sub("\,|\.|\;|\:|\;|\?|\!|\[|\]|\}|\{|\(|\)", "", w)
		return re.sub(" and | or | with ", ", ", w)

	for index, row in df.iterrows():
		row['direction'] = ' '.join(row['direction'].splitlines())
		row['direction'] = clean_word(row['direction'])
		row['ingredient'] = [clean_word(i) for i in row['ingredient']]
		row['ingredient'] = ', '.join(row['ingredient'])
		
	df['rating'] = df['rating'].convert_objects(convert_numeric=True)
	print df['rating'].mean()

	df.to_csv('Recipes.csv', encoding='utf8')


