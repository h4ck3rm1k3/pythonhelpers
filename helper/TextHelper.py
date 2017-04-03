
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import nltk
import string
import helper
import numpy as np
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
import codecs
from helper.TweetPreprocessor import TweetPreprocessor
from helper import symspell
from operator import itemgetter
from nltk import ngrams
import re
t = TweetPreprocessor()

log = helper.enableLog()
helper.disableLog(log)
if not symspell.dictionary:
    #symspell.init()
    pass

wordnet_lemmatizer = WordNetLemmatizer()

tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
tp = TweetPreprocessor()
stop = stopwords.words('english') + list(string.punctuation)
default_stopwords = set(stop)
custom_stopwords = set(codecs.open("slang.txt".format("english"), 'r', ).read().splitlines())
all_stopwords = list(default_stopwords | custom_stopwords)

porter = nltk.PorterStemmer()

def isStopWord(word):

    return word.lower() in all_stopwords

def tokenize(text, excerpt=[]):
    text = t.preprocess(text)
    #tokens = [token for token in tknzr.tokenize(text.lower()) if token in excerpt or token not in all_stopwords]
    tokens = [token for token in text.split() if (len(token) > 3 or token in excerpt ) and (token not in all_stopwords)]
    return tokens

def isInWordNet(word):
    word = wn.synsets(word)
    return word
"""
Compute the Leveinstein distance between the words
"""
def distance(word1, word2):
    return nltk.edit_distance(word1,word2)

def similarity(w1, w2, sim=wn.path_similarity):

  synsets1 = wn.synsets(w1)
  synsets2 = wn.synsets(w2)
  sim_scores = []
  for synset1 in synsets1:
    for synset2 in synsets2:
      sim_scores.append(sim(synset1, synset2))
  sim_scores = [sc for sc in sim_scores if sc]
  if len(sim_scores) == 0:
    return 0
  else:
    return max(sim_scores)

def slangs(text):
    return len(set(text.split()).intersection(custom_stopwords))

def lemmatize(word):
    word = word.lower()
    if not isInWordNet(word):
        word = symspell.best_word(word)
    wordv =  wordnet_lemmatizer.lemmatize(word, pos='v')
    if wordv == word:
        wordv = wordnet_lemmatizer.lemmatize(word, pos='n')
    return wordv

class MySentences(object):
    def __init__(self, files):
        self.files = files

    def __iter__(self):
        for fname in self.files:
            for line in open(fname):
                _,__,text  = line.split('\t')
                yield tokenize(text)

def tokenizer(text):
    text = text.lower()

    tokens = text.split(sep="=>")
    return [t for t in tokens if len(t) > 1]

def top_tfidf_feats(row, features, top_n=25):
    ''' Get top n tfidf values in row and return them with their corresponding feature names.'''
    topn_ids = np.argsort(row)[::-1]
    top_feats = {features[i]:row[i] for i in topn_ids}
    top_feats = {key:top_feats[key] for key in top_feats.keys() if top_feats[key] > 0}
    return top_feats

def top_feats_in_doc(Xtr, features, row_id, top_n=25):
    ''' Top tfidf features in specific document (matrix row) '''
    row = np.squeeze(Xtr[row_id].toarray())
    return top_tfidf_feats(row, features, top_n)

def buildTfIdf(docs):
    vectorizer = TfidfVectorizer(min_df=1, tokenizer=tokenizer)
    tfidf_matrix = vectorizer.fit_transform(docs)
    feature_names = vectorizer.get_feature_names()
    doc =  top_feats_in_doc(tfidf_matrix, feature_names, len(docs)-1)
    return  doc

def extract_entity_context(tweet, n=1):
    tweet = reIndex(tweet)
    text = tweet['text']

    if slangs(text) >= 1 :
        return []


    mDicts = []
    if(tweet['annotations']):
        ents = []
        for ann in tweet['annotations']:
            if ann['relevance'] < 0.2 or not ann['extractorType']:
                continue
            uris = str(ann['uri'] if ann['uri'] else ann['label']).split(sep="/")
            if len(uris) < 3:
                continue
            label = uris[len(uris)-1]
            if '(' in label:
                labels = label.split("_(")[:-1]
                label = '_('.join(labels)
            regex = re.compile('[,\.!?]')  # etc.
            label = regex.sub('', label).lower()
            if len(label) > 3:
                text = text[0:ann['startChar']] + " " + label +" " + text[ann['endChar']+1:]
                mDict = {'label': label.lower(), 'type':ann['extractorType'].lower()}
                ents.append(label.lower())
                mDicts.append(mDict)

        """if stops(text) > 3 and len(ents) < 2:
            return []"""
        text = tokenize(text, excerpt=ents) #test
        text = [t if t in ents else symspell.get_suggestions(t, silent=True) for t in text]
        for a in mDicts:
            try:
                index = text.index(a['label'])
                a['edges'] = []
                if index > 0 :
                    a['edges'].append((text[index-1], a['label'], 1))
                if index < len(text)-1:
                    a['edges'].append((a['label'], text[index + 1], 0))
            except:
                return []

        gg = ngrams(ents,2)
        for g in gg:
            mDicts.append({'edges' :[(g[0], g[1], 2)]})

    return mDicts


def reIndex(tweet):
    #print(tweet['id'])
    start = tweet['end'] - len(tweet['text']) #tweet['start']
    tweet['annotations'] = sorted(tweet['annotations'], key=itemgetter('startChar'), reverse=True)
    for ann in tweet['annotations']:
        try:
            ann['startChar'] = ann['startChar'] - start
            ann['endChar'] = ann['startChar'] + len(ann['label'])
            indexes = [m.start() for m in re.finditer(ann['label'].lower(), tweet['text'].lower())]
            current, small = -1, 0
            if not indexes:
                ann['relevance'] = 0
            for index in indexes:
                if ann['startChar'] - index < small or small == 0:
                    small = ann['startChar'] - index
                    current = index
            ann['startChar'] = current
            ann['endChar'] = ann['startChar'] + len(ann['label'])
        except:
            ann['relevance'] = 0
    tweet['annotations'] = sorted(tweet['annotations'], key=itemgetter('startChar'), reverse=True)
    tweet['start'] = 0

    return tweet

if __name__ == '__main__':


    print(tokenize("go helll fuck this shiet damn it lmfao loll "))

    """tweet ={
    "start" : 15049,
    "text" : "IFollowBack ClassicMap app brings back Google Maps to Apple iOS 6 -- kind of - Los Angeles… ",
    "end" : 15144,
    "annotations" : [
        {
            "extractor" : "textrazor",
            "idEntity" : 26684293,
            "relevance" : 0.3286,
            "confidence" : 0.396842,
            "startChar" : 15072,
            "extractorType" : "/business/industry,/business/competitive_space,/organization/organization_sector,/computer/operating_system,/computer/software_genre,/cvg/cvg_genre,/book/book_subject,/internet/website_category,/business/consumer_product,/media_common/media_genre",
            "nerdType" : "http://nerd.eurecom.fr/ontology#Thing",
            "label" : "app",
            "endChar" : 15075,
            "uri" : "http://en.wikipedia.org/wiki/Mobile_app"
        },
        {
            "extractor" : "textrazor",
            "idEntity" : 26684295,
            "relevance" : 0.3728,
            "confidence" : 0.605474,
            "startChar" : 15088,
            "extractorType" : "Work,Agent,Website,Organisation,Company,/projects/project_focus,/book/book_subject,/business/brand,/internet/website",
            "nerdType" : "http://nerd.eurecom.fr/ontology#Organization",
            "label" : "Google Maps",
            "endChar" : 15099,
            "uri" : "http://en.wikipedia.org/wiki/Google_Maps"
        },
        {
            "extractor" : "textrazor",
            "idEntity" : 26684298,
            "relevance" : 0.0,
            "confidence" : 0.0,
            "startChar" : 15128,
            "extractorType" : "Company,/organization/organization",
            "nerdType" : "http://nerd.eurecom.fr/ontology#Organization",
            "label" : "Los Angeles…",
            "endChar" : 15140,
            "uri" : ""
        },
        {
            "extractor" : "textrazor",
            "idEntity" : 26684299,
            "relevance" : 0.463,
            "confidence" : 0.190316,
            "startChar" : 15109,
            "extractorType" : "Work,Software,/computer/operating_system",
            "nerdType" : "http://nerd.eurecom.fr/ontology#Thing",
            "label" : "iOS 6",
            "endChar" : 15114,
            "uri" : "http://en.wikipedia.org/wiki/IOS_6"
        },
        {
            "extractor" : "textrazor",
            "idEntity" : 26684300,
            "relevance" : 0.406,
            "confidence" : 0.832842,
            "startChar" : 15103,
            "extractorType" : "Work,Software,/computer/software,/cvg/cvg_platform,/computer/operating_system",
            "nerdType" : "http://nerd.eurecom.fr/ontology#Thing",
            "label" : "Apple iOS",
            "endChar" : 15112,
            "uri" : "http://en.wikipedia.org/wiki/IOS"
        }
    ],
    "id" : "255819983924375553",
    "dataset" : "event 2012",
    "event_id" : -1
}

    print(extract_entity_context(tweet))"""
