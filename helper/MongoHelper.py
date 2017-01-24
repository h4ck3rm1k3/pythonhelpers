# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 12:44:37 2016

@author: aedouard
"""
from bson.objectid import ObjectId
import pymongo
from pymongo import MongoClient
from helper import NltkHelper

db = None
index = 0


def connect(databaseName):
    global db
    if db is None:
        client = MongoClient()
        db = client[databaseName]
    return db


def insert(collection, newData):
    data = db[collection]
    if type(newData) is list:
        data.insert_many(newData)
    else:
        data.insert_one(newData)


def find(collection, limit=0, skip=0, query={}):
    data = db[collection]
    results = None
    if (limit == 0):
        results =  data.find(query).sort('_id', pymongo.ASCENDING)
    else:
        results = data.find(query).sort('_id', pymongo.ASCENDING).limit(limit).skip(skip)
    return list(results)


def setCategoryForTweets():
    data = find("category")
    for category in data:
        print(category)
        result = db.tweet.update_many({"event_id": category["event_id"]},
                                      {"$set": {"category": category["_id"]}})

        print(category["event_id"], ":", "match", ":", result.matched_count, "modified", " : ", result.modified_count)


def setTweetAuthor(data):
    for tweet in data:
        result = db.tweet.update_many({"tweet_id": tweet["tweet_id"]},
                                      {"$set": {"author": tweet['author'], 'date': tweet['date']}})
        # print("match-tweet", ":", result.matched_count,"modified", " : ", result.modified_count)
        if (result.matched_count == 0):
            print("tweet", tweet["tweet_id"])

        result = db.annotated.update_many({"tweet_id": tweet["tweet_id"]},
                                          {"$set": {"author": tweet['author'], 'date': tweet['date']}})
        if (result.matched_count == 0):
            print("annotated", tweet["tweet_id"])
            # print("match-annoated", ":", result.matched_count,"modified", " : ", result.modified_count)


def modifyAnnotation(tweet_id):
    data = ["STANFORD", "ST", "TweetNLP", "NERD", "TEXTRAZOR", "ALCHEMYAPI", "COMBINED", "DANDELIONAPI", "NERDML",
            "RITTER"]
    db.annotation.remove({"type": {"$in": data}, "tweet": tweet_id})
    """
    for annotation in data:
        result = db.annotation.update_one({"_id": annotation["_id"]},
                                      {"$set":{"extractorType":annotation["nerdType"]}})
        print("match", ":", result.matched_count,"modified", " : ", result.modified_count)
    """


def modifyTweets():
    data = db.tweet.find();
    for tweet in data:
        event_id = int(tweet["event_id"])  # .replace("ObjectId(","").replace(")","")
        # print (tweet)
        # print (str(annotation["_id"]))
        result = db.tweet.update_many({"_id": tweet["_id"]},
                                      {"$set": {"event_id": event_id}})
        print("match", ":", result.matched_count, "modified", " : ", result.modified_count)


def findOneByKey(collection, key, value):
    data = db[collection]
    return data.find_one({key: value})


def denormalizeAnnotation():
    # Load the tweets
    i = 0
    while True:
        print('Iteration ', i)
        tweets = find('tweet', 1000, i, {'dataset': 'fsd', 'event_id': -1})
        if tweets.count(True) == 0:
            break;
        for tweet in tweets:
            # get the category of the tweet
            # category = findOneByKey("category","event_id", tweet["event_id"])
            # set the category of the tweet in annoated
            result = db.annotation.update_many({"tweet": tweet["_id"]},
                                               {"$set": {"tweet_text": tweet["text"]}})
            print("match", ":", result.matched_count, "modified", " : ", result.modified_count)
        i += 1000


def denormalizeDataset():
    # Load the tweets
    i = 0
    while True:
        print('Iteration ', i)
        tweets = find('tweet', 1000, i, {'tweet_text': {'$exists': False}})
        if tweets.count(True) == 0:
            print("Empty")
            break;

        for tweet in tweets:
            result = db.annotated.update_many({"tweet": tweet["_id"]},
                                              {"$set": {"dataset": tweet["dataset"]}})
            print("match", ":", result.matched_count, "modified", " : ", result.modified_count)
        i += 1000
    print('Done')


def buildDictionnary(dataset, ontology, _type):
    token_dict = {}
    i = 0
    while True:
        annotations = find('annotated', 1000, i, {'ontology': ontology, 'dataset': dataset, 'type': _type})
        if annotations.count(True) == 0:
            print("Empty")
            break;

        for annotation in annotations:
            token_dict[annotation["_id"]] = annotation["text"];
        i += 1000
    return token_dict


def preprocessingDataset():
    # Load the tweets
    i = 0
    while True:
        # print ('Iteration ', i)
        annotations = find('annotated', 1000, i, {})
        if annotations.count(True) == 0:
            print("Empty")
            break;

        for annotation in annotations:
            # print (annotation)
            text = preprocess(annotation["text"])
            result = db.annotated.update({"_id": annotation["_id"]},
                                         {'$set': {"text_snowball": text}})
            print(result)
        i += 1000
    print('Done')


def denormalizeTweetId():
    # Load the tweets
    i = 0
    while True:
        annotations = find('annotated', 1000, i, {'tweet_id': {'$exists': False}})
        if annotations.count(True) == 0:
            print("Empty")
            break;

        for annotation in annotations:
            tweet = findOneByKey('tweet', '_id', annotation['tweet'])
            result = db.annotated.update_many({"tweet": annotation['tweet']},
                                              {'$set': {"tweet_id": tweet["tweet_id"]}})
            print("match", ":", result.matched_count, "modified", " : ", result.modified_count)
        i += 1000
    print('Done')


def loadCategories():
    categories = db.category.find({})
    mdict = {
        "Arts, Culture & Entertainment": "Arts",
        "Law, Politics & Scandals": "Politics",
        "Sports": "Sports",
        "Disasters & Accidents": "Accidents",
        "Miscellaneous": "Miscellaneous",
        "Science & Technology": "Science",
        "Business & Economy": "Economy",
        "Armed Conflicts & Attacks": "Attacks"
    }
    for category in categories:
        result = db.annotated.update_many({"category": str(category['_id'])},
                                          {'$set': {"category": mdict[category["categorie_text"]]}})
        print("match", ":", result.matched_count, "modified", " : ", result.modified_count)


def addTwetId():
    # Load the tweets
    i = 0
    index = 0
    while True:
        annotations = find('annotated', 1000, i, {'tweet_id': {'$exists': False}})
        index = index + 1
        if annotations.count(True) == 0:
            print("Empty")
            break;

        for annotation in annotations:
            "tweet = findOneByKey('tweet','_id', annotation['tweet'])"
            result = db.annotated.update_many({"tweet": annotation['tweet']},
                                              {'$set': {"tweet_id": tweet["tweet_id"]}})
            print("match", ":", result.matched_count, "modified", " : ", result.modified_count)
        i += 1000
    print('Done')