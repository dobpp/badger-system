from brownie import interface
from rich.console import Console
from tabulate import tabulate

from helpers.utils import val
from helpers.multicall import Call, as_wei, func
from config.badger_config import digg_decimals
from .StrategyCoreResolver import StrategyCoreResolver

console = Console()


class StrategyDiggRewardsResolver(StrategyCoreResolver):
    # ===== Strategies must implement =====
    def confirm_rebase(self, before, after, value):
        """
        All share values should stay the same.
        bDIGG values should stay the same.
        All DIGG balances should change in proportion to the rebase. (10% towards the new target)
        """
        console.print("=== Compare Rebase ===")
        self.manager.printCompare(before, after)
        # TODO: Impl more accurate rebase checks.
        if value > 10**digg_decimals:
            assert after.balances("digg", "user") > before.balances("digg", "user")
        elif value < 10**digg_decimals:
            assert after.balances("digg", "user") < before.balances("digg", "user")

    def printHarvestState(self, event, keys):
        table = []
        console.print("[blue]== Harvest State ==[/blue]")
        for key in keys:
            table.append([key, val(event[key])])

        print(tabulate(table, headers=["account", "value"]))

    def confirm_harvest_events(self, before, after, tx):
        key = 'HarvestState'
        assert key in tx.events
        assert len(tx.events[key]) == 1
        event = tx.events[key][0]
        keys = [
            'totalDigg',
            'totalShares',
            'totalInitialFragments',
            'diggIncrease',
            'sharesIncrease',
            'scaledSharesIncrease',
        ]
        for key in keys:
            assert key in event

        self.printHarvestState(event, keys)

    def confirm_harvest(self, before, after, tx):
        super().confirm_harvest(before, after, tx)

        # No staking position, strategy want should increase irrespective of
        # current balance.
        # TODO: Add more specific check that the correct reward amount was deposited.
        assert (
            after.get("strategy.balanceOf") >= before.get("strategy.balanceOf")
        )

        # PPFS should not decrease
        assert after.get("sett.pricePerFullShare") >= before.get(
            "sett.pricePerFullShare"
        )

    def confirm_deposit(self, before, after, params):
        """
        Since DIGG is a rebasing token, the amount of shares
        transferred per DIGG changes over time so we need to
        calculated expected shares using the following equation:

        (sharesTransferred * totalSupply) / poolBefore

        Note that shares scale values are scaled down to 18 decimal
        values (e.g. sharesTransferred, poolBefore).
        """
        digg = self.manager.badger.digg.token

        sharesTransferred = after.get("sett.shares") - before.get("sett.shares")
        sharesTransferredFrags = digg.sharesToInitialFragments(sharesTransferred)

        totalSupply = before.get("sett.totalSupply")  # bDIGG is already at 18 decimal scale
        if totalSupply == 0:
            expected_shares = sharesTransferredFrags
        else:
            poolBefore = before.get("sett.shares")
            poolBeforeFrags = digg.sharesToInitialFragments(poolBefore)
            expected_shares = (sharesTransferredFrags * totalSupply) / poolBeforeFrags

        params["expected_shares"] = expected_shares

        # We need to pass in expected_shares to the core resolver so we call the
        # super method down here.
        super().confirm_deposit(before, after, params)

    def add_balances_snap(self, calls, entities):
        sett = self.manager.sett

        # Add FARM token balances.
        digg = interface.IERC20(self.manager.strategy.want())

        calls = self.add_entity_balances_for_tokens(calls, "digg", digg, entities)
        calls = self.add_entity_shares_for_tokens(calls, "digg", digg, entities)
        calls = self.add_entity_balances_for_tokens(calls, "sett", sett, entities)

        return calls

    def get_strategy_destinations(self):
        strategy = self.manager.strategy
        return {
            "diggFaucet": strategy.diggFaucet(),
        }

    def add_strategy_snap(self, calls):
        super().add_strategy_snap(calls)

        sett = self.manager.sett
        strategy = self.manager.strategy

        calls.append(
            Call(
                strategy.diggFaucet(),
                [func.diggFaucet.earned],
                [["diggFaucet.earned", as_wei]],
            )
        )

        # Sett Shares
        calls.append(Call(sett.address, [func.sett.shares], [["sett.shares", as_wei]],))

        # Strategy Shares
        calls.append(
            Call(
                strategy.address,
                [func.strategy.sharesOf],
                [["strategy.sharesOf", as_wei]],
            )
        )
        calls.append(
            Call(
                strategy.address,
                [func.strategy.sharesOfPool],
                [["strategy.sharesOfPool", as_wei]],
            )
        )
        calls.append(
            Call(
                strategy.address,
                [func.strategy.sharesOfWant],
                [["strategy.sharesOfWant", as_wei]],
            )
        )

        return calls
