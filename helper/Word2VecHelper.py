import gensim
from helper import TextHelper
import numpy as np

def createModel(files, name, merge=0,  args={"job":10, "size" :300, "min_count" : 2, "window":2}):
    #load the google model
    #model = loadModel("GoogleNews-vectors-negative300")
    sentences = TextHelper.MySentences(files)  # a memory-friendly iterator
    #model.train(sentences, total_words=sum(len(i) for i in sentences))
    name = "{}_{}.bin".format(name,'merged' if merge > 0 else 'simple')
    model = gensim.models.Word2Vec(sentences, workers=args["job"], size=args["size"], min_count=args["min_count"], window=args["window"])
    if merge > 0:
        model.intersect_word2vec_format('GoogleNews-vectors-negative300.bin',
                                lockf=1.0,
                                binary=True)
    model.train(sentences)
    model.save_word2vec_format(name, binary=True)
    return model

def loadModel(name, merge=0):
    name = "{}_{}.bin".format(name, 'merged' if merge>0 else 'simple')
    model = gensim.models.Word2Vec.load_word2vec_format(name,binary=True, unicode_errors='ignore')
    return model

def loadModel(name,):
    model = gensim.models.Word2Vec.load_word2vec_format(name,binary=True, unicode_errors='ignore')
    return model




def dataFromFile(file):
    texts, ids, labels = [],[], []
    with open(file, "r") as infile:
        for line in infile:
            id, label, text = line.split("\t")
            texts.append(TextHelper.tokenize(text))
            ids.append(id)
            labels.append(label)
    return ids,labels, texts


def loadData(classes, args, type):
    instances, labels, texts = [], [], []
    for index, category in enumerate(classes):
        folder = "{}/{}/{}/{}.txt".format(type, args.ontology,args.type,category)
        _instances, _labels, _texts = dataFromFile(folder)
        instances.extend(_instances)
        labels.extend(_labels)
        texts.extend(_texts)

    instances, labels, texts = np.array(instances), np.array(labels),np.array(texts)
    return instances, labels, texts
