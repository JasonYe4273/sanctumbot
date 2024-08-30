import os
import asyncio
import discord
from discord import app_commands
try:
    from secrets import TOKEN, BOT_ID, SANCTUM_ID
except:
    TOKEN = os.environ.get('TOKEN', '')
    BOT_ID = os.environ.get('BOT_ID', '')
    SANCTUM_ID = os.environ.get('SANCTUM_ID', '')
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

def log_command(interaction: discord.Interaction) -> bool:
    print(f"{str(interaction.user)} used /{interaction.command.name}")  # type: ignore[union-attr]
    return True



### UTIL


def _get_one_db(query_str: str):
    try:
        cur.execute(query_str)
        return cur.fetchone()
    except Exception as e:
        cur.execute("ROLLBACK")
        con.commit()
        raise e

def _get_all_db(query_str: str):
    try:
        cur.execute(query_str)
        return cur.fetchall()
    except Exception as e:
        cur.execute("ROLLBACK")
        con.commit()
        raise e

def _set_db(query_str: str):
    try:
        cur.execute(query_str)
        con.commit()
    except Exception as e:
        cur.execute("ROLLBACK")
        con.commit()
        raise e


async def _get_tournament(interaction: discord.Interaction, tid: int):
    tournament = _get_one_db(f"SELECT name FROM tournaments WHERE tid={tid}")
    if not tournament:
        await send_error(interaction, f"Could not find tournament with ID {tid}.")
        return False
    return tournament[0]


async def _get_pid(interaction: discord.Interaction, tid: int):
    user = str(interaction.user)
    player = _get_one_db(f"SELECT pid FROM players WHERE tid={tid} AND username='{user}' AND NOT dropped")
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
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def create_tournament(interaction: discord.Interaction, name: str, description: str):
    _set_db(
        f"""INSERT INTO tournaments (name, description, active, type, channel) VALUES
        ('{name}', '{description}', TRUE, 'async', {interaction.channel_id})"""
    )

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
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def get_players(interaction: discord.Interaction, tid: int, include_dropped: bool, publicize: bool):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    query = f"SELECT pid,username,decklist,wins,losses,draws,dropped FROM players WHERE tid={tid}"
    if not include_dropped:
        query += " AND NOT dropped"
    players = _get_all_db(query)

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

    await interaction.response.send_message(message_str, ephemeral=(not publicize))



@tree.command(  # type: ignore[arg-type]
    name="drop_player",
    description="[ADMIN ONLY] Drop a player from a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def drop_player(interaction: discord.Interaction, tid: int, user: str):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    registered = _get_one_db(f"SELECT pid FROM players WHERE username='{user}' AND tid={tid} AND NOT dropped")
    if not registered:
        await send_error(interaction, f"{user} is not currently registered for this tournament.")
        return

    _set_db(f"UPDATE players SET dropped=TRUE WHERE username='{user}' AND tid={tid}")

    message_str = f"{user} has successfully been dropped from {tournament}."
    await interaction.response.send_message(message_str, ephemeral=True)



### ALL OTHER COMMANDS BELOW



@tree.command(  # type: ignore[arg-type]
    name="tournaments",
    description="Get a list of tournaments",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.check(log_command)
async def tournaments(interaction: discord.Interaction):
    tournaments = _get_all_db("SELECT tid,name,description FROM tournaments WHERE active")

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
@app_commands.check(log_command)
async def register(interaction: discord.Interaction, tid: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    user = str(interaction.user)
    already_registered = _get_one_db(f"SELECT pid FROM players WHERE username='{user}' AND tid={tid} AND NOT dropped")
    if already_registered:
        await send_error(interaction, f"You are already registered for that tournament. You must drop to re-register.")
        return

    _set_db(
        f"""INSERT INTO players (tid, username, uid, wins, losses, draws, dropped) VALUES
        ({tid}, '{user}', {interaction.user.id}, 0, 0, 0, FALSE)""",
    )

    message_str = f"Registered for {tournament}!"
    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="drop",
    description="Drop from a tournament",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.check(log_command)
async def drop(interaction: discord.Interaction, tid: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    _set_db(f"UPDATE players SET dropped=TRUE WHERE pid={pid}")

    message_str = f"You have successfully been dropped from {tournament}."
    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="registrations",
    description="Find all of your tournament registrations",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.check(log_command)
async def registrations(interaction: discord.Interaction, include_dropped: bool):
    registrations = _get_all_db(f"SELECT tournaments.tid,name,decklist,wins,losses,draws,dropped FROM players INNER JOIN tournaments ON players.tid=tournaments.tid WHERE username='{str(interaction.user)}'")

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
@app_commands.check(log_command)
async def submitdeck(interaction: discord.Interaction, tid: int, decklist: str):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    _set_db(f"UPDATE players SET decklist='{decklist}' WHERE pid={pid}")

    message_str = f"[Decklist](<{decklist}>) submitted for {tournament}!"
    await interaction.response.send_message(message_str, ephemeral=True)




HANDLING = dict()  # type: ignore[var-annotated]

@tree.command(  # type: ignore[arg-type]
    name="lfg",
    description="Join the 'looking for games' queue",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.check(log_command)
async def lfg(interaction: discord.Interaction, tid: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    if not _get_one_db(f"SELECT decklist FROM players WHERE pid={pid}")[0]:
        await send_error(interaction, f"You must first submit a decklist for this tournament.")
        return

    if _get_one_db(f"SELECT * FROM queue WHERE tid={tid} AND pid={pid}"):
        await send_error(interaction, f"You are already in the Looking For Games queue for {tournament}.")
        return

    for h in HANDLING:
        if HANDLING[h]["p1"]["pid"] == pid or HANDLING[h]["p2"]["pid"] == pid:
            await send_error(interaction, f"You are already in the process of being matched for {tournament}.")
            return

    if _get_one_db(f"SELECT * FROM matches WHERE tid={tid} AND NOT reported AND (pid1={pid} OR pid2={pid})"):
        await send_error(interaction, f"You are currently in an outstanding match for {tournament}. Please report that match result before re-joining the queue.")
        return

    MAX_MATCHES = 6
    if len(_get_all_db(f"SELECT * FROM matches WHERE tid={tid} AND (pid1={pid} OR pid2={pid})")) >= MAX_MATCHES:
        await send_error(interaction, f"You have already played the maximum number of matches for {tournament}.")
        return

    _set_db(f"INSERT INTO queue (tid, pid) VALUES ({tid}, {pid})")

    message_str = f"You have successfully joined the Looking For Games queue for {tournament}!"
    await interaction.response.send_message(message_str, ephemeral=True)

    await _try_assign_match(tid)



@tree.command(  # type: ignore[arg-type]
    name="leave",
    description="Leave the 'looking for games' queue",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.check(log_command)
async def leave(interaction: discord.Interaction, tid: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    queue_place = _get_one_db(f"SELECT * FROM queue WHERE tid={tid} AND pid={pid}")
    if not queue_place:
        await send_error(interaction, f"You are not in the Looking For Games queue for {tournament}.")
        return

    _set_db(f"DELETE FROM queue WHERE tid={tid} AND pid={pid}")

    message_str = f"You have left the Looking For Games queue for {tournament}."
    await interaction.response.send_message(message_str, ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="queue",
    description="Show the 'looking for games' queue",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.check(log_command)
async def queue(interaction: discord.Interaction, tid: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    queue = _get_all_db(f"SELECT username FROM queue INNER JOIN players ON queue.pid=players.pid WHERE tid={tid}")
    if len(queue) == 0:
        await interaction.response.send_message(f"There is no one in the queue for {tournament}.")
    else:
        message_str = f"The current queue for {tournament} is:"
        for u in queue:
            message_str += f"\n- {u[0]}"
        await interaction.response.send_message(message_str)



@tree.command(  # type: ignore[arg-type]
    name="report",
    description="Report a match result",
    guild=discord.Object(id=SANCTUM_ID)
)
@app_commands.check(log_command)
async def report(interaction: discord.Interaction, tid: int, wins: int, losses: int):
    tournament = await _get_tournament(interaction, tid)
    if not tournament:
        return

    pid = await _get_pid(interaction, tid)
    if not pid:
        return

    match = _get_one_db(f"SELECT mid,pid1,pid2 FROM matches WHERE tid={tid} AND NOT reported AND (pid1={pid} OR pid2={pid})")
    if not match:
        await send_error(interaction, f"You do not have any outstanding matches for this tournament.")

    me_n = 1
    you_n = 2
    op_pid = match[2]
    if match[2] == pid:
        me_n = 2
        you_n = 1
        op_pid = match[1]

    # TODO: result confirmations. for now things are locked once submitted. oh well.

    _set_db(f"UPDATE matches SET reported=TRUE,wins{me_n}={wins},wins{you_n}={losses} WHERE mid={match[0]}")
    if wins > losses:
        w = _get_one_db(f"SELECT wins FROM players WHERE pid={pid}")[0]
        _set_db(f"UPDATE players SET wins={w+1} WHERE pid={pid}")

        l = _get_one_db(f"SELECT losses FROM players WHERE pid={op_pid}")[0]
        _set_db(f"UPDATE players SET losses={l+1} WHERE pid={op_pid}")
    elif wins < losses:
        w = _get_one_db(f"SELECT wins FROM players WHERE pid={op_pid}")[0]
        _set_db(f"UPDATE players SET wins={w+1} WHERE pid={op_pid}")

        l = _get_one_db(f"SELECT losses FROM players WHERE pid={pid}")[0]
        _set_db(f"UPDATE players SET losses={l+1} WHERE pid={pid}")
    else:
        d1 = _get_one_db(f"SELECT draws FROM players WHERE pid={pid}")[0]
        _set_db(f"UPDATE players SET draws={d1+1} WHERE pid={pid}")

        d2 = _get_one_db(f"SELECT draws FROM players WHERE pid={op_pid}")[0]
        _set_db(f"UPDATE players SET draws={d2+1} WHERE pid={op_pid}")

    channel: discord.TextChannel = client.get_channel(_get_one_db(f"SELECT channel FROM tournaments WHERE tid={tid}")[0])  # type: ignore[assignment]
    uid1 = _get_one_db(f"SELECT uid FROM players WHERE pid={pid}")[0]
    uid2 = _get_one_db(f"SELECT uid FROM players WHERE pid={op_pid}")[0]
    
    message_str = f"""
Match result reported:<@{uid1}> {wins}-{losses} <@{uid2}>.
"""
    message = await channel.send(message_str)



### MATCH LOGIC

def _find_matchable_pair(tid: int):
    queue = _get_all_db(f"SELECT pid FROM queue WHERE tid={tid}")
    if len(queue) < 2:
        return False
    for i in queue:
        for j in queue:
            if i[0] == j[0]:
                continue
            already_played = _get_all_db(f"SELECT * FROM matches WHERE pid1={i[0]} AND pid2={j[0]}")
            already_played += _get_all_db(f"SELECT * FROM matches WHERE pid1={j[0]} AND pid2={i[0]}")

            if len(already_played) == 0:
                return (i[0], j[0])

async def _try_assign_match(tid: int):
    # find a matchable pair
    pair = _find_matchable_pair(tid)
    if not pair:
        return

    pid1 = pair[0]
    pid2 = pair[1]

    # remove them from the queue
    _set_db(f"DELETE FROM queue WHERE tid={tid} AND pid={pid1}")
    _set_db(f"DELETE FROM queue WHERE tid={tid} AND pid={pid2}")

    # send message
    channel: discord.TextChannel = client.get_channel(_get_one_db(f"SELECT channel FROM tournaments WHERE tid={tid}")[0])  # type: ignore[assignment]
    tournament = _get_one_db(f"SELECT name FROM tournaments WHERE tid={tid}")[0]
    uid1 = _get_one_db(f"SELECT uid FROM players WHERE pid={pid1}")[0]
    uid2 = _get_one_db(f"SELECT uid FROM players WHERE pid={pid2}")[0]

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

    # wait 5 minutes and then check if still handling this
    await asyncio.sleep(30)
    if message.id not in HANDLING:
        return

    # mark as not handling anymore
    h: dict = HANDLING[message.id]
    del HANDLING[message.id]

    message_str = ""
    if h["p1"]["reacted"] and h["p2"]["reacted"]:
        # if both have reacted create the match
        await message.delete()
        await _create_match(tid, pid1, pid2)
        return
    elif h["p1"]["reacted"]:
        # if only p1 has reacted readd them and remove p2
        if not _get_one_db(f"SELECT * FROM queue WHERE tid={tid} AND pid={pid1}"):
            _set_db(f"INSERT INTO queue (tid, pid) VALUES ({tid}, {pid1})")

        message_str = f"""
<@{uid1}> you have been re-added to the queue for {tournament}.
<@{uid2}> you have been removed from the queue.
"""
    elif h["p2"]["reacted"]:
        # if only p2 has reacted readd them and remove p1
        if not _get_one_db(f"SELECT * FROM queue WHERE tid={tid} AND pid={pid2}"):
            _set_db(f"INSERT INTO queue (tid, pid) VALUES ({tid}, {pid2})")

        message_str = f"""
<@{uid2}> you have been re-added to the queue for {tournament}.
<@{uid1}> you have been removed from the queue.
"""
    else:
        # if neither has reacted remove both from the queue
        message_str = f"""
<@{uid1}> <@{uid2}> you have both been removed from the queue.
"""

    # send the message and delete the original ping.
    notif_message = await channel.send(message_str)
    await message.delete()

    # delete the message after 5 minutes
    await asyncio.sleep(300)
    await notif_message.delete()

async def _create_match(tid: int, pid1: int, pid2: int):
    _set_db(f"INSERT INTO matches (tid, pid1, pid2, reported, wins1, wins2) VALUES ({tid}, {pid1}, {pid2}, FALSE, 0, 0)")

    channel: discord.TextChannel = client.get_channel(_get_one_db(f"SELECT channel FROM tournaments WHERE tid={tid}")[0])  # type: ignore[assignment]
    tournament = _get_one_db(f"SELECT name FROM tournaments WHERE tid={tid}")[0]
    p1 = _get_one_db(f"SELECT uid,username,decklist FROM players WHERE pid={pid1}")
    p2 = _get_one_db(f"SELECT uid,username,decklist FROM players WHERE pid={pid2}")

    message_str = f"""
<@{p1[0]}> <@{p2[0]}> you may now start your match! Don't forget to use the /report command to report after you're done.

Here are your opponent's decklists:
[{p1[1]}](<{p1[2]}>)
[{p2[1]}](<{p2[2]}>)
"""
    message = await channel.send(message_str)



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
