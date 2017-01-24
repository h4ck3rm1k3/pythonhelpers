# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 16:39:25 2016

@author: aedouard
"""

import csv 
from helper import MongoHelper
from helper import FileHelper
import os
localDirectory = "/Users/aedouard/Documents/these/pipeline/"
MongoHelper.connect("tweets_dataset")
def readModelFile(fileName):
    labels = ['Arts', 'Accidents', 'undefined', 'Politics', 'Attacks', 'Science', 'Sports', 'Miscellaneous', 'Economy']
    query = {'ontology':'dbpedia', 'type':'generic', 'dataset':'fsd'}
    tweets = MongoHelper.find("annotated",0,0,query)
    vals = []
    for tweet in tweets:
        vals.append({'tweet_id' : "'"+str(tweet["tweet_id"])+"'", 'expected':tweet["category"], 'predicted' : '?'})
    print (len(vals))
    with open(localDirectory+fileName) as data:
            lines = csv.reader(data, delimiter=';', quotechar='|')
            result = []
            current = 0
            for line in lines:
                correct = 0
                correct_index = 0
                for index,val in enumerate(labels):
                    if correct < float(line[index]):
                        correct = float(line[index])
                        correct_index = index
                vals[current]["predicted"] = labels[correct_index]
                #result.append(v) 
                current = current + 1
                #print("Correct " + str(correct_index) + " With " + str(correct))
    #print(result)
    
    with open('result.arff', 'w') as f:  # Just use 'w' mode in 3.x
        for res in vals:
                w = csv.DictWriter(f, res.keys())
                w.writerow(res)
        
readModelFile("dbpedia_eval-output_test.csv")







