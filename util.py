import os
import discord
from discord import app_commands

try:
    from secrets import TOKEN, BOT_ID, SANCTUM_ID, PT_SERVER_ID, RIFTBOUND_ID, TEST_ID  # type: ignore[attr-defined]
except:
    TOKEN = os.environ.get('TOKEN', '')
    BOT_ID = os.environ.get('BOT_ID', '')
    SANCTUM_ID = os.environ.get('SANCTUM_ID', '')
    PT_SERVER_ID = os.environ.get('PT_SERVER_ID', '')
    RIFTBOUND_IDS = os.environ.get('RIFTBOUND_IDS', '')
    TEST_ID = os.environ.get('TEST_ID', '')
    OTHER_IDS = os.environ.get('OTHER_IDS', '')

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SANCTUM = discord.Object(id=SANCTUM_ID)
PT = discord.Object(id=PT_SERVER_ID)
TEST = discord.Object(id=TEST_ID)
OTHERS = [discord.Object(id=int(i)) for i in OTHER_IDS.split(',')]
MAGIC = [SANCTUM,PT,TEST] + OTHERS
RIFTBOUND = [discord.Object(id=int(i)) for i in RIFTBOUND_IDS.split(',')]
ALL = MAGIC + RIFTBOUND

MAGIC_IDS = [m.id for m in MAGIC]

RIFTBOUND_LEGENDS = [
    "kaisa", "volibear", "jinx", "darius", "ahri", "lee sin", "yasuo", "leona", "teemo", "viktor", "miss fortune", "sett",
    "annie", "lux", "master yi", "garen",
    "rumble", "lucian", "draven", "reksai", "ornn", "jax", "irelia", "azir", "ezreal", "renata glasc", "sivir", "fiora",
    "jhin", "rengar", "pyke", "vi", "lilia", "master yi wm", "vex", "ivern", "diana", "leblanc", "khazix", "poppy"
    "kennen", "akali", "renekton", "zed", "mel", "ambessa"]

headers = {"User-Agent": "SanctumBot/1.0"}


async def send_error(interaction: discord.Interaction, message: str):
    if interaction and not interaction.response.is_done():
        await interaction.response.send_message(
            f"""```ansi
[2;31m{message}[0m
```""",
            ephemeral=True
        )

async def send_long_msg(interaction: discord.Interaction, message: str):
    if interaction and not interaction.response.is_done() and interaction.channel_id:
        channel = client.get_channel(interaction.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await send_error(interaction, "Not a text channel")
            return

        lines = message.split('\n')
        i = 0

        for l in lines:
            if len(l) >= 2000:
                await send_error(interaction, "Single line of response too long, contact Jason")
                return

        chunks = []
        while i < len(lines):
            chunk = ""
            while i < len(lines) and len(chunk) + len(lines[i]) < 2000:
                chunk += lines[i] + '\n'
                i += 1
            chunks.append(chunk)

        for i in range(len(chunks)):
            if i == 0:
                await interaction.response.send_message(chunks[0])
            else:
                await channel.send(chunks[i])

def log_command(interaction: discord.Interaction) -> bool:
    print(f"{str(interaction.user)} used /{interaction.command.name}")  # type: ignore[union-attr]
    return True



