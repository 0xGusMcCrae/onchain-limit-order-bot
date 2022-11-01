from brownie import *
import os
from dotenv import load_dotenv
import time

load_dotenv()

class limit_order:
    #token = token address 
    #amount of token to buy/sell (NOT accounting for decimals)  i.e. 1 to sell 1 dpx or 2500 to buy tokens with 2500 usdc
    #buy = true, false for sell
    #desired price in USD (per token)
    #max slippage in decimals (i.e. .01 is 1%)
    def __init__(self,token,amount,buy,desiredPrice,maxSlippage=.01,user=accounts[0]):
        #Check for valid inputs
        assert amount > 0, 'Input should be positive'
        assert type(buy) == type(True), 'buy parameter must be a boolean value'
        assert token != os.getenv('USDC_ADDRESS'), 'token should not be usdc'

        
        self.user=user
        self.token = Contract.from_explorer(token)
        self.maxSlippage = maxSlippage
        self.router = Contract.from_explorer(os.getenv('SUSHI_ROUTER'))
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
                self.amount*(1+self.maxSlippage),
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
            #i need to convert the limit price since it is for just one 
            #token whereas latestPrice is for the whole thing. Or I can 
            #just convert latestPrice to a single token
            print(f"Delta: {delta}")

            slippage = delta/self.limitPrice
            print(f"Slippage: {slippage}")
            
            if slippage <= self.maxSlippage:
                minAmountOut = 0
                self.executeSwap(minAmountOut,path)
                print("Swap completed")
                self.executed=True
            


    def executeSwap(self, _amountOutMin, _path):
        if self.buy:    
            self.router.swapExactTokensForTokens(
                self.amount,            #amountIn
                _amountOutMin,          #amountOutMin
                _path,                  #path
                self.user.address,      #to
                1000000000000000,       #deadline
                {'from': self.user}
            )
        else: #Some token sells were failing if the sell amount was the wallet's whole token balance
            self.router.swapExactTokensForTokens(
                .9999999999999999*self.amount,        #I need to figure out why this works (and adding another 9 doesnt)  
                _amountOutMin,                        
                _path,                                   
                self.user.address,    
                1000000000000000,     
                {'from': self.user}
            )
        
    #calcualate the price per token
    def getPrice(self, path):
        if self.buy:
            #calculate tokens out from amount in, divide amount in by amount out to get unit price
            amountOut=self.router.getAmountsOut(self.amount,path)[-1]*10**-self.token.decimals()
            return self.amount/amountOut
        else:
            return self.router.getAmountsOut(self.amount,path)[-1]/((self.amount*10**-self.token.decimals()))#*10**-self.usdc.decimals())

    def getPath(self):
        if self.buy and self.token.address != self.weth.address:
            path = [self.usdc.address, self.weth.address, self.token.address]
        elif self.buy and self.token.address == self.weth.address:
            path = [self.usdc.address, self.weth.address]
        elif not self.buy and self.token.address != self.weth.address:
            path = [self.token.address, self.weth.address, self.usdc.address]
        elif not self.buy and self.token.address == self.weth.address:
            path = [self.weth.address, self.usdc.address]
        else:
            raise Exception("Invalid parameters - check 'buy' and token addresses")
        
        return path