from math import comb

import discord
from discord import app_commands

from util import client, tree, send_error, log_command, SANCTUM_ID, PT_SERVER_ID
from database import _get_all_db, _get_one_db, _set_db



@tree.command(  # type: ignore[arg-type]
    name="hypergeo",
    description="Hypergeometric calculator",
    guilds=[discord.Object(id=SANCTUM_ID),discord.Object(id=PT_SERVER_ID)]
)
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
