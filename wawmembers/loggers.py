# Python Imports
import logging

'''
Various logs. Ideally to be more comprehensive for all actions.
'''

formatter = logging.Formatter('%(asctime)s: %(message)s')

warlogger = logging.getLogger('war')
warlogger.setLevel(logging.INFO)
warhdlr = logging.FileHandler('logs/war.log')
warhdlr.setFormatter(formatter)
warlogger.addHandler(warhdlr)

tradelogger = logging.getLogger('trade')
tradelogger.setLevel(logging.INFO)
tradehdlr = logging.FileHandler('logs/trade.log')
tradehdlr.setFormatter(formatter)
tradelogger.addHandler(tradehdlr)

aidlogger = logging.getLogger('aid')
aidlogger.setLevel(logging.INFO)
aidhdlr = logging.FileHandler('logs/aid.log')
aidhdlr.setFormatter(formatter)
aidlogger.addHandler(aidhdlr)
