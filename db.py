import sqlite3
from datetime import datetime, timezone
from config import DB_PATH

def connect():
    c=sqlite3.connect(DB_PATH,check_same_thread=False)
    c.row_factory=sqlite3.Row
    return c

def init_db():
    c=connect()
    c.execute("""CREATE TABLE IF NOT EXISTS influencers(
      username TEXT PRIMARY KEY, name TEXT, profile_url TEXT, niche TEXT,
      followers INTEGER, email TEXT, location TEXT, bio TEXT,
      ai_summary TEXT DEFAULT '', score INTEGER DEFAULT 0, category TEXT DEFAULT '',
      status TEXT DEFAULT 'New Lead', created_at TEXT, last_contacted TEXT,
      followup_stage INTEGER DEFAULT 0, thread_id TEXT DEFAULT '', last_reply TEXT DEFAULT '',
      email_subject TEXT DEFAULT '', email_body TEXT DEFAULT '', opted_out INTEGER DEFAULT 0)""")
    c.commit(); c.close()

def upsert(row):
    cols=["username","name","profile_url","niche","followers","email","location","bio"]
    vals=[str(row.get(k,"") or "") for k in cols]
    vals[4]=int(float(vals[4] or 0))
    c=connect()
    c.execute("""INSERT INTO influencers(username,name,profile_url,niche,followers,email,location,bio,created_at)
    VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username) DO UPDATE SET
    name=excluded.name,profile_url=excluded.profile_url,niche=excluded.niche,
    followers=excluded.followers,email=CASE WHEN excluded.email='' THEN influencers.email ELSE excluded.email END,
    location=excluded.location,bio=excluded.bio""",vals+[datetime.now(timezone.utc).isoformat()])
    c.commit(); c.close()

def all_rows():
    c=connect(); rows=[dict(x) for x in c.execute("SELECT * FROM influencers ORDER BY created_at DESC")]; c.close()
    return rows

def one(username):
    c=connect(); r=c.execute("SELECT * FROM influencers WHERE username=?",(username,)).fetchone(); c.close()
    return dict(r) if r else None

def update(username,**kw):
    allowed={"ai_summary","score","category","status","last_contacted","followup_stage","thread_id","last_reply","email_subject","email_body","opted_out"}
    d={k:v for k,v in kw.items() if k in allowed}
    if d:
        c=connect(); c.execute("UPDATE influencers SET "+",".join(k+"=?" for k in d)+" WHERE username=?",list(d.values())+[username]); c.commit(); c.close()
