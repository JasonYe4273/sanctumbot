import sqlite3

con = sqlite3.connect("sanctum.db")
cur = con.cursor()

# initialization
cur.execute("""CREATE TABLE IF NOT EXISTS tournaments(
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  active INTEGER NOT NULL,
  type TEXT NOT NULL
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS players(
  tid INTEGER NOT NULL,
  user TEXT NOT NULL,
  decklist TEXT,
  wins INTEGER NOT NULL,
  losses INTEGER NOT NULL,
  draws INTEGER NOT NULL,
  dropped INTEGER NOT NULL
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS matches(
  tid INTEGER NOT NULL,
  pid1 INTEGER NOT NULL,
  pid2 INTEGER NOT NULL,
  otp INTEGER NOT NULL,
  reported INTEGER NOT NULL,
  wins1 INTEGER NOT NULL,
  wins2 INTEGER NOT NULL,
  draws INTEGER NOT NULL,
  round INTEGER
)""")
con.commit()