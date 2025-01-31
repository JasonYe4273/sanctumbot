import os
import discord
from discord import app_commands

try:
    from secrets import TOKEN, BOT_ID, SANCTUM_ID
except:
    TOKEN = os.environ.get('TOKEN', '')
    BOT_ID = os.environ.get('BOT_ID', '')
    SANCTUM_ID = os.environ.get('SANCTUM_ID', '')
    PT_SERVER_ID = os.environ.get('PT_SERVER_ID', '')

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def send_error(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(
        f"""```ansi
[2;31m{message}[0m
```""",
        ephemeral=True
    )

def log_command(interaction: discord.Interaction) -> bool:
    print(f"{str(interaction.user)} used /{interaction.command.name}")  # type: ignore[union-attr]
    return True