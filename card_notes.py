from datetime import datetime

import discord
from discord import app_commands

from util import client, tree, send_error, send_long_msg, log_command, ALL
from database import _get_all_db, _get_one_db, _set_db



CARD_CACHE = list()



async def card_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    subseq = re.compile('.*'.join(re.escape(x) for x in current.lower()))
    return [
        app_commands.Choice(name=n, value=n)
        for n in CARD_CACHE
        if subseq.search(n.lower())
    ][:10]

@tree.command(  # type: ignore[arg-type]
    name="add_card_note",
    description="Record notes on a limited card",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.autocomplete(card=card_autocomplete)
async def add_card_note(interaction: discord.Interaction, your_name: str, card: str, note: str):
    _set_db(
        f"""INSERT INTO card_notes (server, card, note, recorded_by, recorded_at) VALUES
        ({interaction.guild_id}, '{card.lower()}', '{note}', '{your_name}', {int(datetime.now().timestamp())})"""
    )

    await interaction.response.send_message("Recorded!", ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="card_notes",
    description="Get all notes on a limited card",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.autocomplete(card=card_autocomplete)
async def card_notes(interaction: discord.Interaction, card: str):
    notes = _get_all_db(f"SELECT note,recorded_by,recorded_at FROM card_notes WHERE server={interaction.guild_id} AND card='{card.lower()}'")
    if len(notes) == 0:
        await interaction.response.send_message(f"No notes found for {card}")
        return

    msg = f"{len(notes)} sets of notes found for {card}:\n"
    for note in notes:
        msg += f"- {note[0]} - {note[1]} @ <t:{note[2]}:s>:\n"
    await send_long_msg(interaction, msg)