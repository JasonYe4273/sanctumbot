import requests
import re
import discord
from database import con, cur



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
        name_path = re.search('(?<=href=\")(.*?)(?=\">)', l).group()
        name = re.search('(?<=cards/)(.*?)(?=\\.)', name_path).group()

        # no repeats
        cur.execute(f"SELECT * FROM scrapercards WHERE setcode='{setcode}' AND cardname='{name}'")
        if cur.fetchone():
          continue

        print(f"FOUND NEW CARD: {name}")
        img = re.search('(?<=src=\")(.*?)(?=\">)', l).group()

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
      title = re.search('(?<=-->)(.*?)(?=<font class)', s, flags=re.DOTALL).group().strip()

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
          name_path = re.search('(?<=<div class=\"grid-card\"><a href=\")(.*?)(?=\">)', l, flags=re.DOTALL).group().strip()
          name = re.search('(?<=cards/)(.*?)(?=\\.)', name_path).group()

          # check set matches, if not stop searching this section
          if not name_path.startswith(setcode):
            break

          # no repeats
          cur.execute(f"SELECT * FROM scrapercards WHERE setcode='{setcode}' AND cardname='{name}'")
          if cur.fetchone():
            continue

          print(f"FOUND NEW CARD: {name}")
          img = re.search('(?<=src=\")(.*?)(?=\">)', l, flags=re.DOTALL).group().strip()

          message = f"""<@&{role}> [New spoiler!](<https://www.mythicspoiler.com/{name_path}>)
  [Image](https://www.mythicspoiler.com/{img})"""
          c: discord.TextChannel = client.get_channel(channel)
          await c.send(message)

          cur.execute(f"INSERT INTO scrapercards (setcode, cardname) VALUES ('{setcode}', '{name}')")
          con.commit()
  except:
    pass

  print(f"DONE SCRAPING SET {setcode}")




