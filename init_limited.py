import json
import requests
from random import randint
from typing import Optional

import discord
from discord import app_commands
from discord.ext import tasks

from util import client, tree, send_error, log_command, ALL


@tree.command(  # type: ignore[arg-type]
    name="init_limited",
    description="[ADMIN ONLY] Initialize limited channels for a set. WARNING: will make 300+ channels.",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def init_limited(interaction: discord.Interaction, setcode: str):
  code = setcode.upper()
  guild = interaction.guild
  if not guild:
    await send_error(interaction, "Could not find server")
    return
  
  channel_cards = [
    ["Rares and Mythics", "r>u"],
    ["White Commons", "r%3Dc+c%3Dw"],
    ["White Uncommons", "r%3Du+c%3Dw"],
    ["Blue Commons", "r%3Dc+c%3Du"],
    ["Blue Uncommons", "r%3Du+c%3Du"],
    ["Black Commons", "r%3Dc+c%3Db"],
    ["Black Uncommons", "r%3Du+c%3Db"],
    ["Red Commons", "r%3Dc+c%3Dr"],
    ["Red Uncommons", "r%3Du+c%3Dr"],
    ["Green Commons", "r%3Dc+c%3Dg"],
    ["Green Uncommons", "r%3Du+c%3Dg"],
    ["Other Commons", "r%3Dc+-%28c%3Dw+or+c%3Du+or+c%3Db+or+c%3Dr+or+c%3Dg%29+-is%3Abasic"],
    ["Other Uncommons", "r%3Du+-%28c%3Dw+or+c%3Du+or+c%3Db+or+c%3Dr+or+c%3Dg%29+-is%3Abasic"]
  ]

  for i in range(len(channel_cards)):
    cards = requests.get(f'https://api.scryfall.com/cards/search?q=e%3A{code}+{channel_cards[i][1]}').json()["data"]
    category = await guild.create_category(f"{code} {channel_cards[i][0]}")
    for c in cards:
      ni = get_name_and_image(c)
      channel = await category.create_text_channel(ni[0])
      if ni[1]:
        await channel.send(content=ni[1])


def get_name_and_image(card_data):
  if "card_faces" in card_data:
    return [card_data["card_faces"][0]["name"], card_data["card_faces"][0]["image_uris"]["png"] + "\n" + card_data["card_faces"][1]["image_uris"]["png"]]
  else:
    return [card_data["name"], card_data["image_uris"]["png"]]






