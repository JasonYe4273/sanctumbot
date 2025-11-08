import json
import requests
from random import randint
from typing import Optional

import discord
from discord import app_commands
from discord.ext import tasks

from util import client, tree, send_error, log_command, ALL
from database import _get_all_db, _get_one_db, _set_db

SEALED_DATA = dict()
def fetch_sealed_data():
  try:
    # TEMP TLA DATA
    with open("tla.json") as f:
      SEALED_DATA["TLA"] = json.load(f)

    resp = requests.get("https://raw.githubusercontent.com/taw/magic-sealed-data/refs/heads/master/sealed_basic_data.json")
    for s in resp.json():
      if s["code"][-5:] == "draft" or s["code"][-4:] == "play":
        SEALED_DATA[s["set_code"].upper()] = s

    print("Fetched sealed_basic_data!")
    return True
  except:
    print("Failed to fetch sealed_basic_data")
    return False
fetch_sealed_data()

SET_CACHE = dict()  # type: ignore[var-annotated]


async def generate_pack(interaction: Optional[discord.Interaction], setcode: str) -> list[list[str], str]:
  if not SEALED_DATA:
    if not fetch_sealed_data():
      if interaction:
        await send_error(interaction, f"Error loading pack data")
      return []

  setcode = setcode.upper()
  if setcode not in SEALED_DATA:
    if interaction:
      await send_error(interaction, f"Cannot find a draft set with code {setcode}")
    return []

  boosters = SEALED_DATA[setcode]["boosters"]
  booster = boosters[0]
  sheets = SEALED_DATA[setcode]["sheets"]

  # select kind of booster
  total_weight = 0
  for b in boosters:
    total_weight += b["weight"]

  r = randint(1,total_weight)
  weight = 0
  for b in boosters:
    weight += b["weight"]
    if r <= weight:
      booster = b
      break


  # generate sheets
  pack: list[str] = []
  for s in booster["sheets"]:
    # generate packlet for a group of sheets
    packlet: list[str] = []
    total_weight = sheets[s]["total_weight"]
    for i in range(booster["sheets"][s]):
      weight = 0
      card = ""
      r = randint(1, total_weight)
      for c in sheets[s]["cards"]:
        # duplicate protection within a group
        if c in packlet:
          continue
        weight += sheets[s]["cards"][c]
        if r <= weight:
          total_weight -= sheets[s]["cards"][c]
          card = c
          break
      packlet.append(card)
    pack += packlet

  scryfall = f"https://scryfall.com/search?q="
  pack_names: list[str] = []
  for i in range(len(pack)):
    set_cn = pack[i].split(":")
    set_ = set_cn[0].upper()
    cn = set_cn[1]

    set_cards = dict()
    if set_ in SET_CACHE:
      set_cards = SET_CACHE[set_]
    else:
      try:
        print(set_)
        resp = requests.get(f"https://mtgjson.com/api/v5/{set_}.json")
        print(f"Fetched {set_} JSON!")
        for c in resp.json()["data"]["cards"]:
          set_cards[c["number"]] = c["name"]
      except:
        if interaction:
          print(f"error: {set_cn}")
          await send_error(interaction, f"Error loading card data")
        return []
      SET_CACHE[set_] = set_cards

    if not cn.isdigit() and cn[:-1].isdigit():
      cn = cn[:-1]
    if cn not in set_cards:
      if set_cn == "tla:115":
        pack_names.append("Pirate Peddlers")
      elif set_cn == "tla:138":
        pack_names.append("Firebending Lesson")
      elif set_cn == "tla:250":
        pack_names.append("Wandering Musicians")
      else:
        pack_names.append(pack[i])
    else:
      pack_names.append(set_cards[cn])

    scryfall += f"%28cn%3D{cn}+e%3D{set_}%29"
    if i < len(pack)-1:
      scryfall += f"+or+"

  return [pack_names, scryfall]


@tree.command(  # type: ignore[arg-type]
    name="create_p1p1_loop",
    description="[ADMIN ONLY] Create a p1p1 task loop in this channel",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def create_p1p1_loop(interaction: discord.Interaction, setcode: str, minutes: int):
    _set_db(f"INSERT INTO packtaskloop (setcode,channel,minutes) VALUES ('{setcode.upper()}',{interaction.channel_id},{minutes})")
    create_pack_taskloop(setcode, interaction.channel_id, minutes)  # type: ignore[arg-type]
    await interaction.response.send_message(f"{setcode} p1p1 task loop created!", ephemeral=True)



# @tree.command(  # type: ignore[arg-type]
#     name="get_p1p1_loops",
#     description="[ADMIN ONLY] See all p1p1 loops in this channel",
#     guilds=ALL
# )
# @app_commands.check(log_command)
# @app_commands.checks.has_permissions(administrator=True)
# async def get_p1p1_loops(interaction: discord.Interaction):
#     p1p1s = _get_all_db(f"SELECT setcode,channel,minutes FROM packtaskloop")
#     await interaction.response.send_message(str(p1p1s), ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="delete_p1p1_loop",
    description="[ADMIN ONLY] Delete all p1p1 task loops of a set from this channel",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def delete_p1p1_loop(interaction: discord.Interaction, setcode: str):
  _set_db(f"DELETE FROM packtaskloop WHERE setcode='{setcode.upper()}' AND channel={interaction.channel_id}")
  await interaction.response.send_message(f"All {setcode} p1p1 task loops deleted!", ephemeral=True)

  if interaction.channel_id in PACK_TASK_LOOPS and setcode in PACK_TASK_LOOPS[interaction.channel_id]:
    for tl in PACK_TASK_LOOPS[interaction.channel_id][setcode]:
      tl.stop()



@tree.command(  # type: ignore[arg-type]
    name="p1p1",
    description="Pack 1 Pick 1 from the specified set",
    guilds=ALL
)
@app_commands.check(log_command)
async def p1p1(interaction: discord.Interaction, setcode: str):
  pack = await generate_pack(interaction, setcode)
  pack_names = pack[0]
  scryfall = pack[1]

  msg = f"[P1P1](<{scryfall}>) from {setcode}:\n```"
  for name in pack_names:
    msg += f"\n{name}"
  msg += "```"

  await interaction.response.send_message(msg, ephemeral=False)



@tree.command(  # type: ignore[arg-type]
    name="generate_draft",
    description="Generate 24 packs from the specified set",
    guilds=ALL
)
@app_commands.check(log_command)
async def generate_draft(interaction: discord.Interaction, setcode: str):
  with open("draft_boosters.txt", 'w') as f:
    for i in range(100):
      f.write('\n')
    for i in range(24):
      pack = await generate_pack(interaction, setcode)
      for name in pack[0]:
        f.write(f"{name}\n")
      f.write('\n')

  await interaction.response.send_message("Generated draft!", file=discord.File("draft_boosters.txt"), ephemeral=False)


PACK_TASK_LOOPS = dict()  # type: ignore[var-annotated]
def create_pack_taskloop(setcode: str, channel: int, minutes: int):
  async def p_task():
    pack = await generate_pack(None, setcode)
    if pack:
      pack_names = pack[0]
      scryfall = pack[1]

      msg = f"[P1P1](<{scryfall}>) from {setcode}:\n```"
      for name in pack_names:
        msg += f"\n{name}"
      msg += "```"

      c: discord.TextChannel = client.get_channel(channel)  # type: ignore[annotation-unchecked]
      await c.send(msg)
      print(f"Posted {setcode} P1P1 in #{c.name}")

  p_taskloop = tasks.loop(minutes=minutes)(p_task)

  if channel not in PACK_TASK_LOOPS:
    PACK_TASK_LOOPS[channel] = dict()
  if setcode not in PACK_TASK_LOOPS[channel]:
    PACK_TASK_LOOPS[channel][setcode] = list()
  PACK_TASK_LOOPS[channel][setcode] = p_taskloop

  p_taskloop.start()



