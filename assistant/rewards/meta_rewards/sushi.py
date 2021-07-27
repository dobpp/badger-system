from scripts.systems.badger_system import BadgerSystem
from brownie import *
from assistant.subgraph.client import fetch_sushi_harvest_events
from assistant.rewards.classes.RewardsList import RewardsList
from assistant.rewards.meta_rewards.calc_meta_rewards import calc_rewards
from assistant.rewards.rewards_utils import combine_rewards
from helpers.constants import XSUSHI


def calc_all_sushi_rewards(
    badger: BadgerSystem, startBlock: int, endBlock: int, nextCycle: int
):
    allSushiEvents = fetch_sushi_harvest_events()

    wbtcEthRewards = calc_sushi_rewards(
        badger,
        startBlock,
        endBlock,
        nextCycle,
        allSushiEvents["wbtcEth"],
        "native.sushiWbtcEth",
    )
    wbtcBadgerRewards = calc_sushi_rewards(
        badger,
        startBlock,
        endBlock,
        nextCycle,
        allSushiEvents["wbtcBadger"],
        "native.sushiBadgerWbtc",
    )
    wbtcDiggRewards = calc_sushi_rewards(
        badger,
        startBlock,
        endBlock,
        nextCycle,
        allSushiEvents["wbtcDigg"],
        "native.sushiDiggWbtc",
    )

    iBbtcWbtcRewards = calc_sushi_rewards(
        badger,
        startBlock,
        endBlock,
        nextCycle,
        allSushiEvents["iBbtcWbtc"],
        "experimental.sushiIBbtcWbtc",
    )

    # Verify all rewards are correct (for extra safety)
    return combine_rewards(
        [wbtcEthRewards, wbtcBadgerRewards, wbtcDiggRewards, iBbtcWbtcRewards],
        nextCycle,
        badger.badgerTree,
    )


def calc_sushi_rewards(badger, startBlock, endBlock, nextCycle, events, name):
    return calc_rewards(
        badger,
        startBlock,
        endBlock,
        nextCycle,
        events,
        name,
        XSUSHI,
    )
