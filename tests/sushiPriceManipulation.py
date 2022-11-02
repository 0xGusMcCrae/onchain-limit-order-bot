from brownie import *
import os
from dotenv import load_dotenv
import sys
sys.path.append(r"C:\Users\Trevo\Documents\Bots\limit-order-bot\scripts")
from sushi import limit_order
load_dotenv()

#for testing on ganache arbitrum local fork

#this isn't meant to be run, it's a collection of commands I was pasting 
#in the terminal to test manually

router = Contract.from_explorer(os.getenv('SUSHI_ROUTER'))
usdc = Contract.from_explorer(os.getenv('USDC_ADDRESS'))
weth = Contract.from_explorer(os.getenv('WETH_ADDRESS'))
dpx = Contract.from_explorer(os.getenv('DPX_ADDRESS'))

buyer=accounts[0]
dumper=accounts[1]

#Get DPX and usdc
router.swapExactETHForTokens(
    0,
    [weth.address,dpx.address],
    dumper.address,
    100000000000,
    {'from':dumper, 'value':50*10**18}
)
router.swapExactETHForTokens(
    0,
    [weth.address,usdc.address],
    buyer.address,
    100000000000,
    {'from':buyer, 'value':5*10**18}
)

#price of 1 dpx
router.getAmountsOut(
    1*10**dpx.decimals(),
    [dpx.address,weth.address,usdc.address]
)[-1]*10**-usdc.decimals()

#how many dpx out for this usdc input
router.getAmountsOut(
    5000*10**usdc.decimals(),
    [usdc.address,weth.address,dpx.address]
)[-1]*10**-dpx.decimals()




#set up limit order

#buy order
myOrder = limit_order(dpx.address,5000,True,310,.03,buyer)
myOrder.main()
#sell order
myOrder = limit_order(dpx.address,dpx.balanceOf(buyer.address)*10**-dpx.decimals(),False,330,.01,buyer)
myOrder.main()
#dump dpx
#approve spend
dpx.approve(router.address,dpx.balanceOf(dumper.address),{'from':dumper})
#swap
router.swapExactTokensForETH(
    1*10**dpx.decimals(),
    0,
    [dpx.address,weth.address],
    dumper.address,
    100000000000,
    {'from':dumper}
)