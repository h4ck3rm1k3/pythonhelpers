
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import string
import nltk
from autocorrect import spell
import re
from helper import MongoHelper as db
from helper.nerd import  NERD
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


def correct(text):
    text = re.sub(r'(.)\1+', r'\1', text)
    res = []
    for t in text.split(" "):
        res.append(spell(t))
    return ' '.join(res)

def nerdIt(params,tt):
    timeout = 10
    n = NERD('nerd.eurecom.fr', "cci7nqeutkegjsjlb4rrobd9s88vdejl")
    data = n.extract(tt, 'textrazor', timeout)

    for t in params:
        t['annotations'] = [d for d in data if d['startChar'] >= t['start'] and d['endChar'] <= t['end']]
        print(t)

    db.insert("annotation_python", params)

def parseTweets():
    db.connect("tweets_dataset")
    limit, skip, index = 10, 0, 0
    separator = "==="


    while True:
        params = []
        tt = ""
        res = list(db.find("annotated", limit=limit, skip=skip, query={'ontology':'dbpedia', 'type':'normal'}))
        if len(res) > 0:
            for r in res:
                text = str(r['text']).strip()
                params.append(
                    {"start": index, "end": len(text) + index + len(separator), 'text': text, 'annotations': [], 'id' : r['tweet_id']})
                index += len(text) + len(separator)
                tt += text + separator
        else:
            break
        skip+=limit
        nerdIt(params,tt)



if __name__ == '__main__':
    parseTweets()
