# Recipe_Generation

This is a project for Big Data Analytics at Columbia University.

## Project Overview
Recipe recording and sharing has been around for many years. Recipe collections containing ingredient combinations yield information about cooking fundamentals and user preferences. We construct an ingredient network to study the importance of each ingredient, capture the relationships between ingredients and explore reasonable combinations. We also perform experiments, to predict ratings of newly generated recipes using features derived from the network and accordingly suggest the recipes to the user. 

## Data Generation
Data are scaped from Allrecipes.com (http://allrecipes.com/recipes/?grouping=all). Each row contains the following features:
  1. id: ID of the recipe (type: string)
  2. made_it_count: the number of users who have tried the recipe (type: int)
  3. time: the total time needed for the recipe (including preparing and cooking) (type: int)
  4. direction: cooking instructions (type: string)
  5. ingredients: a list of ingredients needed for the recipe (type: list)

To be able to run the scraper, you need to download the following tools:
  1. MongoDB: 
  (i). In terminal:
  brew install mongodb 
  (make sure homebrew is installed first)
  (ii). To start mongodb: 
  Linux: brew services start mongodb;
  Windows: http://stackoverflow.com/questions/20796714/what-is-the-way-to-start-mongo-db-from-windows-7-64-bit
  2. Chromedriver (if you are using Chrome):
  https://chromedriver.storage.googleapis.com/index.html?path=2.25/
  3. Install the following python libraries:
  selenium, pymongo, numpy, pandas


## Dataset
Recipes.csv

## Network Data
Nodes.csv, Edges.csv, features.csv, SVDfactor.npy

## Model
SGBT

## Package Description
We provided python implementation for our recipe generator. To be able to run the package, one need to first download the pre-stored file containing nodes (Nodes.csv) and edges (Edges.csv), pre-trained boosted tree model (SGBT directory), and network features (features.csv, SVDfactor.npy). Users can then run the python script generator.py to see the results.

generator.py: recipe generator
(to speed up, users need to have an initial run of the program to generate clique.json file. For the future runs, users can ingore this step and simply load clique file.)

After the generator is initiated, users will first be asked to input one or two ingredients they would like to try (separated by comma and no space allowed after the comma). If they are not satisfied with the suggested recipe, a new recipe will be generated until the generator produces one that the users like. If the user input consists of unusual ingredient combinations that are considered unachievable as stated in section 4.4 (2), users will be asked to input another set of ingredients. 
