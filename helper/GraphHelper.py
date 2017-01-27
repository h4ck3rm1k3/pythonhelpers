import numpy as np
from itertools import cycle
from sklearn.preprocessing import label_binarize
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
import matplotlib.pyplot as plt
from helper import FileHelper
from sklearn.externals import joblib


def saveClassifier(clf, name):
    FileHelper.create("models")
    joblib.dump(clf,"models/{}".format(name))

def savePrediction(name, y_score, y_pred, y, classes):
    y = label_binarize(y, classes=classes)
    FileHelper.create("predictions")
    np.savez_compressed("predictions/{}.npz".format(name), y_score, y_pred, y, classes)

def loadPrediction(fileName):
    return np.load("predictions/{}".format(fileName))
    #y_score, y_pred, y, classes = npz['arr_0'], npz['arr_1'], npz['arr_2'], npz['arr_3']

def drawGraph(y_score, y_pred, y, classes ):
    n_classes = y.shape[1]
    colors = cycle(['navy', 'turquoise', 'darkorange', 'cornflowerblue', 'teal'])
    lw = 2
    classes = ["Accidents", "Arts", "Attacks", "Economy", "Miscellaneous", "Politics", "Science"]

    precision = dict()
    recall = dict()
    average_precision = dict()
    # print(n_classes, test_labels.shape[1])
    # print(n_classes, y_pred.shape[1])
    for i in range(n_classes):
        precision[i], recall[i], _ = precision_recall_curve(y[:, i],
                                                            y_score[:, i])
        average_precision[i] = average_precision_score(y[:, i], y_score[:, i])

    # Compute micro-average ROC curve and ROC area
    precision["micro"], recall["micro"], _ = precision_recall_curve(y.ravel(),
                                                                    y_score.ravel())
    average_precision["micro"] = average_precision_score(y, y_score,
                                                         average="micro")

    # Plot Precision-Recall curve
    plt.clf()
    plt.plot(recall[0], precision[0], lw=lw, color='navy',
             label='Precision-Recall curve')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    plt.title('Precision-Recall Curve: AUC={0:0.2f}'.format(average_precision[0]))
    plt.legend(loc="upper right")
    plt.savefig('{}_prc.svg'.format("test"), format="svg",
                facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None,
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)
    # plt.show()


    # Plot Precision-Recall curve for each class
    plt.clf()
    plt.plot(recall["micro"], precision["micro"], color='gold', lw=lw,
             label='micro-average Precision-recall curve (area = {0:0.2f})'
                   ''.format(average_precision["micro"]))
    for i, color in zip(range(n_classes), colors):
        plt.plot(recall[i], precision[i], color=color, lw=lw,
                 label='{0} (area = {1:0.2f})'
                       ''.format(classes[i], average_precision[i]))

    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall curve for model {}'.format("test"))
    plt.legend(loc='upper right',
               ncol=1, fancybox=False)
    return plt



