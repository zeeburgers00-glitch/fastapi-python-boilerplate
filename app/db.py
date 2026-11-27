import json, sqlite3
from pathlib import Path
from datetime import datetime,timezone
from .config import get_settings
def now(): return datetime.now(timezone.utc).isoformat()
def connect():
 p=Path(get_settings().database_path); p.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(p); c.row_factory=sqlite3.Row; return c
def init_db():
 with connect() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,title TEXT,topic TEXT,mode TEXT,competitor_url TEXT,status TEXT,created_at TEXT,updated_at TEXT,result_json TEXT);
  CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,project_id TEXT,status TEXT,stage TEXT,error TEXT,created_at TEXT,updated_at TEXT);""")
def create_project(d):
 with connect() as c: c.execute("INSERT INTO projects VALUES(?,?,?,?,?,?,?,?,NULL)",(d["id"],d["title"],d["topic"],d["mode"],d.get("competitor_url"),"queued",now(),now()))
def create_job(j,p):
 with connect() as c: c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?)",(j,p,"queued","queued",None,now(),now()))
def update_job(j,status,stage,error=None):
 with connect() as c: c.execute("UPDATE jobs SET status=?,stage=?,error=?,updated_at=? WHERE id=?",(status,stage,error,now(),j))
def save_result(p,result):
 with connect() as c: c.execute("UPDATE projects SET result_json=?,status='completed',updated_at=? WHERE id=?",(json.dumps(result),now(),p))
def get_project(p):
 with connect() as c: r=c.execute("SELECT * FROM projects WHERE id=?",(p,)).fetchone()
 if not r:return None
 d=dict(r)
 if d.get("result_json"): d["result"]=json.loads(d.pop("result_json"))
 else:d.pop("result_json",None)
 return d
def list_projects():
 with connect() as c: rows=c.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
 out=[]
 for r in rows:
  d=dict(r)
  if d.get("result_json"):d["result"]=json.loads(d.pop("result_json"))
  else:d.pop("result_json",None)
  out.append(d)
 return out
def get_job(j):
 with connect() as c:r=c.execute("SELECT * FROM jobs WHERE id=?",(j,)).fetchone()
 return dict(r) if r else None
