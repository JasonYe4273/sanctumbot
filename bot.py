import discord
from discord import app_commands
from secrets import TOKEN, BOT_ID, SANCTUM_ID
from database import con, cur

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



### ADMIN COMMANDS



@tree.command(  # type: ignore[arg-type]
    name="create_tournament",
    description="Create a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def create_tournament(interaction: discord.Interaction, name: str, description: str):
    cur.execute(
        "INSERT INTO tournaments VALUES(?, ?, ?, ?)", (name, description, True, "swiss")
    )
    con.commit()

    message_str = f"""```ansi
[0;32mTournament created!
    
[1;37mName[0;37m: {name}
[1;37mDescription[0;37m: {description}```"""
    await interaction.response.send_message(message_str, ephemeral=True)


@tree.command(  # type: ignore[arg-type]
    name="get_players",
    description="Get the table of all players in a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def get_players(interaction: discord.Interaction, tid: int):
    tournament = cur.execute(
        f"SELECT name FROM tournaments WHERE rowid={tid}"
    ).fetchone()

    if tournament:
        players = cur.execute(
            f"SELECT rowid,user,decklist,wins,losses,draws,dropped FROM players WHERE tid={tid}"
        ).fetchall()

        message_str = ""
        if len(players) == 0:
            message_str = f"There are no players in {tournament[0]} yet."
        else:
            message_str = f"Here's a list of all the players in the {tournament[0]} tournament:\n```ansi"
            for p in players:
                message_str += f"\n[1;34m{p[1]}[0;34m (ID: {p[0]})[0;37m is {p[3]}-{p[4]}-{p[5]}."
                if p[2]:
                    message_str += f"\nTheir decklist: {p[2]}."
                else:
                    message_str += f"\nThey have [1;31mNOT[0;37m submitted their decklist."
                if p[6]:
                    message_str += "\nThey have [1;31mDROPPED[0;37m."
                message_str += "\n"
            message_str += "```"

        await interaction.response.send_message(message_str, ephemeral=True)
    else:
        await send_error(interaction, f"Could not find tournament with ID {tid}.")



### ALL OTHER COMMANDS BELOW



@tree.command(  # type: ignore[arg-type]
    name="tournaments",
    description="Get a list of tournaments",
    guild=discord.Object(id=SANCTUM_ID)
)
async def tournaments(interaction: discord.Interaction):
    tournaments = cur.execute(
        "SELECT rowid,name,description FROM tournaments WHERE active=true"
    ).fetchall()

    message_str = "Here's a list of active tournaments:\n```ansi"
    for t in tournaments:
        message_str += f"\n[1;34m{t[1]}[0;34m (ID: {t[0]})[0;37m\n{t[2]}\n"
    message_str += "```"

    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="register",
    description="Register for a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
async def register(interaction: discord.Interaction, tid: int):
    tournament = cur.execute(f"SELECT name FROM tournaments WHERE rowid={tid}").fetchone()

    if tournament:
        pid = cur.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?)",
            (tid, str(interaction.user), '', 0, 0, 0, False)).lastrowid
        con.commit()

        message_str = f"Registered for {tournament[0]}! Your player ID is `{pid}` - this is used for various tournament commands."
        await interaction.response.send_message(message_str, ephemeral=True)
    else:
        await send_error(interaction, f"Could not find tournament with ID {tid}.")



@tree.command(  # type: ignore[arg-type]
    name="registrations",
    description="Find all of your active tournament registrations",
    guild=discord.Object(id=SANCTUM_ID)
)
async def registrations(interaction: discord.Interaction):
    registrations = cur.execute(
        f"SELECT players.rowid,name,decklist,wins,losses,draws,dropped FROM players INNER JOIN tournaments ON players.tid=tournaments.rowid WHERE user='{str(interaction.user)}'"
    ).fetchall()

    message_str = "Here's a list of all of your current active player registrations:\n"
    for p in registrations:
        message_str += f"\n__**{p[1]}**__: player ID `{p[0]}`\n"
        if p[2]:
            message_str += f"Your [submitted decklist](<{p[2]}>)."
        else:
            message_str += f"You have not submitted your decklist."
        message_str += f"\nYou are currently {p[3]}-{p[4]}-{p[5]}.\n"
        if p[6]:
            message_str += f"You have DROPPED.\n"

    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="submitdeck",
    description="Submit your decklist for tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
async def submitdeck(interaction: discord.Interaction, pid: int, decklist: str):
    player = cur.execute(f"SELECT * FROM players WHERE rowid={pid}").fetchone()

    if player:
        if player[1] != str(interaction.user):
            await send_error(interaction, f"You do not own that player ID.")
        else:
            tournament = cur.execute(
                f"SELECT name FROM tournaments WHERE rowid={player[0]}"
            ).fetchone()
            cur.execute(f"UPDATE players SET decklist='{decklist}' WHERE rowid={pid}")
            con.commit()

            message_str = f"[Decklist](<{decklist}>) submitted for {tournament[0]}!"
            await interaction.response.send_message(message_str, ephemeral=True)
    else:
        await send_error(interaction, f"Could not find player with ID {pid}.")



@tree.command(  # type: ignore[arg-type]
    name="report",
    description="Report a match result",
    guild=discord.Object(id=SANCTUM_ID)
)
async def report(interaction: discord.Interaction):
    message_str = "Reporting! Implementation TBD."
    await interaction.response.send_message(message_str, ephemeral=True)



### GENERAL BOT STUFF


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
async def on_ready():
    await tree.sync(guild=discord.Object(id=SANCTUM_ID))
    print("Ready!")

client.run(TOKEN)
