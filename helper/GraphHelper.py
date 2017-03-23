import numpy as np
from itertools import cycle
from sklearn.preprocessing import label_binarize
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
import matplotlib.pyplot as plt
from helper import FileHelper
import  matplotlib.pyplot
from sklearn.externals import joblib
colors = cycle(['blue', 'green', 'brown', 'black','navy', 'turquoise', 'darkorange', 'cornflowerblue', 'teal'])
lw = 2

def saveClassifier(clf, name):
    FileHelper.create("models")
    joblib.dump(clf,"models/{}".format(name))

def loadClassifier(name):
    return joblib.load(filename='models/{}'.format(name))

def savePrediction(name, y_score, y_pred, y, classes):
    #y = label_binarize(y, classes=classes)
    FileHelper.create("predictions")
    np.savez_compressed("predictions/{}.npz".format(name), y_score, y_pred, y, classes)


def savePredictionForStatistics(name, ids,labels,preds):
    #y = label_binarize(y, classes=classes)
    FileHelper.create("stat")
    np.savez_compressed("stat/{}.npz".format(name), ids,labels,preds)

def loadPrediction(fileName):
    npz =  np.load("predictions/{}".format(fileName))
    return npz['arr_0'], npz['arr_1'], npz['arr_2'], npz['arr_3']

def loadPredictionStat(fileName):
    npz =  np.load("stat/{}".format(fileName))
    return npz['arr_0'], npz['arr_1'], npz['arr_2']


def loadParameters(y_score, y_pred, y, classes):
    precision = dict()
    recall = dict()
    average_precision = dict()
    n_classes = y.shape[1]
    for i in range(n_classes):
        precision[i], recall[i], _ = precision_recall_curve(y[:, i],
                                                            y_score[:, i])
        average_precision[i] = average_precision_score(y[:, i], y_score[:, i])

    # Compute micro-average ROC curve and ROC area
    precision["micro"], recall["micro"], _ = precision_recall_curve(y.ravel(),
                                                                    y_score.ravel())
    average_precision["micro"] = average_precision_score(y, y_score,
                                                         average="micro")
    return precision,recall,average_precision

def drawGraphPrecRec(models, title='Precision Recall curves'):
    plt = initGraph(title)
    for i, color in zip(range(len(models)), colors):
        model = models[i]
        y_score, y_pred, y, classes = loadPrediction(model['fileName'])
        precision, recall, _ = loadParameters(y_score, y_pred, y, classes)
        plt.plot(recall[0], precision[0], lw=lw, color=color,
                 label=model['label'])

    plt.legend(loc='upper right',
               ncol=1, fancybox=False)
    return plt


def initGraph(title):
    matplotlib.pyplot.figure(
        figsize=(25.0, 25.0))  # The size of the figure is specified as (width, height) in inches

    plt.clf()
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    plt.title(title)
    return plt

def save(plt, name):
    plt.savefig(name, format="pdf",
                facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None,
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)

def drawGraph(model, type='auc', title='Precision Recall Curve', hide = ['Sports']):
    y_score, y_pred, y, classes = loadPrediction(model)
    loadParameters(y_score, y_pred, y, classes)
    n_classes = y.shape[1]

    precision, recall, average_precision = loadParameters(y_score,y_pred, y,classes)
    plt = initGraph(title)

    if type == 'prc':
        # Plot Precision-Recall curve
        plt.plot(recall[0], precision[0], lw=lw, color='navy',
                 label='Precision-Recall curve')
    else:
        # Plot Precision-Recall curve for each class
        plt.plot(recall["micro"], precision["micro"], color='gold', lw=lw,
                 label='micro-average Precision-recall curve (area = {0:0.2f})'
                       ''.format(average_precision["micro"]))
        for i, color in zip(range(n_classes), colors):
            if classes[i] in hide:
                continue
            plt.plot(recall[i], precision[i], color=color, lw=lw,
                     label='{0} (area = {1:0.2f})'
                           ''.format(classes[i], average_precision[i]))

    plt.legend(loc='upper right',
               ncol=1, fancybox=False)
    return plt



