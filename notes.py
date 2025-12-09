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





