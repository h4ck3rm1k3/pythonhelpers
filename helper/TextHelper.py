
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import string
import nltk
import re

tknzr = TweetTokenizer()

stop = stopwords.words('english') + list(string.punctuation)
porter = nltk.PorterStemmer()

def isStopWord(word):
    return word.lower() in stop

def tokenize(text):
    tokens = [token for token in tknzr.tokenize(text.lower()) if token not in stop and len(token) > 2]
    return tokens


class MySentences(object):
    def __init__(self, files):
        self.files = files

    def __iter__(self):
        for fname in self.files:
            for line in open(fname):
                _,__,text  = line.split('\t')
                yield tokenize(text)

