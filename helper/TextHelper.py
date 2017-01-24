
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import string
import nltk

tknzr = TweetTokenizer()

stop = stopwords.words('english') + list(string.punctuation)
porter = nltk.PorterStemmer()


def tokenize(text):
    tokens = [porter.stem(token) for token in tknzr.tokenize(text.lower()) if token not in stop and len(token) > 2]
    return tokens


class MySentences(object):
    def __init__(self, files):
        self.files = files

    def __iter__(self):
        for fname in self.files:
            for line in open(fname):
                yield tokenize(line)

