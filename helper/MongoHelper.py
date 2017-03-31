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
    client = MongoClient()
    db = client[databaseName]
    return db


def insert(collection, newData):
    data = db[collection]
    if type(newData) is list:
        res = data.insert_many(newData)
    else:
        res = data.insert_one(newData)
    return res


def find(collection, limit=0, skip=0, query={}):
    data = db[collection]
    results = None
    if (limit == 0):
        results =  data.find(query).sort("_id", pymongo.ASCENDING)
    else:
        results = data.find(query).sort("_id", pymongo.ASCENDING).limit(limit).skip(skip)
    return list(results)

def remove(collection, query):
    collection = db[collection]
    collection.delete_many(query)

def setCategoryForTweets():
    data = find("category")
    for category in data:
        print(category)
        result = db.tweet.update_many({"event_id": category["event_id"]},
                                      {"$set": {"category": category["_id"]}})

        print(category["event_id"], ":", "match", ":", result.matched_count, "modified", " : ", result.modified_count)


def update(collection, condition, value):
    collection = db[collection]
    result =collection.update_many(condition, {"$set":value})
    print("match", ":", result.matched_count, "modified", " : ", result.modified_count)

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


def getEventCategory(collection, ids):
    pipeline  = [
        {   "$match" : {"id" : {"$in":ids}}},
        {   "$group" : { "_id" : {"event":"$event_id"},"data" : { "$addToSet" :{'id': '$id'}}}}
        ]
    return list(db[collection].aggregate(pipeline, allowDiskUse=True))

def aggregateDate(collection, day):
    pipeline = [ { "$group" : { "_id" : {"day" : { "$dayOfYear" : "$date"}},"data" : { "$addToSet" :{'text':"$text", 'id': '$id', 'annotations':'$annotations'}}}},{ "$sort" : { "_id.day" : 1}}, {"$match" : {"_id.day" : day}}]
    return list(db[collection].aggregate(pipeline,allowDiskUse =True))

def intervales(collection, param="hour", interval=2):
    from collections import OrderedDict
    pipeline = [
        {"$group": {
            "_id": {
                "year": {"$year": "$date"},
                "intervalday": {"$dayOfYear": "$date"},
                "interval": {
                    "$subtract": [
                        {"${}".format(param): "$date"},
                        {"$mod": [{"${}".format(param): "$date"}, interval]}
                    ]
                }
            },
            "data": {"$addToSet": '$id'}
        }
        },
        {'$match': {'_id.intervalday': {'$gte': 284}}}
    ]

    sort = OrderedDict()
    sort["_id.intervalday"]=  1
    sort["_id.interval"]=  1

    pipeline.append({"$sort":sort})
    #pipeline = [{'$group': {'_id': {'intervalday': {'$dayOfYear': '$date'}, 'year': {'$year': '$date'}, 'interval': {'$subtract': [{'$hour': '$date'}, {'$mod': [{'$hour': '$date'}, 1]}]}}, 'data': {'$addToSet': '$id'}}}, {'$sort': {'_id.interval': 1, '_id.intervalday': 1}}]

    #print(pipeline)

    return [{'day' : l['_id']['intervalday'], 'interval' : l['_id']['interval'], 'data':l['data']} for l in list(db[collection].aggregate(pipeline, allowDiskUse=True))]

def stat(collection):
    #pipeline = [ { "$group" : { "_id" : {"event_id" : "$event_id","day" : { "$dayOfYear" : "$date"}},
    #"data" : { "$addToSet" :{'id':"$id"}}}}]
    pipeline = [ { "$group" : { "_id" : {"event_id" : "$event_id"},
    "data" : { "$addToSet" :{'id':"$id"}}}}]
    return aggregate(collection,pipeline)

def aggregate(collection, pipeline):
    return list(db[collection].aggregate(pipeline, allowDiskUse=True))

if __name__ == '__main__':
    print(stat('annotation_unsupervised'))