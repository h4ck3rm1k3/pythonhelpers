# -*- coding: utf-8 -*-
"""
Created on Sat Feb 27 10:20:14 2016

@author: aedouard
"""


from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import os
import string 
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import SnowballStemmer
#MongoHelper.connect("tweets_dataset")

def tokenize(text):
    text = text.lower().translate(string.punctuation)
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(text)
    stems = []
    for item in tokens:
        stems.append(SnowballStemmer('english').stem(item))
    return stems
    """
    tokens = nltk.word_tokenize(text)
    stems = []
    for item in tokens:
        stems.append(PorterStemmer().stem(item))
    return stems
    """


def preprocess(sentence):
    stems = tokenize(sentence)
    filtered_words = [w for w in stems if len(w)> 2 and not w in stopwords.words('english')]
    return " ".join(filtered_words)


def tfidf(token_dict, sentence):
    tfidf = TfidfVectorizer(tokenizer=tokenize, stop_words='english')
    tfs = tfidf.fit_transform(token_dict.values())
    response = tfidf.transform([sentence])
    print (response)
    feature_names = tfidf.get_feature_names()
    for col in response.nonzero()[1]:
        print (feature_names[col], ' - ', response[0, col]) 


