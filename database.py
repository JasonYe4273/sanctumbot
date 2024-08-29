import psycopg2  # type: ignore[import]
try:
    from secrets import DATABASE_URL
except:
    import os
    DATABASE_URL = os.environ.get('DATABASE_URL', '')

con = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = con.cursor()

# cur.execute("DROP TABLE IF EXISTS tournaments CASCADE")
# cur.execute("DROP TABLE IF EXISTS players CASCADE")
# cur.execute("DROP TABLE IF EXISTS matches CASCADE")
# cur.execute("DROP TABLE IF EXISTS queue CASCADE")

# initialization
cur.execute("""CREATE TABLE IF NOT EXISTS tournaments(
  tid SERIAL,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  active BOOL NOT NULL,
  type TEXT NOT NULL,
  channel BIGINT NOT NULL,
  PRIMARY KEY(tid)
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS players(
  pid SERIAL,
  tid INT,
  username TEXT NOT NULL,
  uid BIGINT NOT NULL,
  decklist TEXT,
  wins INT NOT NULL,
  losses INT NOT NULL,
  draws INT NOT NULL,
  dropped BOOL NOT NULL,
  PRIMARY KEY(pid),
  CONSTRAINT fk_tournament
    FOREIGN KEY(tid)
    REFERENCES tournaments(tid)
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS matches(
  mid SERIAL,
  tid INT,
  pid1 INT NOT NULL,
  pid2 INT NOT NULL,
  reported BOOL NOT NULL,
  wins1 INT NOT NULL,
  wins2 INT NOT NULL,
  PRIMARY KEY(mid),
  CONSTRAINT fk_tournament
    FOREIGN KEY(tid)
    REFERENCES tournaments(tid),
  CONSTRAINT fk_p1
    FOREIGN KEY(pid1)
    REFERENCES players(pid),
  CONSTRAINT fk_p2
    FOREIGN KEY(pid2)
    REFERENCES players(pid)
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS queue(
  qid SERIAL,
  tid INT,
  pid INT,
  PRIMARY KEY(qid),
  CONSTRAINT fk_tournament
    FOREIGN KEY(tid)
    REFERENCES tournaments(tid),
  CONSTRAINT fk_player
    FOREIGN KEY(pid)
    REFERENCES players(pid)
)""")
con.commit()