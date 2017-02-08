import logging
import sys

def enableLog():
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    return log

def disableLog(log):
    log = logging.getLogger()
    log.setLevel(logging.ERROR)
