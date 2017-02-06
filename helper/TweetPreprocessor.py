# -*- coding: utf-8 -*-
"""
Created on Wed May 11 11:45:08 2016

@author: aedouard
"""

import re
import nltk 
class TweetPreprocessor(object):

    def __init__(self):
        self.FLAGS = re.MULTILINE | re.DOTALL
        self.ALLCAPS = '<allcaps>'
        self.HASHTAG = '<hashtag>'
        self.URL = '<url>'
        self.USER = '<user>'
        self.SMILE = ''
        self.LOLFACE = '<lolface>'
        self.SADFACE = '<sadface>'
        self.NEUTRALFACE = '<neutralface>'
        self.HEART = '<heart>'
        self.NUMBER = '<number>'
        self.REPEAT = ''
        self.ELONG = '<elong>'

    def _hashtag(self, text):
        text = text.group()
        hashtag_body = text[1:]
        if hashtag_body.isupper():
            result = (self.HASHTAG + " {} " + self.ALLCAPS).format(hashtag_body)
        else:
            result = " ".join([self.HASHTAG] + [hashtag_body])#re.split(r"(?=[A-Z])", hashtag_body, flags=self.FLAGS))
        return result

    def _allcaps(self, text):
        text = text.group()
        return text.lower() + ' ' + self.ALLCAPS

    def tokenize(self, text):
        default_stopwords = set(nltk.corpus.stopwords.words('english'))
        text = self.preprocess(text)
        words = nltk.word_tokenize(text)
        # Lowercase all words (default_stopwords are lowercase too)
        words = [word for word in words if word not in default_stopwords]
        # Remove stop words 
        words = [word.lower() for word in words]
        # Remove single-character tokens (mostly punctuation)
        words = [word for word in words if len(word) > 3]
        # Stem with snowbal
        # Remove numbers
        words = [word for word in words if not word.isnumeric()]
        return words 

    def topKWords(self,text,k):
        words = self.tokenize(text)
        frequencyActual = nltk.FreqDist(words)
        return frequencyActual.most_common(k)

    def preprocess(self, text):
        eyes, nose = r"[8:=;]", r"['`\-]?"

        re_sub = lambda pattern, repl: re.sub(pattern, repl, text, flags=self.FLAGS)

        text = re_sub(r"https?:\/\/\S+\b|www\.(\w+\.)+\S*", '')
        #text = re_sub(r"/"," / ")
        #text = re_sub(r"@\w+", self.USER)
        text = re_sub(r"{}{}[)dD]+|[)dD]+{}{}".format(eyes, nose, nose, eyes), self.SMILE)
        text = re_sub(r"{}{}p+".format(eyes, nose), self.LOLFACE)
        text = re_sub(r"{}{}\(+|\)+{}{}".format(eyes, nose, nose, eyes), self.SMILE)
        text = re_sub(r"{}{}[\/|l*]".format(eyes, nose), self.SMILE)
        text = re_sub(r"<3", self.SMILE)
        #text = re_sub(r"[-+]?[.\d]*[\d]+[:,.\d]*", self.NUMBER)
        text = re_sub(r"#", '')
        text = re_sub(r"/", '')
        text = re_sub(r"([!?.]){2,}", r"\1 " + self.SMILE)
        #text = re_sub(r"\b(\S*?)(.)\2{2,}\b", r"\1\2 " + self.ELONG)

        #text = re_sub(r"([A-Z]){2,}", self._allcaps)

        return text#.lower()


if __name__ == '__main__':
    t = TweetPreprocessor()
    text = t.preprocess("#syria shaykh jamaluddin serawan assoc syrian scholars http://freehalab.wordpress.com/2012/08/21/shaykh-jamaluddin-serawan-and-the-association-of-syrian-scholars/")
    print(text)