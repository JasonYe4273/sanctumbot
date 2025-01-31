import requests
import re

import discord
from discord import app_commands

from util import client, tree, send_error, log_command, SANCTUM
from database import con, cur, _get_all_db, _get_one_db, _set_db



async def mythicscraper(client, setcode: str):
  print(f"SCRAPING SET {setcode}")

  cur.execute(f"SELECT channel,altchannel,role,altrole FROM scraperinfo WHERE setcode='{setcode}'")
  data = cur.fetchone()
  if not data:
    return

  resp = requests.get(f'https://www.mythicspoiler.com/{setcode}/index.html')
  lines = resp.text.split('\n')

  alt = False
  channel = data[0]
  role = data[2]
  for l in lines:
    # all main set cards are above the first isolated section
    if 'ISOLATED SECTION' in l:
      alt = True
      channel = data[1]
      role = data[3]

    if 'class="card"' in l:
      try:
        name_path = re.search('(?<=href=\")(.*?)(?=\">)', l).group()  # type: ignore[union-attr]
        name = re.search('(?<=cards/)(.*?)(?=\\.)', name_path).group()  # type: ignore[union-attr]

        # no repeats
        cur.execute(f"SELECT * FROM scrapercards WHERE setcode='{setcode}' AND cardname='{name}'")
        if cur.fetchone():
          continue

        print(f"FOUND NEW CARD: {name}")
        img = re.search('(?<=src=\")(.*?)(?=\">)', l).group()  # type: ignore[union-attr]

        message = f"""<@&{role}> [New spoiler!](<https://www.mythicspoiler.com/{setcode}/{name_path}>)
[Image](https://www.mythicspoiler.com/{setcode}/{img})"""
        c: discord.TextChannel = client.get_channel(channel)
        await c.send(message)

        cur.execute(f"INSERT INTO scrapercards (setcode, cardname) VALUES ('{setcode}', '{name}')")
        con.commit()
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
        channel = data[1]
        role = data[3]
      else:
        alt = False
        channel = data[0]
        role = data[2]

      lines = s.split('<!--CARD CARD CARD CARD CARD CARD CARD-->')

      for l in lines:
        if 'class="grid-card"' in l:
          name_path = re.search('(?<=<div class=\"grid-card\"><a href=\")(.*?)(?=\">)', l, flags=re.DOTALL).group().strip()  # type: ignore[union-attr]
          name = re.search('(?<=cards/)(.*?)(?=\\.)', name_path).group()  # type: ignore[union-attr]

          # check set matches, if not stop searching this section
          if not name_path.startswith(setcode):
            break

          # no repeats
          cur.execute(f"SELECT * FROM scrapercards WHERE setcode='{setcode}' AND cardname='{name}'")
          if cur.fetchone():
            continue

          print(f"FOUND NEW CARD: {name}")
          img = re.search('(?<=src=\")(.*?)(?=\">)', l, flags=re.DOTALL).group().strip()  # type: ignore[union-attr]

          message = f"""<@&{role}> [New spoiler!](<https://www.mythicspoiler.com/{name_path}>)
  [Image](https://www.mythicspoiler.com/{img})"""
          c: discord.TextChannel = client.get_channel(channel)  # type: ignore[no-redef]
          await c.send(message)

          cur.execute(f"INSERT INTO scrapercards (setcode, cardname) VALUES ('{setcode}', '{name}')")
          con.commit()
  except:
    pass

  print(f"DONE SCRAPING SET {setcode}")


@tree.command(  # type: ignore[arg-type]
    name="create_scraper",
    description="[ADMIN ONLY] Create a mythicspoiler scraper",
    guild=SANCTUM
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def create_scraper(interaction: discord.Interaction, setcode: str):
    # TODO: actual role handling, not just hardcoded
    _set_db(f"INSERT INTO scraperinfo (setcode,channel,altchannel,role,altrole) VALUES ('{setcode}',{interaction.channel_id},0,1282790401790578689,1282790483143299073)")
    await interaction.response.send_message(f"{setcode} scraper created!", ephemeral=True)


@tree.command(  # type: ignore[arg-type]
    name="set_scraper_channel",
    description="[ADMIN ONLY] Create a mythicspoiler scraper",
    guild=SANCTUM
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def set_scraper_channel(interaction: discord.Interaction, setcode: str):
    _set_db(f"UPDATE scraperinfo SET channel={interaction.channel_id} WHERE setcode='{setcode}'")
    await interaction.response.send_message(f"{setcode} scraper channel set!", ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="set_scraper_alt",
    description="[ADMIN ONLY] Set a scraper's alt channel",
    guild=SANCTUM
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def set_scraper_alt(interaction: discord.Interaction, setcode: str):
    _set_db(f"UPDATE scraperinfo SET altchannel={interaction.channel_id} WHERE setcode='{setcode}'")
    await interaction.response.send_message(f"{setcode} scraper alt channel set!", ephemeral=True)



@tree.command(  # type: ignore[arg-type]
    name="delete_scraper",
    description="[ADMIN ONLY] Delete a mythicspoiler scraper",
    guild=SANCTUM
)
@app_commands.check(log_command)
@app_commands.checks.has_permissions(administrator=True)
async def delete_scraper(interaction: discord.Interaction, setcode: str):
    _set_db(f"DELETE FROM scraperinfo WHERE setcode='{setcode}'")
    await interaction.response.send_message(f"{setcode} scraper deleted!", ephemeral=True)




