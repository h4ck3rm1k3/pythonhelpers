
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import string
import nltk
import statistics as st
import re
from helper.TweetPreprocessor import TweetPreprocessor
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
wordnet_lemmatizer = WordNetLemmatizer()

tknzr = TweetTokenizer()

stop = stopwords.words('english') + list(string.punctuation) + ['rt', 'via', 'tweet', 'twitter', 'lol']
porter = nltk.PorterStemmer()

def isStopWord(word):
    return word.lower() in stop

def tokenize(text):
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


def frequency(dists, actual):

    tWords = {}
    # compute word frequency for each word in the past intervals
    # frequencyPast = nltk.FreqDist(past)
    # compute word frequency for each word in the current interval
    frequencyActual = nltk.FreqDist(actual)
    fdist = frequencyActual.most_common()
    # return fdist[0][0] + " " + fdist[1][0]

    for word, n in fdist:
        count = []
        count.extend([freq[word] for freq in dists])
        print(count)
        if len(count) > 1:
            # count.append(n)
            mean = sum(count) / len(count)
            d = st.stdev(count)
            if d==0:
                d = 1
            re = (n - mean) / d
            print(word, mean,d,re)
            tWords[word] = re
            # print(word,count,n,mean,d)
        else:
            tWords[word] = n

    dists.append(frequencyActual)
    res = sorted(tWords.items(), key=lambda x: (-x[1], x[0]))
    return res

def frequentWords(dists, data):
    # default_stopwords = set(nltk.corpus.stopwords.words(language))
    tweet_preprocessor = TweetPreprocessor()
    texts = ' '.join([y['text'] for y in data])
    texts = tweet_preprocessor.preprocess(texts)
    words = nltk.word_tokenize(texts)
    # Lowercase all words (default_stopwords are lowercase too)
    words = [word for word in words if word not in stop]
    # Remove stop words
    words = [word.lower() for word in words]
    # Remove single-character tokens (mostly punctuation)
    words = [word for word in words if len(word) > 3]
    # Stem with snowbal
    # stemmer = nltk.stem.snowball.SnowballStemmer('english')
    # words = [stemmer.stem(word) for word in words]
    # Remove numbers
    words = [word for word in words if not word.isnumeric()]
    # fdist = nltk.FreqDist(words)
    tot = {}
    d = frequency(dists, words)
    return d