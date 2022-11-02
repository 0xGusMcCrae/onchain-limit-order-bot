from brownie import *
import os
from dotenv import load_dotenv
import sys
sys.path.append(r"C:\Users\Trevo\Documents\Bots\limit-order-bot\scripts")
from uni import limit_order
import eth_abi.packed
load_dotenv()

#for testing on ganache arbitrum local fork

#this isn't meant to be run, it's a collection of commands I was pasting 
#in the terminal to test manually

#uniswapV3 router cant come from explorer since the returned abi is incorrect due to proxy
router = interface.ISwapRouter(os.getenv('UNI_ROUTER'))
quoter = Contract.from_explorer(os.getenv('UNI_QUOTER'))
usdc = Contract.from_explorer(os.getenv('USDC_ADDRESS'))
weth = Contract.from_explorer(os.getenv('WETH_ADDRESS'))
gmx = Contract.from_explorer(os.getenv('GMX_ADDRESS'))

buyer=accounts[0]
dumper=accounts[1]

#Get DPX and usdc
weth.deposit({'from': buyer, 'value': 100*10**18})
weth.deposit({'from': dumper, 'value': 100*10**18})

weth.approve(router.address,2**256-1,{'from': buyer})
weth.approve(router.address,2**256-1,{'from': dumper})

wethToGmxPath = eth_abi.packed.encode_abi_packed(
        ['address','uint24','address'],
        [weth.address, 3000, gmx.address]
    )
wethToUsdcPath = eth_abi.packed.encode_abi_packed(
        ['address','uint24','address'],
        [weth.address, 3000, usdc.address]
    )
usdcToGmxPath = eth_abi.packed.encode_abi_packed(
        ['address','uint24','address','uint24','address'],
        [usdc.address, 3000, weth.address, 3000, gmx.address]
    )
gmxToUsdcPath = eth_abi.packed.encode_abi_packed(
        ['address','uint24','address','uint24','address'],
        [gmx.address, 3000, weth.address, 3000, usdc.address]
    )

#Buy gmx with weth
router.exactInput(
        (
            wethToGmxPath,          #path
            dumper.address,         #recipient
            1000000000000000,       #deadline
            50*10**weth.decimals(), #amountIn
            0                       #minAmountOut
        ),
        {'from': dumper}
    )
#buy usdc with weth
router.exactInput(
        (
            wethToUsdcPath,         #path
            buyer.address,         #recipient
            1000000000000000,       #deadline
            50*10**weth.decimals(), #amountIn
            0                       #minAmountOut
        ),
        {'from': buyer}
    )

#price of 1 gmx
quoter.quoteExactInput.call(gmxToUsdcPath,1*10**gmx.decimals())*10**-usdc.decimals()

#how many dpx out for this usdc input
quoter.quoteExactInput.call(usdcToGmxPath,5000*10**usdc.decimals())*10**-gmx.decimals()



#set up limit order

#buy order
myOrder = limit_order(gmx.address,5000,True,40,0.3,.03,buyer)
myOrder.main()
#sell order
myOrder = limit_order(gmx.address,gmx.balanceOf(buyer.address)*10**-gmx.decimals(),False,44,0.3,.01,buyer)
myOrder.main()
#dump gmx
gmx.balanceOf(dumper.address)*10**-gmx.decimals()
#approve spend
gmx.approve(router.address,gmx.balanceOf(dumper.address),{'from':dumper})
#swap
router.exactInput(
        (
            gmxToUsdcPath,          #path
            dumper.address,         #recipient
            1000000000000000,       #deadline
            100*10**gmx.decimals(), #amountIn
            0                       #minAmountOut
        ),
        {'from': dumper}
    )