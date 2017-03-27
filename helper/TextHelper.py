
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

"""if not symspell.dictionary:
    symspell.create_dictionary_from_wordnet()"""

wordnet_lemmatizer = WordNetLemmatizer()

tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
tp = TweetPreprocessor()
stop = stopwords.words('english') + list(string.punctuation) + ['rt', 'via', 'tweet', 'twitter', 'lol', '"', "'", "lmao"]
default_stopwords = set(stop)
custom_stopwords = set(codecs.open("stops.txt".format("english"), 'r', ).read().splitlines())
all_stopwords = list(default_stopwords | custom_stopwords)

porter = nltk.PorterStemmer()

def isStopWord(word):

    return word.lower() in all_stopwords

def tokenize(text):
    text = text.replace('._', '__')
    text = t.preprocess(text)
    tokens = [token.replace('__', '._') for token in tknzr.tokenize(text.lower()) if token not in all_stopwords]
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
    text = tweet['text']

    mDicts = []
    if(tweet['annotations']):
        #text = ' '.join(text)
        #text = symspell.correct_sentence(text)
        newlist = sorted(tweet['annotations'], key=itemgetter('startChar'))
        index = 0
        ents = []
        for ann in newlist:
            #ann['label'] = t.preprocess(ann['label']).lower()
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
                mDict ['label'] = label.lower()
                mDict['type'] = ann['extractorType'].lower()
                mDict['start'] = start
                mDict['end'] = end
                ents.append(ann['label'].lower())
            if mDict:
                mDicts.append(mDict)
            index = end


        text = tokenize(text)
        text = [t if t in ents else symspell.get_suggestions(t, silent=True) for t in text]

        print(text)
        print(mDicts)

        for a in mDicts:
            index = text.index(a['label'])
            a['edges'] = []
            if index > 0 :
                a['edges'].append((text[index-1], a['label'], 1))
            if index < len(text)-1:
                a['edges'].append((a['label'], text[index + 1], 0))

        gg = ngrams(ents,2)
        for g in gg:
            mDicts.append({'edges' :[(g[0], g[1], 2)]})

    return mDicts


if __name__ == '__main__':
    tweet = {
    "event_id" : -1,
    "dataset" : "event 2012",
    "text" : "My school think they so damn better than everybody else, and don't even have BET where I can watch the Hip Hop Awards",
    "start" : 10953,
    "annotations" : [
        {
            "idEntity" : 26684876,
            "extractorType" : "Agent,Organisation,Broadcaster,TelevisionStation,/award/award_winner,/organization/organization,/tv/tv_network,/award/award_presenting_organization,/business/employer,/business/customer,/film/film_distributor,/tv/tv_program_creator,/award/award_nominee,/business/business_operation",
            "relevance" : 0.3307,
            "endChar" : 11033,
            "uri" : "http://en.wikipedia.org/wiki/BET",
            "nerdType" : "http://nerd.eurecom.fr/ontology#Organization",
            "label" : "BET",
            "extractor" : "textrazor",
            "confidence" : 0.953263,
            "startChar" : 11030
        },
        {
            "idEntity" : 26684878,
            "extractorType" : "MusicGenre,TopicalConcept,Genre,/broadcast/genre,/film/film_subject,/book/book_subject,/business/industry,/music/genre,/radio/radio_subject,/tv/tv_subject,/media_common/media_genre,/broadcast/radio_format,/music/music_video_genre,/broadcast/content,/theater/theater_genre,/award/award_discipline",
            "relevance" : 0.4629,
            "endChar" : 11063,
            "uri" : "http://en.wikipedia.org/wiki/Hip_hop_music",
            "nerdType" : "http://nerd.eurecom.fr/ontology#Thing",
            "label" : "Hip Hop",
            "extractor" : "textrazor",
            "confidence" : 8.53158,
            "startChar" : 11056
        }
    ],
    "id" : "255820017243942913",
    "end" : 11073
}

    print(extract_entity_context(tweet))
