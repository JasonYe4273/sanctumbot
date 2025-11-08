import requests
import re

import discord
from discord import app_commands

from util import client, tree, send_error, log_command, SANCTUM, ALL
from database import con, cur, _get_all_db, _get_one_db, _set_db



async def mythicscraper(client, setcode: str):
  print(f"SCRAPING SET {setcode}")

  data = _get_all_db(f"SELECT channel,altchannel,role,altrole FROM scraperinfo WHERE setcode='{setcode}'")
  if not data:
    return

  resp = requests.get(f'https://www.mythicspoiler.com/{setcode}/index.html')
  lines = resp.text.split('\n')

  alt = False
  for l in lines:
    # all main set cards are above the first isolated section
    if 'ISOLATED SECTION' in l:
      alt = True

    if 'class="card"' in l:
      try:
        name_path = re.search('(?<=href=\")(.*?)(?=\">)', l).group()  # type: ignore[union-attr]
        name = re.search('(?<=cards/)(.*?)(?=\\.)', name_path).group()  # type: ignore[union-attr]

        # no repeats
        if _get_one_db(f"SELECT * FROM scrapercards WHERE setcode='{setcode}' AND cardname='{name}'"):
          continue

        print(f"FOUND NEW CARD: {name}")
        img = re.search('(?<=src=\")(.*?)(?=\">)', l).group()  # type: ignore[union-attr]

        for d in data:
          message = f"""<@&{role}> [New spoiler!](<https://www.mythicspoiler.com/{setcode}/{name_path}>)
  [Image](https://www.mythicspoiler.com/{d[3] if alt else d[2]}/{img})"""
          c: discord.TextChannel = client.get_channel(d[1] if alt else d[0])
          await c.send(message)

        _set_db(f"INSERT INTO scrapercards (setcode, cardname) VALUES ('{setcode}', '{name}')")
      except:
        pass

  print(f"SCRAPING LATEST SPOILERS")

  resp = requests.get(f'https://www.mythicspoiler.com/newspoilers.html')
  sections = resp.text.split('<!--BOLD')

  try:
    for s in sections[1:]:
      title = re.search('(?<=-->)(.*?)(?=<font class)', s, flags=re.DOTALL).group().strip()  # type: ignore[union-attr]

      if "-" in title:
        alt = True
      else:
        alt = False

      lines = s.split('<!--CARD CARD CARD CARD CARD CARD CARD-->')

      for l in lines:
        if 'class="grid-card"' in l:
          name_path = re.search('(?<=<div class=\"grid-card\"><a href=\")(.*?)(?=\">)', l, flags=re.DOTALL).group().strip()  # type: ignore[union-attr]
          name = re.search('(?<=cards/)(.*?)(?=\\.)', name_path).group()  # type: ignore[union-attr]

          # check set matches, if not stop searching this section
          if not name_path.startswith(setcode):
            break

          # no repeats
          if _get_one_db(f"SELECT * FROM scrapercards WHERE setcode='{setcode}' AND cardname='{name}'"):
            continue

          print(f"FOUND NEW CARD: {name}")
          img = re.search('(?<=src=\")(.*?)(?=\">)', l, flags=re.DOTALL).group().strip()  # type: ignore[union-attr]

          for d in data:
            message = f"""<@&{d[3] if alt else d[2]}> [New spoiler!](<https://www.mythicspoiler.com/{name_path}>)
    [Image](https://www.mythicspoiler.com/{img})"""
            c: discord.TextChannel = client.get_channel(d[1] if alt else d[0])  # type: ignore[no-redef]
            await c.send(message)

          _set_db(f"INSERT INTO scrapercards (setcode, cardname) VALUES ('{setcode}', '{name}')")
  except:
    pass

  print(f"DONE SCRAPING SET {setcode}")


@tree.command(  # type: ignore[arg-type]
    name="create_scraper",
    description="[ADMIN ONLY] Create a mythicspoiler scraper in this channel",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def create_scraper(interaction: discord.Interaction, setcode: str):
    # TODO: actual role handling, not just hardcoded
    _set_db(f"INSERT INTO scraperinfo (setcode,channel,altchannel,role,altrole) VALUES ('{setcode}',{interaction.channel_id},0,1282790401790578689,1282790483143299073)")
    await interaction.response.send_message(f"{setcode} scraper created!", ephemeral=True)


@tree.command(  # type: ignore[arg-type]
    name="set_scraper_channel",
    description="[ADMIN ONLY] Set a scraper's channel",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def set_scraper_channel(interaction: discord.Interaction, setcode: str):
    _set_db(f"UPDATE scraperinfo SET channel={interaction.channel_id} WHERE setcode='{setcode}'")
    await interaction.response.send_message(f"{setcode} scraper channel set!", ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="set_scraper_alt",
    description="[ADMIN ONLY] Set a scraper's alt channel",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def set_scraper_alt(interaction: discord.Interaction, setcode: str):
    _set_db(f"UPDATE scraperinfo SET altchannel={interaction.channel_id} WHERE setcode='{setcode}'")
    await interaction.response.send_message(f"{setcode} scraper alt channel set!", ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="update_scraper_role",
    description="[ADMIN ONLY] Update this channel's ping role",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def update_scraper_role(interaction: discord.Interaction, role: str):
    _set_db(f"UPDATE scraperinfo SET role={role} WHERE channel='{interaction.channel_id}'")
    _set_db(f"UPDATE scraperinfo SET altrole={role} WHERE altchannel='{interaction.channel_id}'")
    await interaction.response.send_message(f"Scraper ping role set for this channel!", ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="delete_scraper",
    description="[ADMIN ONLY] Delete a mythicspoiler scraper",
    guilds=ALL
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def delete_scraper(interaction: discord.Interaction, setcode: str):
    _set_db(f"DELETE FROM scraperinfo WHERE setcode='{setcode}'")
    await interaction.response.send_message(f"{setcode} scraper deleted!", ephemeral=True)




