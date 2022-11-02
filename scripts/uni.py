from brownie import *
import os
from dotenv import load_dotenv
import time
import eth_abi.packed

load_dotenv()

class limit_order:
    #token = token address 
    #amount of token to buy/sell (NOT accounting for decimals)  i.e. 1 to sell 1 dpx or 2500 to buy tokens with 2500 usdc
    #buy = true, false for sell
    #desired price in USD (per token)
    #max slippage in decimals (i.e. .01 is 1%)
    #uniV3 pool fee as a percentage i.e. 0.3 for 0.3%
    def __init__(self,token,amount,buy,desiredPrice,poolFee=0.3,maxSlippage=.01,user=accounts[0]):
        #Check for valid inputs
        assert amount > 0, 'Input should be positive'
        assert type(buy) == type(True), 'buy parameter must be a boolean value'
        assert token != os.getenv('USDC_ADDRESS'), 'token should not be usdc'
        #ensure valid poolFee

        
        self.user=user
        self.token = Contract.from_explorer(token)
        self.maxSlippage = maxSlippage
        self.poolFee = int(poolFee * 10000) #0.3% pool fee is represented as 3000
        self.router = interface.ISwapRouter(os.getenv('UNI_ROUTER'))
        self.quoter = Contract.from_explorer(os.getenv('UNI_QUOTER'))
        self.weth = Contract.from_explorer(os.getenv('WETH_ADDRESS'))
        self.usdc = Contract.from_explorer(os.getenv('USDC_ADDRESS'))
        if buy:
            self.amount = amount*10**self.usdc.decimals()
        else:
            self.amount = amount*10**self.token.decimals()
        self.limitPrice = desiredPrice*10**self.usdc.decimals()
        self.buy = buy #true or false
        self.executed = False #to stop the bot once swap is executed

        


    def main(self):
        path = self.getPath()
        #token spend approval for the router
        if self.buy:
            self.usdc.approve(
                self.router.address,
                2**256-1,
                {'from': self.user}
            )
        else:
            self.token.approve(
                self.router.address,
                2**256-1,
                {'from': self.user}
            )
        
        while not self.executed:
            time.sleep(1)
            latestPrice = self.getPrice(path)
            print(f'\nLatest price: {latestPrice}')
            print(f"Desired Price: {self.limitPrice}")

            delta = abs(self.limitPrice - latestPrice)
            print(f"Delta: {delta}")

            slippage = delta/self.limitPrice
            print(f"Slippage: {slippage}")
            
            if slippage <= self.maxSlippage:
                minAmountOut = 0 #change this
                self.executeSwap(minAmountOut,path)
                print("Swap completed")
                self.executed=True
            


    def executeSwap(self, _amountOutMin, _path):
        if self.buy:    
            self.router.exactInput(
                (
                    _path,                  #path
                    self.user.address,      #recipient
                    1000000000000000,       #deadline
                    self.amount,            #amountIn
                    _amountOutMin           #minAmountOut
                ),
                {'from': self.user}
            )
        else: #Some token sells were failing if the sell amount was the wallet's whole token balance
            self.router.exactInput(
                (
                    _path,                              #path
                    self.user.address,                  #recipient
                    1000000000000000,                   #deadline
                    .9999999999999999*self.amount,      #amountIn
                    _amountOutMin                       #minAmountOut 
                ),
                {'from': self.user}
            )
        
    #calcualate the price per token
    def getPrice(self, path):
        if self.buy:
            #calculate tokens out from amount in, divide amount in by amount out to get unit price
            amountOut=self.quoter.quoteExactInput.call(path, self.amount)*10**-self.token.decimals() #do I need the [-1]?
            return self.amount/amountOut
        else:
            return self.quoter.quoteExactInput.call(path, self.amount)/((self.amount*10**-self.token.decimals()))

    def getPath(self): 
        if self.buy and self.token.address != self.weth.address:
            path = eth_abi.packed.encode_abi_packed(
                ['address','uint24','address','uint24','address'],
                [self.usdc.address, self.poolFee, self.weth.address, self.poolFee, self.token.address]
            )
        elif self.buy and self.token.address == self.weth.address:
            path = eth_abi.packed.encode_abi_packed(
                ['address','uint24','address'],
                [self.usdc.address, self.poolFee, self.weth.address]
            )
        elif not self.buy and self.token.address != self.weth.address:
            path = eth_abi.packed.encode_abi_packed(
                ['address','uint24','address','uint24','address'],
                [self.token.address, self.poolFee, self.weth.address, self.poolFee, self.usdc.address]
            )
        elif not self.buy and self.token.address == self.weth.address:
            path = eth_abi.packed.encode_abi_packed(
                ['address','uint24','address'],
                [self.weth.address, self.poolFee, self.usdc.address]
            )
        else:
            raise Exception("Invalid parameters - check 'buy' and token addresses")
        
        return path