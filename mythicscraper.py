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
        name = re.search('(?<=cards/)(.*?)(?=\.)', name_path).group()

        # no repeats
        cur.execute(f"SELECT * FROM scrapercards WHERE setcode='{setcode}' AND cardname='{name}'")
        if cur.fetchone():
          continue

        print(f"FOUND NEW CARD: {name}")
        img = re.search('(?<=src=\")(.*)(?=\">)', l).group()

        message = f"""<@&{role}> new spoiler! <https://www.mythicspoiler.com/{setcode}/{name_path}>
  https://www.mythicspoiler.com/{setcode}/{img}
  """
        c: discord.TextChannel = client.get_channel(channel)
        await c.send(message)

        cur.execute(f"INSERT INTO scrapercards (setcode, cardname) VALUES ('{setcode}', '{name}')")
        con.commit()
      except:
        pass




