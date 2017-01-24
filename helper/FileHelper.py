from helper import MongoHelper as db
from helper import TextHelper
import os
db.connect("tweets_dataset")
categories = ["Science","Attacks", "Politics","Miscellaneous","Arts","Sports","Accidents","Economy"]
binaries = ["positive","negative"]

def parse(data):
    texts = []
    for t in data:
        text = t['text']
        text = ' '.join([t for t in text.split() if len(t) > 2])
        if len(text) > 0:
            texts.append(text)
    return texts

def write(data, folder, file):
    create(folder)
    with open("{}/{}".format(folder,file), "w", encoding='utf-8') as f:
        texts = parse(data)
        f.write('\n'.join(texts).strip())

def create(folder, destination="./"):
    if not os.path.exists("{}/{}".format(destination,folder)):
        os.makedirs("{}/{}".format(destination,folder))

def generate(type,ontology):

    data = db.find("annotated", query={"type":type, "ontology":ontology, "dataset":"event 2012", "category":{"$ne":"undefined"}})
    write(data=data,folder="train/{}/{}".format(ontology,type), file='positive.txt')

    data = db.find("annotated", query={"type":type, "ontology":ontology, "dataset":"event 2012", "category":"undefined"})
    write(data=data, folder="train/{}/{}".format(ontology, type), file='negative.txt')

    data = db.find("annotated", query={"type":type, "ontology":ontology, "dataset":"fsd", "category":{"$ne":"undefined"}})
    write(data=data, folder="test/{}/{}".format(ontology, type), file='positive.txt')

    data = db.find("annotated", query={"type":type, "ontology":ontology, "dataset":"fsd", "category":"undefined"})
    write(data=data, folder="test/{}/{}".format(ontology, type), file='negative.txt')


def nbLines(file):
    num_lines = sum(1 for line in open(file))
    return num_lines

def buildModelForTrain(config):
    config['dataset'] = "fsd"
    sentences = db.find("annotated",query=config)
    write(sentences, folder="test/{}/{}".format(config['ontology'], config['type']),
          file="{}.txt".format(config['category']))

    config['dataset'] = "event 2012"
    sentences = db.find("annotated", query=config)
    write(sentences, folder="train/{}/{}".format(config['ontology'], config['type']),
          file="{}.txt".format(config['category']))

    #print(sentences)

def generateFolders():
    create("train")
    create("test")
    create("dbpedia", destination="train")
    create("dbpedia", destination="test")
    create("yago", destination="train")
    create("yago", destination="test")
    create("generic", destination="train/dbpedia")
    create("specific", destination="train/dbpedia")
    create("generic", destination="train/yago")
    create("specific", destination="train/yago")
    create("generic", destination="test/dbpedia")
    create("specific", destination="test/dbpedia")
    create("generic", destination="test/yago")
    create("specific", destination="test/yago")
    create("normal", destination="train")
    create("normal", destination="test")

def generateDataFile():
    params = [
        {'ontology': 'dbpedia', 'type': 'generic', 'name': 'dbpedia_generic'},
        {'ontology': 'dbpedia', 'type': 'specific', 'name': 'dbpedia_specific'},
        {'ontology': 'yago', 'type': 'generic', 'name': 'yago_generic'},
        {'ontology': 'yago', 'type': 'specific', 'name': 'yago_specific'},
        {'ontology': 'dbpedia', 'type': 'normal', 'name': 'dbpedia_normal'},
    ]


    for cat in categories:
        for config in params:
            config['category'] = cat
            if 'name' in config:
                del config['name']

            buildModelForTrain(config)
            generate(config['type'], config['ontology'])

def createTrainFile(classes, directory, name="neon_train"):
    data = []
    with open("./{}.tsv".format(name), "w", encoding='utf-8') as file:
        for index, cl in enumerate(classes):
            with open(os.path.join(directory, "{}.txt".format(cl))) as f:
                for line in f:
                    line = TextHelper.tokenize(line)
                    if len(line) <=0:
                        continue
                    file.write("{}\t{}\n".format(index,' '.join(line)))


if __name__ == '__main__':
    generateDataFile()
