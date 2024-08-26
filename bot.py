import asyncio
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



### UTIL


async def _get_tournament(interaction: discord.Interaction, tid: int):
    tournament = cur.execute(f"SELECT name FROM tournaments WHERE rowid={tid}").fetchone()
    if not tournament:
        await send_error(interaction, f"Could not find tournament with ID {tid}.")
        return False
    return tournament[0]


async def _get_pid(interaction: discord.Interaction, tid: int):
    user = str(interaction.user)
    player = cur.execute(f"SELECT rowid FROM players WHERE tid={tid} AND user='{user}' AND dropped=0").fetchone()
    if not player:
        await send_error(interaction, f"You are not registered for this tournament.")
        return False
    return player[0]




### ADMIN COMMANDS



@tree.command(  # type: ignore[arg-type]
    name="create_tournament",
    description="[ADMIN ONLY] Create a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def create_tournament(interaction: discord.Interaction, name: str, description: str):
    cur.execute(
        "INSERT INTO tournaments VALUES(?, ?, ?, ?, ?)", (name, description, True, "async", interaction.channel_id)
    )
    con.commit()

    message_str = f"""```ansi
[0;32mTournament created!
    
[1;37mName[0;37m: {name}
[1;37mDescription[0;37m: {description}```"""
    await interaction.response.send_message(message_str, ephemeral=True)


@tree.command(  # type: ignore[arg-type]
    name="get_players",
    description="[ADMIN ONLY] Get the table of all players in a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def get_players(interaction: discord.Interaction, tid: int, include_dropped: bool):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    query = f"SELECT rowid,user,decklist,wins,losses,draws,dropped FROM players WHERE tid={tid}"
    if not include_dropped:
        query += " AND dropped=0"
    players = cur.execute(query).fetchall()

    message_str = ""
    if len(players) == 0:
        message_str = f"There are no players in {tournament} yet."
    else:
        message_str = f"Here's a list of all the players in the {tournament} tournament:\n```ansi"
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



@tree.command(  # type: ignore[arg-type]
    name="drop_player",
    description="[ADMIN ONLY] Drop a player from a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def drop_player(interaction: discord.Interaction, tid: int, user: str):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    registered = cur.execute(f"SELECT rowid FROM players WHERE user='{user}' AND tid={tid} AND dropped=0").fetchone()
    if not registered:
        await send_error(interaction, f"{user} is not currently registered for this tournament.")
        return

    pid = cur.execute(f"UPDATE players SET dropped=1 WHERE user='{user}' AND tid={tid}").lastrowid
    con.commit()

    message_str = f"{user} has successfully been dropped from {tournament}."
    await interaction.response.send_message(message_str, ephemeral=True)



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
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    user = str(interaction.user)
    already_registered = cur.execute(f"SELECT rowid FROM players WHERE user='{user}' AND tid={tid} AND dropped=0").fetchone()
    if already_registered:
        await send_error(interaction, f"You are already registered for that tournament. You must drop to re-register.")
        return

    pid = cur.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
        (tid, user, interaction.user.id, '', 0, 0, 0, False)).lastrowid
    con.commit()

    message_str = f"Registered for {tournament}!"
    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="drop",
    description="Drop from a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
async def drop(interaction: discord.Interaction, tid: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    cur.execute(f"UPDATE players SET dropped=1 WHERE rowid={pid[0]}").lastrowid
    con.commit()

    message_str = f"You have successfully been dropped from {tournament}."
    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="registrations",
    description="Find all of your tournament registrations",
    guild=discord.Object(id=SANCTUM_ID)
)
async def registrations(interaction: discord.Interaction, include_dropped: bool):
    query = f"SELECT tournaments.rowid,name,decklist,wins,losses,draws,dropped FROM players INNER JOIN tournaments ON players.tid=tournaments.rowid WHERE user='{str(interaction.user)}'"
    registrations = cur.execute(query).fetchall()

    message_str = "Here's a list of all of your current active player registrations:\n"
    for p in registrations:
        if p[6] and not include_dropped:
            continue
        message_str += f"\n__**{p[1]}** (ID: `{p[0]}`)__:\n"
        if p[2]:
            message_str += f"Your [submitted decklist](<{p[2]}>)."
        else:
            message_str += f"You have not submitted your decklist."
        message_str += f"\nYou are currently {p[3]}-{p[4]}-{p[5]}.\n"
        if p[6]:
            message_str += f"You have **DROPPED**.\n"

    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="submitdeck",
    description="Submit your decklist for tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
async def submitdeck(interaction: discord.Interaction, tid: int, decklist: str):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    cur.execute(f"UPDATE players SET decklist='{decklist}' WHERE rowid={pid}")
    con.commit()

    message_str = f"[Decklist](<{decklist}>) submitted for {tournament}!"
    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="lfg",
    description="Join the 'looking for games' queue",
    guild=discord.Object(id=SANCTUM_ID)
)
async def lfg(interaction: discord.Interaction, tid: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    if not cur.execute(f"SELECT decklist FROM players WHERE rowid={pid}").fetchone()[0]:
        await send_error(interaction, f"You must first submit a decklist for this tournament.")
        return

    if cur.execute(f"SELECT * FROM queue WHERE tid={tid} AND pid={pid}").fetchone():
        await send_error(interaction, f"You are already in the Looking For Games queue for {tournament}.")
        return

    cur.execute("INSERT INTO queue VALUES (?, ?)", (tid, pid))
    con.commit()

    message_str = f"You have successfully joined the Looking For Games queue for {tournament}!"
    await interaction.response.send_message(message_str, ephemeral=True)

    await _try_assign_match(tid)



@tree.command(  # type: ignore[arg-type]
    name="leave",
    description="Leave the 'looking for games' queue",
    guild=discord.Object(id=SANCTUM_ID)
)
async def leave(interaction: discord.Interaction, tid: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    queue_place = cur.execute(f"SELECT * FROM queue WHERE tid={tid} AND pid={pid}").fetchone()
    print(queue_place)
    if not queue_place:
        await send_error(interaction, f"You are not in the Looking For Games queue for {tournament}.")
        return

    cur.execute(f"DELETE FROM queue WHERE tid={tid} AND pid={pid}")
    con.commit()

    message_str = f"You have left the Looking For Games queue for {tournament}."
    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="report",
    description="Report a match result",
    guild=discord.Object(id=SANCTUM_ID)
)
async def report(interaction: discord.Interaction):
    message_str = "Reporting! Implementation TBD."
    await interaction.response.send_message(message_str, ephemeral=True)


### MATCH LOGIC

HANDLING = dict()

async def _try_assign_match(tid: int):
    queue = cur.execute(f"SELECT pid FROM queue WHERE tid={tid}").fetchall()
    if len(queue) >= 2:
        pid1 = queue[0][0]
        pid2 = queue[1][0]

        print(pid1, pid2)

        cur.execute(f"DELETE FROM queue WHERE tid={tid} AND pid={pid1}")
        cur.execute(f"DELETE FROM queue WHERE tid={tid} AND pid={pid2}")
        con.commit()


        channel: discord.TextChannel = client.get_channel(cur.execute(f"SELECT channel FROM tournaments WHERE rowid={tid}").fetchone()[0])  # type: ignore[assignment]
        tournament = cur.execute(f"SELECT name FROM tournaments WHERE rowid={tid}").fetchone()[0]
        uid1 = cur.execute(f"SELECT uid FROM players WHERE rowid={pid1}").fetchone()[0]
        uid2 = cur.execute(f"SELECT uid FROM players WHERE rowid={pid2}").fetchone()[0]

        message_str = f"""
<@{uid1}> <@{uid2}> you have been matched in {tournament}!

Please react to this message (with any reaction) to acknowledge that you're able to play your match.

If one or both players have not reacted to this message within the next five minutes, the match will be cancelled, and those who reacted will be readded to the queue.
"""
        message = await channel.send(message_str)
        HANDLING[message.id] = {
            "tid": tid,
            "p1": {
                "pid": pid1,
                "uid": uid1,
                "reacted": False
            },
            "p2": {
                "pid": pid2,
                "uid": uid2,
                "reacted": False
            }
        }

        await asyncio.sleep(30)

        if message.id in HANDLING:
            h: dict = HANDLING[message.id]
            del HANDLING[message.id]

            message_str = ""
            if h["p1"]["reacted"] and h["p2"]["reacted"]:
                await _create_match(tid, pid1, pid2)
                await message.delete()
                return
            elif h["p1"]["reacted"]:
                if not cur.execute(f"SELECT * FROM queue WHERE tid={tid} AND pid={pid1}").fetchone():
                    cur.execute("INSERT INTO queue VALUES (?, ?)", (tid, pid1))
                    con.commit()

                message_str = f"""
<@{uid1}> you have been re-added to the queue for {tournament}.
<@{uid2}> you have been removed from the queue.
"""
            elif h["p2"]["reacted"]:
                if not cur.execute(f"SELECT * FROM queue WHERE tid={tid} AND pid={pid2}").fetchone():
                    cur.execute("INSERT INTO queue VALUES (?, ?)", (tid, pid2))
                    con.commit()

                message_str = f"""
<@{uid2}> you have been re-added to the queue for {tournament}.
<@{uid1}> you have been removed from the queue.
"""
            else:
                message_str = f"""
<@{uid1}> <@{uid2}> you have both been removed from the queue.
"""

            await channel.send(message_str)
            await message.delete()

async def _create_match(tid: int, pid1: int, pid2: int):
    print(f"creating match with {pid1} and {pid2} in {tid}!")




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
    print("Ready!")

client.run(TOKEN)
