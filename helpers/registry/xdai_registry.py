import json

from helpers.registry.ChainRegistry import ChainRegistry
from helpers.registry.YearnRegistry import YearnRegistry
from brownie.network import web3
from dotmap import DotMap
from helpers.registry.WhaleRegistryAction import WhaleRegistryAction
import json

sushi_registry = DotMap(
    sushiToken="0x6b3595068778dd592e39a122f4f5a5cf09c90fe2",
    xsushiToken="0x8798249c2E607446EfB7Ad49eC89dD1865Ff4272",
    symbol="SUSHI",
    symbol_xsushi="XSUSHI",
    sushiChef="0xc2EdaD668740f1aA35E4D8f227fB8E17dcA888Cd",
    router="0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    factory="0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
    lpTokens=DotMap(
        sushiBadgerWBtc="0x110492b31c59716AC47337E616804E3E3AdC0b4a",
        sushiWbtcWeth="0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58",
    ),
    pids=DotMap(sushiBadgerWBtc=73, sushiEthWBtc=21),
)

xdai_registry = ChainRegistry(
    sushiswap=sushi_registry,
    sushi=sushi_registry,
)