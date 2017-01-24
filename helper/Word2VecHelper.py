import gensim
from helper import TextHelper


def createModel(files, name, args={"job":10, "size" :300, "min_count" : 2, "window":2}):
    sentences = TextHelper.MySentences(files)  # a memory-friendly iterator
    model = gensim.models.Word2Vec(sentences, workers=args["job"], size=args["size"], min_count=args["min_count"], window=args["window"])
    model.save_word2vec_format("{}.bin".format(name), binary=True)
    return model