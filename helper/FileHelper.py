from helper import MongoHelper as db
from helper import TextHelper
import os
db.connect("tweets_dataset")
categories = ["Science","Attacks", "Politics","Miscellaneous","Arts","Sports","Accidents","Economy"]
binaries = ["positive","negative"]


def parse(data, binary=False):
    texts = []
    for t in data:
        text = t['text']
        text = ' '.join([t for t in text.split() if len(t) > 2])
        if len(text) > 0:
            clazz = t['category'] if not binary else 'negative' if t['category']=='undefined' else 'positive'
            texts.append('{}\t{}\t{}'.format(t['tweet_id'],clazz, text))
    return texts

def write(data, folder, file, binary=False):
    create(folder)
    with open("{}/{}".format(folder,file), "w", encoding='utf-8') as f:
        texts = parse(data, binary=binary)
        f.write('\n'.join(texts).strip())

def create(folder, destination="./"):
    if not os.path.exists("{}/{}".format(destination,folder)):
        os.makedirs("{}/{}".format(destination,folder))

def generate(type,ontology):

    data = db.find("annotated", query={"type":type, "ontology":ontology, "dataset":"event 2012", "category":{"$ne":"undefined"}})
    write(data=data,folder="train/{}/{}".format(ontology,type), file='positive.txt', binary=True)

    data = db.find("annotated", query={"type":type, "ontology":ontology, "dataset":"event 2012", "category":"undefined"})
    write(data=data, folder="train/{}/{}".format(ontology, type), file='negative.txt', binary=True)

    data = db.find("annotated", query={"type":type, "ontology":ontology, "dataset":"fsd", "category":{"$ne":"undefined"}})
    write(data=data, folder="test/{}/{}".format(ontology, type), file='positive.txt', binary=True)

    data = db.find("annotated", query={"type":type, "ontology":ontology, "dataset":"fsd", "category":"undefined"})
    write(data=data, folder="test/{}/{}".format(ontology, type), file='negative.txt', binary=True)


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


def generateFileForIds(ids, ontology, type):
    file = "{}_{}.tsv".format(ontology, type)
    data = db.find("annotated", query={"tweet_id": {"$in":ids}, 'ontology':ontology, 'type':type})
    write(data=data,folder='eval',file=file)
    return 'eval/{}'.format(file)


def generateDataFile():
    params = [
        {'ontology': 'dbpedia', 'type': 'generic', 'name': 'dbpedia_generic'},
        {'ontology': 'dbpedia', 'type': 'specific', 'name': 'dbpedia_specific'},
        {'ontology': 'yago', 'type': 'generic', 'name': 'yago_generic'},
        {'ontology': 'yago', 'type': 'specific', 'name': 'yago_specific'},
        {'ontology': 'dbpedia', 'type': 'normal', 'name': 'dbpedia_normal'},
    ]
    categories.append("undefined")
    for cat in categories:
        for config in params:
            config['category'] = cat
            if 'name' in config:
                del config['name']

            buildModelForTrain(config)
            generate(config['type'], config['ontology'])

def createTrainFile(classes, directory, name="neon_train"):
    data = []
    with open(name, "w", encoding='utf-8') as file:
        for index, cl in enumerate(classes):
            with open(os.path.join(directory, "{}.txt".format(cl))) as f:
                position = 0
                for line in f:
                    line = ' '.join(line.split('\t'))
                    line = TextHelper.tokenize(line)
                    if len(line) <=1:
                        continue
                    if position == 0:
                        file.write("{}\t{}".format(index,' '.join(line)))
                    else:
                        file.write("\n{}\t{}".format(index, ' '.join(line)))
                    position+=1


if __name__ == '__main__':
    generateFileForIds(['255923608482881536','255968499887923200'], folder='eval',ontology='dbpedia',type='generic')
