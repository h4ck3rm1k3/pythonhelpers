from operator import itemgetter
from helper import MongoHelper as db
from helper.nerd import  NERD
from helper import Utils, TextHelper
from nltk import ngrams
import re
from helper.TweetPreprocessor import TweetPreprocessor

t = TweetPreprocessor()

def nerdIt(params,tt):
    timeout = 10
    n = NERD('nerd.eurecom.fr', "cci7nqeutkegjsjlb4rrobd9s88vdejl")
    data = n.extract(tt, 'textrazor', timeout)

    for t in params:
        t['annotations'] = [d for d in data if d['startChar'] >= t['start'] and d['endChar'] <= t['end']]
        cleanAnnotation(t)
        #print(t)
    print("Annotated", len(params))
    db.insert("annotation_unsupervised", params)

def parseTweets():
    db.connect("event_2012")
    limit, skip, index = 400, 400400, 0
    separator = "==="

    while True:
        params = []
        tt = ""
        index = 0
        res = list(db.find("tweets", limit=limit, skip=skip))
        if len(res) > 0:
            for r in res:
                text = str(r['text']).strip()
                text = t.preprocess(text)
                param = r
                del param['_id']
                param['annotations'] = []
                param['start'] = index
                param['end'] = len(text) + index + len(separator)
                params.append(param)
                index += len(text) + len(separator)
                tt += text + separator
        else:
            break

        skip+=limit
        nerdIt(params,tt)
        #break

def cleanAnnotation(r):
    annoations = r['annotations']
    if not annoations:
        return
    ann = []
    found = False
    for i, a in enumerate(annoations):
        for j, b in enumerate(annoations):
            if j == i:
                continue
            if (a['startChar'] >= b['startChar'] and a['endChar'] <= b['endChar']):
                found = True
                break
        if not found:
            ann.append(a)
        found = False
    r['annotations'] = ann

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
        skip+=limit
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

def isEntityConsidered(types):
    entities = ['person','location','organization','company']
    isIn = False
    for ent in entities:
        if ent in types.split('/'):
            isIn = True
            break
    return isIn

def format(tweet, n=1):

    text = t.preprocess(tweet['text'])
    text = ' '.join(TextHelper.tokenize(text))
    _text =  ""
    newlist = sorted(tweet['annotations'], key=itemgetter('startChar'))
    index = 0
    mDicts= []

    for ann in newlist:
        ann['label'] = t.preprocess(ann['label']).lower()
        if ann['relevance'] < 0.1 or not ann['uri']:
            continue
        uris = str(ann['uri']).split(sep="/")
        label = uris[len(uris)-1]#.replace("_", " ")
        #ann['label'] = t.preprocess(ann['label'].lower()).replace("'s", "")
        mDict = {}
        try:
            start =  text.index(ann['label'], index) if ann['label'] in text else -1
        except:
            start = -1
        end = index
        if start >= 0:
            text = text.replace(ann['label'], label)
            end = start + len(label) #ann['endChar'] - ann['startChar']
            mDict ['label'] = label
            mDict['start'] = start
            mDict['end'] = end
        if mDict:
            mDicts.append(mDict)
        index = end

    ents = []

    for a in mDicts:
        ents.append(a['label'])
        a['edges'] =  [(' '.join(text[0:a['start']].split()[-n:]), a['label'],1),(a['label'], ' '.join(text[a['end']:].split()[0:n]),0)] #'{} {} {}'.format(' '.join(text[0:a['start']].split()[-2:]), a['label'], ' '.join(text[a['end']:].split()[0:2]))

    return mDicts

def getNodes(text, n=2):
    text = t.preprocess(text)
    tokens = text.split()
    #tokens = TextHelper.tokenize(text)
    ng = ngrams(tokens,n)
    return [t for t in ngrams(tokens,n)]

def groundTruthEvent(collection,ids):
    gte = db.getEventCategory(collection, ids)
    tot = sum(len(d['data']) for d in gte)
    gte = sorted(gte, key=lambda k: len(k['data']), reverse=True)
    print([(e['_id'], len(e['data'])) for e in gte])
    #print(gte)
    if tot > 0.20*len(ids):
        return [gte[0]['_id']['event']]
        """for ev in gte :
            print(ev['_id']['event'], len(ev['data']), len(ids))
            if len(ev['data']) > 0.6*tot:
                return [ev['_id']['event']]"""
        #return [str(ev['_id']['event']) for ev in gte]
    return []

def replacement():
    db.connect("tweets_dataset")
    limit, skip = 100, 0
    while True:
        res = list(db.find("annotation_purge", limit=limit, skip=skip))
        if not res:
            break
        skip+=limit
        for l in res:
            text = str(l['text'])
            _textYG, _textDG , _textYS, _textDS = "", "", "", ""
            newlist = sorted(l['annotations'], key=itemgetter('startChar'))
            index = 0

            for ann in newlist:
                cType = ann['extractorType'].split(',')[0] if not str(ann['extractorType']).startswith("/") else ann['label']
                start = ann['startChar'] - ann['start']
                end = start + ann['endChar']-ann['startChar']
                _textDG +=text[index:start]
                _textDS +=text[index:start]
                _textYG +=text[index:start]
                _textYS +=text[index:start]

                if 'dbpedia' in ann and type(ann['dbpedia']) is list and ann['dbpedia'][0]:
                    dbpedias = ann['dbpedia']
                    _textDG += " " + dbpedias[len(dbpedias)-1]
                    _textDS += " " + dbpedias[0]
                else:
                    _textDG +=" " +cType
                    _textDS +=" " + cType

                if 'yago' in ann and type(ann['yago']) is list and ann['yago'][0]:
                    yagos = ann['yago']
                    _textYG += " " + yagos[len(yagos)-1]
                    _textYS += " " + yagos[0]

                else:
                    _textYG += " " +cType
                    _textYS += " " +cType

                index = end

            _textYG += " " +text[index:len(text)]
            _textDG += " " +text[index:len(text)]
            _textYS += " " +text[index:len(text)]
            _textDS += " " +text[index:len(text)]

            _textDG = _textDG.strip()
            _textYG = _textYG.strip()
            _textYS = _textYS.strip()
            _textDS = _textDS.strip()

            print(_textYG)
            print(_textYS)
            print(_textDG)
            print(_textDS)
            d = {}

            d['dbpedia_generic'] = _textDG
            d['dbpedia_specific'] = _textDS
            d['yago_generic'] = _textYG
            d['yago_specific'] = _textYS
            db.update("annotation_purge", {"id":l['id']}, d)





if __name__ == '__main__':
    parseTweets()
