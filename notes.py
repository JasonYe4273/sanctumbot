from datetime import datetime

import discord
from discord import app_commands

from util import client, tree, send_error, log_command, ALL
from database import _get_all_db, _get_one_db, _set_db



@tree.command(  # type: ignore[arg-type]
    name="notes",
    description="Record Testing Notes",
    guilds=ALL
)
@app_commands.check(log_command)
async def notes(interaction: discord.Interaction, opponent: str, deck1: str, deck2: str, winloss: str):
    deck1 = deck1.lower()
    deck2 = deck2.lower()

    player = str(interaction.user)
    msg = f"""# Notes for {player} on {deck1} vs {opponent} on {deck2}:
**RECORD**: {winloss} 
"""
    await interaction.response.send_message(msg)
    resp = await interaction.original_response()
    url = resp.jump_url

    _set_db(
        f"""INSERT INTO notes (server, message, player, opponent, deck1, deck2, winloss, recorded_at) VALUES
        ({interaction.guild_id}, '{url}', '{player}', '{opponent}', '{deck1}', '{deck2}', '{winloss}', {int(datetime.now().timestamp())})"""
    )

    if interaction.guild_id:
        await update_deck_names(interaction.guild_id)


@tree.command(  # type: ignore[arg-type]
    name="search_notes",
    description="Search Testing Notes",
    guilds=ALL
)
@app_commands.check(log_command)
async def search_notes(interaction: discord.Interaction, deck: str):
    deck = deck.lower()

    notes = _get_all_db(f"SELECT message,player,opponent,deck1,deck2,winloss,recorded_at FROM notes WHERE server={interaction.guild_id} AND (deck1='{deck}' OR deck2='{deck}')")
    if len(notes) == 0:
        await interaction.response.send_message(f"No testing notes found for {deck}")
        return

    for note in notes:
        msg = f"{len(notes)} sets of testing notes found for {deck}:\n"
        for note in notes:
            msg += f"- {note[1]} on {note[3]} vs {note[2]} on {note[4]} ({note[5]}) @ <t:{note[6]}:s>: {note[0]}\n"
        await interaction.response.send_message(msg)


@tree.command(  # type: ignore[arg-type]
    name="create_deck_names_pin",
    description="Create auto-updated message to pin as list of deck names",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def create_deck_names_pin(interaction: discord.Interaction):
    await interaction.response.send_message("# List of Deck Names:")
    resp = await interaction.original_response()

    if _get_one_db(f"SELECT message FROM deck_names WHERE server={interaction.guild_id}"):
        _set_db(f"UPDATE deck_names SET channel={interaction.channel_id} WHERE server={interaction.guild_id}")
        _set_db(f"UPDATE deck_names SET message={resp.id} WHERE server={interaction.guild_id}")
    else:
        _set_db(f"INSERT INTO deck_names (server, channel, message) VALUES ({interaction.guild_id}, {interaction.channel_id}, {resp.id})")

    if interaction.guild_id:
        await update_deck_names(interaction.guild_id)

    await interaction.response.send_message("Done!", ephemeral=True)


@tree.command(  # type: ignore[arg-type]
    name="reload_deck_names",
    description="Reload pinned deck names message",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def reload_deck_names(interaction: discord.Interaction):
    if interaction.guild_id:
        await update_deck_names(interaction.guild_id)
    await interaction.response.send_message("Done!", ephemeral=True)


async def update_deck_names(server: int):
    mid = _get_one_db(f"SELECT message FROM deck_names WHERE server={server}")[0]
    cid = _get_one_db(f"SELECT channel FROM deck_names WHERE server={server}")[0]
    channel: discord.TextChannel = client.get_channel(cid)  # type: ignore[assignment]
    message: discord.Message = await channel.fetch_message(mid)

    if message:
        deck1s = _get_all_db(f"SELECT deck1 FROM notes WHERE server={server}")
        deck2s = _get_all_db(f"SELECT deck2 FROM notes WHERE server={server}")

        decks = []
        for d in deck1s:
            if d not in decks:
                decks.append(d[0])
        for d in deck2s:
            if d not in decks:
                decks.append(d[0])

        msg = "# List of Deck Names:\n"
        for d in decks:
            msg += f"- {d}\n"

        await message.edit(content=msg)





