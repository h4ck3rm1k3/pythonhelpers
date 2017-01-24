# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 17:00:14 2016

@author: aedouard
"""

"""
This script is what created the dataset pickled.

1) You need to download this file and put it in the same directory as this file.
https://github.com/moses-smt/mosesdecoder/raw/master/scripts/tokenizer/tokenizer.perl . Give it execution permission.

2) Get the dataset from http://ai.stanford.edu/~amaas/data/sentiment/ and extract it in the current directory.

3) Then run this script.
"""


import numpy
import MongoHelper
import cPickle as pkl
import numpy as np
import re
import csv
from collections import OrderedDict

import glob
import os


from subprocess import Popen, PIPE

#{'ontology':'dbpedia_yago', 'type':'generic', 'name':'dbpedia_yago_generic'}, 
#{'ontology':'dbpedia_yago', 'type':'specific','name':'dbpedia_yago_specific'}, 
# tokenizer.perl is from Moses: https://github.com/moses-smt/mosesdecoder/tree/master/scripts/tokenizer
tokenizer_cmd = ['/Users/aedouard/Documents/_dev/these/preprocessing/tokenizer.perl', '-l', 'en', '-q', '-']
sentence_length = 0
vocab_size = 0
setting1 = 'event 2012'
setting2 = 'fsd'
params = [
        {'ontology':'dbpedia', 'type':'normal', 'name':'dbpedia_baseline_2_classes'}, 
        {'ontology':'dbpedia', 'type':'generic', 'name':'dbpedia_generic_2_classes'}, 
        {'ontology':'dbpedia', 'type':'specific', 'name':'dbpedia_specific_2_classes'}, 
        {'ontology':'yago', 'type':'generic', 'name':'yago_generic_2_classes'}, 
        {'ontology':'yago', 'type':'specific', 'name':'yago_specific_2_classes'}, 
        {'ontology':'dbpedia_yago', 'type':'generic', 'name':'dbpedia_yago_generic_2_classes'}, 
        {'ontology':'dbpedia_yago', 'type':'specific', 'name':'dbpedia_yago_specific_2_classes'}, 
    ]
def clean_string(string):
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)

    return string.strip().lower()


def pad_sentences(sentences, sentence_length=None, dtype=np.int32, pad_val=0.):
    lengths = [len(sent) for sent in sentences]

    nsamples = len(sentences)
    if sentence_length is None:
        sentence_length = np.max(lengths)

    X = (np.ones((nsamples, sentence_length)) * pad_val).astype(dtype=np.int32)
    for i, sent in enumerate(sentences):
        trunc = sent[-sentence_length:]
        X[i, -len(trunc):] = trunc
    return X

def tokenize(sentences):
    
    print ('Tokenizing..')
    text = "\n".join(sentences)
    #text = clean_string(text)
    text = text.encode(encoding='utf-8')#('utf-8')
    tokenizer = Popen(tokenizer_cmd, stdin=PIPE, stdout=PIPE)
    tok_text, _ = tokenizer.communicate(text)
    tok_text = tok_text.decode(encoding='utf-8')
    toks = tok_text.split('\n')[:-1]
    
    return toks


def build_dict(sentences):
    global sentence_length
    ##sentences = tokenize(sentences)
    lengths = [len(sent) for sent in sentences]
    sentence_length = np.max(lengths)
    print('Building dictionary..')
    wordcount = dict()
    for ss in sentences:
        words = ss.strip().split()
        for w in words:
            if w not in wordcount:
                wordcount[w] = 1
            else:
                wordcount[w] += 1

    counts = list(wordcount.values())
    keys = list(wordcount.keys())

    sorted_idx = numpy.argsort(counts)[::-1]

    worddict = dict()

    for idx, ss in enumerate(sorted_idx):
        worddict[keys[ss]] = idx+9  # leave 0 and 1 (UNK)
    global vocab_size    
    vocab_size = len(keys)
    print(numpy.sum(counts), ' total words ', len(keys), ' unique words')

    return worddict


def grab_data(sentences, dictionary):
    #sentences = tokenize(sentences)
    seqs = [None] * len(sentences)
    for idx, ss in enumerate(sentences):
        words = ss.strip().split()
        seqs[idx] = [dictionary[w] if w in dictionary else 1 for w in words]
    return seqs
    #return pad_sentences(seqs, sentence_length=sentence_length)

def builtModelForTest(config):
    f = open('{0}_dict_{1}.pkl'.format(setting1.replace(' ', '_'), config['name']), 'rb') 
    dictionary = pkl.load(f)
    data = initData()
    loadTweets({'ontology':config['ontology'], 'type':config['type'], 'dataset':setting2}, data)
    saveModel(data, config, dictionary, 'test')
    
def buildModelForTrain(config):
    data = initData()
    sentences = loadTweets({'ontology':config['ontology'], 'type':config['type'], 'dataset':setting1}, data)
    dictionary = build_dict(sentences)
    #dump the dictionnary 
    f = open('{0}_dict_{1}.pkl'.format(setting1.replace(' ', '_'),config['name']), 'wb')  
    pkl.dump(dictionary, f, -1)
    f.close();
    saveModel(data, config, dictionary, 'model')


def initData():
    data = {
    "positive" : [],
    "negative": [],
    };
    return data

def loadTweets(query, data):
    tweets = MongoHelper.find("annotated",0,0,query)
    sentences = []
    print ("QT", tweets.count())
    for tweet in tweets:
        category = 'negative' if tweet['category']=='undefined' else 'positive' 
        data[category].append(clean_string(tweet["text_snowball"]))
        sentences.append(clean_string(tweet["text_snowball"]))
    return sentences

def saveModel(data, config, dictionary, _type):
    train_x = None 
    train_y = None
    i=0;
    for key in data.keys():
        i = i +1
        if(len(data[key]) == 0):
            continue
        x = grab_data(data[key], dictionary)
        y = [i-1] * len(x)
        if train_x is None:
            train_x = x
            train_y = y
        else:
            train_y =  train_y + y
            train_x =  train_x + x
        
    print ('number of class', i)
    config['sentence_length']= sentence_length 
    config['vocab_size']= vocab_size
    _set = setting1 if _type == 'train' else setting2
    f = open('{0}_{1}.pkl'.format(_type, config['name']), 'wb')   
    pkl.dump((train_x, train_y), f, -1)
    f.close()
        
def main():
    # Get the dataset from http://ai.stanford.edu/~amaas/data/sentiment/
    MongoHelper.connect("tweets_dataset")
    for config in params:
       buildModelForTrain(config)
       builtModelForTest(config)
        
        
    """
    with open('params.csv', 'a') as f:  # Just use 'w' mode in 3.x
        w = csv.DictWriter(f, config.keys())
        w.writeheader()
        w.writerow(config)
    """

if __name__ == '__main__':
    main()
