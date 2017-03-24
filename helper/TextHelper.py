
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import nltk
import string
import numpy as np
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
import codecs
from helper.TweetPreprocessor import TweetPreprocessor
from helper import symspell
from operator import itemgetter
from nltk import ngrams

t = TweetPreprocessor()

if not symspell.dictionary:
    symspell.create_dictionary("big.txt")

wordnet_lemmatizer = WordNetLemmatizer()

tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
tp = TweetPreprocessor()
stop = stopwords.words('english') + list(string.punctuation) + ['rt', 'via', 'tweet', 'twitter', 'lol', '"', "'", "lmao"]

porter = nltk.PorterStemmer()

def isStopWord(word):
    default_stopwords = set(stop)
    custom_stopwords = set(codecs.open("stops.txt".format("english"), 'r', ).read().splitlines())
    all_stopwords = list(default_stopwords | custom_stopwords)
    return word.lower() in all_stopwords

def tokenize(text):
    text = ' '.join(text.split())
    text = tp.preprocess(text)
    tokens = [token for token in tknzr.tokenize(text.lower()) if token not in stop and len(token) > 2]
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
    text = t.preprocess(tweet['text'])
    text = tokenize(text)
    mDicts = []
    if(tweet['annotations']):
        text = ' '.join(text)
        newlist = sorted(tweet['annotations'], key=itemgetter('startChar'))
        index = 0

        for ann in newlist:

            ann['label'] = t.preprocess(ann['label']).lower()
            if ann['relevance'] < 0.1 or not ann['extractorType']:
                continue
            uris = str(ann['uri'] if ann['uri'] else ann['label']).split(sep="/")
            label = uris[len(uris)-1]
            if '(' in label:
                labels = label.split("_(")[:-1]
                label = '_('.join(labels)
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
                mDict['type'] = ann['extractorType'].lower()
                mDict['start'] = start
                mDict['end'] = end
            if mDict:
                mDicts.append(mDict)
            index = end

        ents = []

        for a in mDicts:
            ents.append(a['label'])
            a['edges'] =  [(' '.join(text[0:a['start']].split()[-n:]), a['label'],1),(a['label'], ' '.join(text[a['end']:].split()[0:n]),0)]

        gg = ngrams(ents,2)
        for g in gg:
            mDicts.append({'edges' :[(g[0], g[1], 2)]})

    return mDicts

if __name__ == '__main__':
    text = "this is a fuck bull shiet"
    print(tokenize(text))