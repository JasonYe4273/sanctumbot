from math import comb

import discord
from discord import app_commands

from util import client, tree, send_error, log_command, ALL
from database import _get_all_db, _get_one_db, _set_db



@tree.command(  # type: ignore[arg-type]
    name="hypergeo",
    description="Hypergeometric calculator",
    guilds=ALL
)
@app_commands.check(log_command)
async def hypergeo(interaction: discord.Interaction, deck_size: int, hits: int, looking_at: int, looking_for: int):
    N = deck_size
    K = hits
    n = looking_at
    k = looking_for
    gt = 0.0
    gte = 0.0
    eq = 0.0
    lte = 0.0
    lt = 0.0

    if n > N:
        await send_error(interaction, "Invalid input; sample must be smaller than population")
    elif K > N:
        await send_error(interaction, "Invalid input; can't have more successes than population")
    elif k > n:
        await send_error(interaction, "Invalid input; can't have more successes than sample")
    elif k > K:
        await send_error(interaction, "Invalid input; can't have more successes than exist")
    else:
        i = 0;
        while i <= n and i <= K:
            if N-K < n-i:
                i += 1
                continue
            psubi = 100 * comb(K, i) * comb(N-K, n-i) / comb(N, n);
            if i < k:
                lt += psubi
            if i == k:
                eq += psubi
            if i > k:
                gt += psubi
            i += 1

        lte = lt + eq
        gte = gt + eq

        msg = f"""
__Hypergeometric for {k} out of {n} cards to be one of {K} hits in a deck of size {N}:__
```P(X < {k}) = {lt:.2f}%
P(X ≤ {k}) = {lte:.2f}%
P(X = {k}) = {eq:.2f}%
P(X ≥ {k}) = {gte:.2f}%
P(X > {k}) = {gt:.2f}%```
"""
        await interaction.response.send_message(msg, ephemeral=False)




@tree.command(  # type: ignore[arg-type]
    name="mana",
    description="Karsten mana number for this mana cost",
    guilds=ALL
)
@app_commands.check(log_command)
async def mana(interaction: discord.Interaction, cost: str):
    KARSTEN = {
        "5C": 9,
        "4C": 9,
        "3C": 10,
        "2C": 12,
        "5CC": 12,
        "1C": 13,
        "4CC": 13,
        "C": 14,
        "3CC": 15,
        "4CCC": 16,
        "2CC": 16,
        "1CC": 18,
        "2CCC": 19,
        "CC": 21,
        "1CCC": 21,
        "1CCCC": 22,
        "CCC": 23,
        "CCCC": 24
    }

    genericidx = 0
    for i in range(len(cost)):
        if not cost[:(i+1)].isnumeric():
            genericidx = i
            break

    if genericidx == 0:
        generic = 0
    else:
        generic = int(cost[:genericidx])
    pips = cost[genericidx:].upper()

    if len(pips) == 0:
        await send_error(interaction, f"Fully gernic mana cost has no requirements")
        return

    uniquepips = {
        "W": 0,
        "U": 0,
        "B": 0,
        "R": 0,
        "G": 0,
        "C": 0
    }
    for p in pips:
        if p not in uniquepips:
            await send_error(interaction, f"Cannot parse mana cost {cost}")
            return
        uniquepips[p] += 1

    reqs = dict()
    for p in uniquepips:
        if uniquepips[p] > 0:
            pcost = str(generic + len(pips) - uniquepips[p]) + "C"*uniquepips[p]
            if pcost[0] == "0":
                pcost = pcost[1:]
            if pcost not in KARSTEN:
                await send_error(interaction, f"No Karsten number for {pcost} (for {p} mana)")
                return
            reqs[p] = KARSTEN[pcost]

    if len(reqs) == 1:
        for p in reqs:
            await interaction.response.send_message(f"Karsten requires __**{reqs[p]} {p}**__ sources for a cost of {cost}", ephemeral=True)
            return
    else:
        msg = "Karsten requires "
        for p in reqs:
            msg += f"__**{reqs[p]+1} {p}**__ sources, "

        pcost = str(generic) + "C"*len(pips)
        if pcost[0] == "0":
            pcost = pcost[1:]
        if pcost in KARSTEN:
            count = f"all {len(reqs)}"
            if len(reqs) == 2:
                count = "both"

            msg += f"and __**{KARSTEN[pcost]} sources of {count}**__  "

        await interaction.response.send_message(msg[:-2]+f" for a cost of {cost}", ephemeral=True)



