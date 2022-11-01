from brownie import *
import os
from dotenv import load_dotenv
import time

load_dotenv()

class limit_order:
    def __init__(self,outputTokenAddress,inputTokenAddress,desiredRatio):
        self.outputToken = Contract.from_explorer(outputTokenAddress)
        self.inputToken = Contract.from_explorer(inputTokenAddress)
        self.ratio = desiredRatio
        self.wethOracle = Contract.from_explorer(os.getenv('WETH_ORACLE'))
        self.router = Contract.from_explorer(os.getenv('UNI_ROUTER'))
        self.quoter = Contract.from_explorer(os.getenv('UNI_QUOTER'))
