# Recipe_Generation

This is a project for Big Data Analytics at Columbia University.

## Project Overview
Recipe recording and sharing has been around for many years. Recipe collections containing ingredient combinations yield information about cooking fundamentals and user preferences. We construct an ingredient network to study the importance of each ingredient, capture the relationships between ingredients and explore reasonable combinations. We also perform experiments, to predict ratings of newly generated recipes using features derived from the network and accordingly suggest the recipes to the user. 

## Package Description
We provided python implementation for our recipe generator. To be able to run the package, one need to first download the pre-stored file containing cliques (clique.csv), nodes (Nodes.csv) and edges (Edges.csv), pre-trained boosted tree model (SGBT directory), and network features (features.csv, SVDfactor.npy). Users can then run the python script generator.py to see the results.

generator.py: this is the script to 


Users are first asked to input one or two ingredients they would like to try (separated by comma and no space allowed after the comma). If they are not satisfied with the suggested recipe, a new recipe will be generated until the generator produces one that the users like. If the user input consists of unusual ingredient combinations that are considered unachievable as stated in section 4.4 (2), users will be asked to input another set of ingredients. 
