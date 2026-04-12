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
async def init_limited(interaction: discord.Interaction, setcode: str, bonus_setcode: str=""):
  code = setcode.upper()
  guild = interaction.guild
  if not guild:
    await send_error(interaction, "Could not find server")
    return

  await interaction.response.send_message("Working...", ephemeral=True)
  
  channel_cards = [
    # ["Rares and Mythics", "r>u"],
    # ["White Commons", "r%3Dc+c%3Dw"],
    # ["White Uncommons", "r%3Du+c%3Dw"],
    # ["Blue Commons", "r%3Dc+c%3Du"],
    # ["Blue Uncommons", "r%3Du+c%3Du"],
    # ["Black Commons", "r%3Dc+c%3Db"],
    # ["Black Uncommons", "r%3Du+c%3Db"],
    # ["Red Commons", "r%3Dc+c%3Dr"],
    # ["Red Uncommons", "r%3Du+c%3Dr"],
    # ["Green Commons", "r%3Dc+c%3Dg"],
    # ["Green Uncommons", "r%3Du+c%3Dg"],
    ["Silverquill U/Cs", "r<r+c%3Dwb"],
    ["Witherbloom U/Cs", "r<r+c%3Dbg"],
    ["Quandrix U/Cs", "r<r+c%3Dgu"],
    ["Prismari U/Cs", "r<r+c%3Dur"],
    ["Lorehold U/Cs", "r<r+c%3Drw"],
    ["Colorless U/Cs", "r<r+c%3D0+-t%3Aland"],
  ]

  async def category_init(query: str, name: str):
    cards = requests.get(f'https://api.scryfall.com/cards/search?q={query}').json()["data"]
    category = await guild.create_category(name)
    j = 0
    n = 1
    for c in cards:
      if j >= 50:
        j = 0
        n += 1
        category = await guild.create_category(f"{name} {n}")
      ni = get_name_and_image(c)
      channel = await category.create_text_channel(ni[0])
      j += 1
      if ni[1]:
        await channel.send(content=ni[1])

  for i in range(len(channel_cards)):
    await category_init(f'e%3A{code}+{channel_cards[i][1]}', f'{code} {channel_cards[i][0]}')
  if bonus_setcode:
    await category_init(f'e%3A{code}', f'{code} Bonus Sheet')



@tree.command(  # type: ignore[arg-type]
    name="delete_category",
    description="[ADMIN ONLY] Delete a category.",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
def delete_category(interaction: discord.Interaction, category: int):
  category = discord.utils.get(interaction.guild, id=category)
  for c in category.channels:
    await c.delete()
  await category.delete()

  await interaction.response.send_message("Deleted", ephemeral=True)



def get_name_and_image(card_data):
  if card_data['layout'] in ['transform', 'modal_dfc']:
    return [card_data["card_faces"][0]["name"], card_data["card_faces"][0]["image_uris"]["png"] + "\n" + card_data["card_faces"][1]["image_uris"]["png"]]
  else:
    return [card_data["name"], card_data["image_uris"]["png"]]






