import discord
from discord import app_commands, Message
from discord.ext import tasks

from database import con, cur, _get_one_db, _get_all_db, _set_db
from util import client, tree, send_error, TOKEN, TEST, DRAFT, SANCTUM, PT

import misc
import tournaments
import mythicscraper
import booster
import notes
import init_limited

from seventeenlands.utils.consts import COMMAND_STR, DATA_QUERY_L, DATA_QUERY_R
from seventeenlands.utils.settings import UPDATING_SETS, OLD_SETS
from seventeenlands.Manamoji import Manamoji
from seventeenlands.message_maker import handle_card_request_v2, handle_command
from seventeenlands.DataCache import DataCache


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
async def on_message(message: Message) -> None:
    """
    Automatically handles what the bot should do when a user sends a message.
    :param message: The sent message.
    """
    # Don't parse own messages
    if message.author == client.user:
        return

    # Handle data queries of the form '{{query | options}}'
    if (DATA_QUERY_L in message.content) and (DATA_QUERY_R in message.content):
        await handle_card_request_v2(message.content, message.channel)

    # Only parse messages that start with command string '17!'
    if message.content.startswith(COMMAND_STR):
        await handle_command(message.content, message.channel)


@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.id in tournaments.HANDLING:
        h = tournaments.HANDLING[reaction.message.id]

        if user.id == h["p1"]["uid"]:
            h["p1"]["reacted"] = True
        if user.id == h["p2"]["uid"]:
            h["p2"]["reacted"] = True

        if h["p1"]["reacted"] and h["p2"]["reacted"]:
            del tournaments.HANDLING[reaction.message.id]
            await _create_match(h["tid"], h["p1"]["pid"], h["p2"]["pid"])
            await reaction.message.delete()



@tasks.loop(minutes=5.0)
async def scrape():
    print("Checking for scrapers...")
    scrapers = _get_all_db("SELECT setcode FROM scraperinfo")
    for s in scrapers:
        await mythicscraper.mythicscraper(client, s[0])


@tasks.loop(hours=12)
async def refresh_data() -> None:
    """
    Refreshes data about the set on a loop.
    """
    DataCache.fetch_data(UPDATING_SETS)


@client.event
async def on_ready():
    await tree.sync(guild=TEST)
    await tree.sync(guild=DRAFT)
    await tree.sync(guild=SANCTUM)
    await tree.sync(guild=PT)

    Manamoji.cache_manamojis(client)
    DataCache.fetch_data(OLD_SETS)

    scrape.start()
    refresh_data.start()

    p1p1s = _get_all_db("SELECT setcode,channel,minutes FROM packtaskloop")
    for p in p1p1s:
        booster.create_pack_taskloop(p[0],p[1],p[2])

    print("Ready!")

client.run(TOKEN)
