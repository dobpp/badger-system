from assistant.rewards.rewards_utils import calculate_sett_balances
from assistant.rewards.classes.RewardsList import RewardsList
from helpers.time_utils import days,to_days,to_hours,to_utc_date
from dotmap import DotMap
from brownie import *
from rich.console import Console

console = Console()
digg_token = "0x798D1bE841a82a273720CE31c822C61a67a601C3"
digg = interface.IDigg(digg_token)


def calc_geyser_snapshot(badger, name, startBlock, endBlock, nextCycle):
    console.log("Processing rewards for {}".format(name))
    rewards = RewardsList(nextCycle, badger.badgerTree)
    sett = badger.getSett(name)
    geyser = badger.getGeyser(name)
    startTime = web3.eth.getBlock(startBlock)["timestamp"]
    endTime = web3.eth.getBlock(endBlock)["timestamp"]

    balances = calculate_sett_balances(badger, name, sett, endBlock)
    unlockSchedules = {}
    for token in geyser.getDistributionTokens():
        unlockSchedules = parse_schedules(geyser.getUnlockSchedulesFor(token))
        tokenDistribution = int(
            get_distributed_for_token_at(token, endTime, unlockSchedules, name)
            - get_distributed_for_token_at(token, startTime, unlockSchedules, name)
        )
        # Distribute to users with rewards list
        # Make sure there are tokens to distribute (some geysers only 
        # distribute one token)
        if token == digg_token:
            console.log(
                "{} DIGG tokens distributed".format(
                digg.sharesToFragments(tokenDistribution)/1e18)
            )
        else:
            console.log(
                "{} Badger tokens distributed".format(
                tokenDistribution/1e18)
            )
 
        if tokenDistribution > 0:
            rewardsUnit = tokenDistribution/sum(balances.values())
            for addr, balance in balances.items():
                #  Add badger boost here (for non native setts)
                rewards.increase_user_rewards(addr, token, balance*rewardsUnit)

    return rewards


def get_distributed_for_token_at(token, endTime, schedules, name):
    totalToDistribute = 0
    for index, schedule in enumerate(schedules):
        if endTime < schedule["startTime"]:
            toDistribute = 0
            console.log("\nSchedule {} for {} completed\n".format(index, name))
        else:
            rangeDuration = endTime - schedule["startTime"]
            toDistribute = min(
                schedule["initialTokensLocked"],
                int(
                    schedule["initialTokensLocked"]
                    * rangeDuration
                    // schedule["duration"]
                ),
            )
            if schedule["startTime"] <= endTime and schedule["endTime"] >= endTime:
                console.log("Tokens distributed by schedule {} at {} are {} out of {}, or {}% of total\n"
                .format(
                        index,
                        to_utc_date(schedule["startTime"]),
                        digg.sharesToFragment(toDistribute),
                        digg.sharesToFragment(schedule["initialTokensLocked"]),
                        (int(toDistribute)/int(schedule["initialTokensLocked"])) * 100
                    )
                )
                console.log(
                            "Total duration of schedule elapsed is {} hours out of {} hours, or {}% of total duration.\n"
                            .format(
                                to_hours(rangeDuration),
                                to_hours(schedule["duration"]),
                                rangeDuration / schedule["duration"] * 100
                            )
                        )
            
        totalToDistribute += toDistribute
    return totalToDistribute


def parse_schedules(schedules):
    parsedSchedules = []
    for schedule in schedules:
        parsedSchedules.append(
            {
                "initialTokensLocked": schedule[0],
                "endTime": schedule[1],
                "duration": schedule[2],
                "startTime": schedule[3],
            }
        )
    return parsedSchedules
