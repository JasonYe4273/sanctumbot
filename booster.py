import json
import requests
from random import randint

import discord
from discord import app_commands

from util import client, tree, send_error, log_command, ALL
from database import _get_all_db, _get_one_db, _set_db

SEALED_DATA = dict()
def fetch_sealed_data():
  try:
    # TEMP DFT DATA
    with open("dft.json") as f:
      SEALED_DATA["DFT"] = json.load(f)

    resp = requests.get("https://raw.githubusercontent.com/taw/magic-sealed-data/refs/heads/master/sealed_basic_data.json")
    for s in resp.json():
      if s["code"][-5:] == "draft" or s["code"][-4:] == "play":
        SEALED_DATA[s["set_code"].upper()] = s

    print("Fetched sealed_basic_data!")
    return True
  except:
    return False
fetch_sealed_data()

SET_CACHE = dict()  # type: ignore[var-annotated]


@tree.command(  # type: ignore[arg-type]
    name="p1p1",
    description="Pack 1 Pick 1 from the specified set",
    guilds=ALL
)
@app_commands.check(log_command)
async def p1p1(interaction: discord.Interaction, set_code: str):
  if not SEALED_DATA:
    if not fetch_sealed_data():
      await send_error(interaction, f"Error loading pack data")
      return

  set_code = set_code.upper()
  if set_code not in SEALED_DATA:
    await send_error(interaction, f"Cannot find a draft set with code {set_code}")
    return

  boosters = SEALED_DATA[set_code]["boosters"]
  booster = boosters[0]
  sheets = SEALED_DATA[set_code]["sheets"]

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

  set_cards = dict()
  if set_code in SET_CACHE:
    set_cards = SET_CACHE[set_code]
  else:
    try:
      resp = requests.get(f"https://mtgjson.com/api/v5/{set_code}.json")
      print(f"Fetched {set_code} JSON!")
      for c in resp.json()["data"]["cards"]:
        set_cards[c["number"]] = c["name"]
    except:
      await send_error(interaction, f"Error loading card data")
      return
    SET_CACHE[set_code] = set_cards

  scryfall = f"https://scryfall.com/search?q=e%3D{set_code}+game%3Dpaper+%28"
  pack_names: list[str] = []
  for i in range(len(pack)):
    cn = pack[i].split(":")[1]
    if not cn.isdigit() and cn[:-1].isdigit():
      cn = cn[:-1]
    if cn not in set_cards:
      await send_error(interaction, f"Error: cannot find card with CN {cn}")
      return
    pack_names.append(set_cards[cn])

    if i == 0:
      scryfall += f"cn%3D{cn}"
    else:
      scryfall += f"+or+cn%3D{cn}"
  scryfall += "%29"

  msg = f"[P1P1](<{scryfall}>) from {set_code}:\n```"
  for name in pack_names:
    msg += f"\n{name}"
  msg += "```"

  await interaction.response.send_message(msg, ephemeral=False)



