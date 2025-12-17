import os
import discord
from discord import app_commands

try:
    from secrets import TOKEN, BOT_ID, SANCTUM_ID, PT_SERVER_ID, TEST_ID  # type: ignore[attr-defined]
except:
    TOKEN = os.environ.get('TOKEN', '')
    BOT_ID = os.environ.get('BOT_ID', '')
    SANCTUM_ID = os.environ.get('SANCTUM_ID', '')
    PT_SERVER_ID = os.environ.get('PT_SERVER_ID', '')
    TEST_ID = os.environ.get('TEST_ID', '')
    DRAFT_ID = os.environ.get('DRAFT_ID', '')

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SANCTUM = discord.Object(id=SANCTUM_ID)
PT = discord.Object(id=PT_SERVER_ID)
TEST = discord.Object(id=TEST_ID)
DRAFT = discord.Object(id=DRAFT_ID)
ALL = [SANCTUM,PT,TEST,DRAFT]


async def send_error(interaction: discord.Interaction, message: str):
    if interaction and not interaction.response.is_done():
        await interaction.response.send_message(
            f"""```ansi
[2;31m{message}[0m
```""",
            ephemeral=True
        )

def log_command(interaction: discord.Interaction) -> bool:
    print(f"{str(interaction.user)} used /{interaction.command.name}")  # type: ignore[union-attr]
    return True