
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import string
import nltk
from autocorrect import spell
import re
from helper import MongoHelper as db
from helper.nerd import  NERD
from helper import Utils
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
        #print(t)
    print("inserting {} annotated tweets".format(len(params)))
    db.insert("annotation_python", params)

def parseTweets():
    db.connect("tweets_dataset")
    limit, skip, index = 400, 0, 0
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


def dbpediaIt(uri):
    from SPARQLWrapper import SPARQLWrapper, JSON
    yago = 'http://dbpedia.org/class/yago/'
    dbpedia = 'http://dbpedia.org/ontology/'
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    query = Utils.dqueryPattern.replace("URI", uri)
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    dbpedias , yagos = {}, {}

    for result in results["results"]["bindings"]:
        type = str(result['type']['value'])
        group = str(result['group']['value'])
        group = Utils.removeNumeric(group)
        type = Utils.removeNumeric(type)
        #group = group.replace(yago, '').replace('>', ' ')
        group = [g.split('/')[len(g.split('/'))-1] for g in group.split('>') if g.startswith(dbpedia) or g.startswith(yago)]
        group = Utils.remove_duplicates(group)
        #group = list(set([g for g in group if g not in Utils.ignored]))

        if type.startswith(yago) and not 'Wiki' in type:
            type = type.replace(yago,'')
            yagos[type] = group

        if type.startswith(dbpedia):
            type = type.replace(dbpedia, '')
            #group = group.replace(dbpedia, '')
            dbpedias[type] = group

    if yagos:
        yagos = Utils.filter(yagos)

    if dbpedias:
        dbpedias = Utils.filter(dbpedias)

    return dbpedias,yagos

def clean():
    db.connect("tweets_dataset")
    limit, skip = 400, 0


    while True:
        res = list(db.find("annotation_python", limit=limit, skip=skip))
        if not res:
            break
        skip+=limit
        for r in res:
            annoations = r['annotations']
            if not annoations:
                continue
            ann = []
            found = False
            for i, a in enumerate(annoations):
                for j, b in enumerate(annoations):
                    if j==i:
                        continue
                    if (a['startChar'] >= b['startChar'] and a['endChar'] <= b['endChar']):
                        found = True
                        break
                if not found:
                    ann.append(a)
                found = False
            r['annotations'] = ann
        db.insert("annotation_purge", res)



def loadAnnotations():
    db.connect("tweets_dataset")
    limit, skip = 100, 0
    while True :
        res = list(db.find("annotation_purge", limit=limit,skip=skip))
        if not res:
            break
        for l in res:
            print(l['text'])
            annotations = l['annotations']
            for annotation in annotations:
                try:
                    uri = annotation['uri'] if 'dbpedia' in annotation['uri'] else 'http://dbpedia.org/resource/{}'.format(str(annotation['label']).replace(' ', '_'))
                    dbpedias, yagos = dbpediaIt(uri)
                    print("DBP", dbpedias,yagos)
                    annotation['dbpedia'] = dbpedias
                    annotation['yago'] = yagos
                except Exception as err:
                    print('Handling run-time error:', err)
                    print(annotation['label'])
            db.update("annotation_purge", {"id": l['id']}, {"annotations": annotations})


if __name__ == '__main__':
    #parseTweets()
    #dbpedias, yagos = dbpediaIt("http://dbpedia.org/resource/Robert_Lefkowitz")
    #print(dbpedias, yagos)
    clean()
    loadAnnotations()