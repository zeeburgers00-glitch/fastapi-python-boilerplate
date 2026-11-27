import re,httpx
from ..config import get_settings
VIDEO_RE=re.compile(r"(?:youtu\\.be/|youtube\\.com/(?:watch\\?v=|shorts/|embed/))([A-Za-z0-9_-]{11})")
CHANNEL_RE=re.compile(r"(UC[A-Za-z0-9_-]{20,})")
def video_id(url):
 m=VIDEO_RE.search(url); return m.group(1) if m else None
async def analyze(url):
 key=get_settings().youtube_data_api_key
 if not key:return {"available":False,"reason":"Configure YOUTUBE_DATA_API_KEY for official public metadata analysis."}
 vid=video_id(url); channel=CHANNEL_RE.search(url)
 if not vid and not channel:return {"available":False,"reason":"Provide a YouTube video URL or channel ID URL."}
 params={"key":key,"part":"snippet,statistics,contentDetails"}
 async with httpx.AsyncClient(timeout=30) as c:
  if vid:
   r=await c.get("https://www.googleapis.com/youtube/v3/videos",params={**params,"id":vid});r.raise_for_status()
   items=r.json().get("items",[])
   if not items:return {"available":True,"found":False,"kind":"video"}
   x=items[0];s=x["snippet"]
   return {"available":True,"found":True,"kind":"video","video":{"id":vid,"title":s["title"],"description":s.get("description","")[:2000],"channel":s.get("channelTitle"),"published_at":s.get("publishedAt"),"tags":s.get("tags",[])[:30],"statistics":x.get("statistics",{})}}
  cid=channel.group(1)
  r=await c.get("https://www.googleapis.com/youtube/v3/channels",params={**params,"id":cid});r.raise_for_status()
  items=r.json().get("items",[])
  if not items:return {"available":True,"found":False,"kind":"channel"}
  x=items[0]
  return {"available":True,"found":True,"kind":"channel","channel":{"id":cid,"title":x["snippet"]["title"],"description":x["snippet"].get("description","")[:2000],"statistics":x.get("statistics",{})}}
