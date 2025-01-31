import discord
from discord import app_commands

from database import con, cur, _get_one_db, _get_all_db, _set_db
from util import client, tree, send_error, TOKEN, SANCTUM_ID, PT_SERVER_ID



import misc
import tournaments
import mythicscraper


# General errors ala https://stackoverflow.com/questions/75812514/how-to-handle-app-command-errors-inside-cogs-discord-py
async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        return await send_error(interaction, f"Command is currently on cooldown! Try again in [1;31m{error.retry_after:.2f}[0;31m seconds!")
    elif isinstance(error, app_commands.MissingPermissions):
        return await send_error(interaction, "You don't have permission to use that command")
    else:
        raise error

tree.on_error = on_tree_error  # type: ignore[method-assign]


@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.id in HANDLING:
        h = HANDLING[reaction.message.id]

        if user.id == h["p1"]["uid"]:
            h["p1"]["reacted"] = True
        if user.id == h["p2"]["uid"]:
            h["p2"]["reacted"] = True

        if h["p1"]["reacted"] and h["p2"]["reacted"]:
            del HANDLING[reaction.message.id]
            await _create_match(h["tid"], h["p1"]["pid"], h["p2"]["pid"])
            await reaction.message.delete()


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=SANCTUM_ID))
    await tree.sync(guild=discord.Object(id=PT_SERVER_ID))
    print("Ready!")
    scrape.start()

client.run(TOKEN)
