import gensim
from helper import TextHelper
import numpy as np

def createModel(files, name, args={"job":10, "size" :300, "min_count" : 2, "window":2}):
    sentences = TextHelper.MySentences(files)  # a memory-friendly iterator
    model = gensim.models.Word2Vec(sentences, workers=args["job"], size=args["size"], min_count=args["min_count"], window=args["window"])
    model.save_word2vec_format("{}.bin".format(name), binary=True)
    return model

def loadModel(name):
    model = gensim.models.Word2Vec.load_word2vec_format("{}.bin".format(name),binary=True)
    return model


def mFile(file):
    X = []
    with open(file, "r") as infile:
        for line in infile:
            # label, text = line.split("\t")
            # texts are already tokenized, just split on space
            # in a real case we would use e.g. spaCy for tokenization
            # and maybe remove stopwords etc.
            X.append(TextHelper.tokenize(line))
    return X


def load(folder, X, y,label):
    train = mFile(folder)

    if len(train) > 0 :
        y.extend([label for _ in train])
        X.extend(train)
    return X, y

def loadData(classes, args):
    X_train, y_train, X_test, y_test = [], [], [], []
    for index, category in enumerate(classes):
        load("train/{}/{}/{}.txt".format(args.ontology,args.type,category),X_train,y_train,category)
        load("test/{}/{}/{}.txt".format(args.ontology, args.type, category), X_test, y_test, category)

    X_train, y_train, X_test, y_test = np.array(X_train), np.array(y_train),np.array(X_test), np.array(y_test)
    return X_train, y_train, X_test, y_test