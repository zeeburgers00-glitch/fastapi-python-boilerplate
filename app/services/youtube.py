import re,httpx
from ..config import get_settings
VIDEO_RE=re.compile(r"(?:youtu\\.be/|youtube\\.com/(?:watch\\?v=|shorts/|embed/))([A-Za-z0-9_-]{11})")
CHANNEL_RE=re.compile(r"(UC[A-Za-z0-9_-]{20,})")
HANDLE_RE=re.compile(r"youtube\\.com/@([^/?]+)")
def video_id(url):
 m=VIDEO_RE.search(url);return m.group(1) if m else None
async def analyze(url):
 key=get_settings().youtube_data_api_key
 if not key:return {"available":False,"reason":"Configure YOUTUBE_DATA_API_KEY for official public metadata analysis."}
 vid=video_id(url);channel=CHANNEL_RE.search(url);handle=HANDLE_RE.search(url)
 if not vid and not channel and not handle:return {"available":False,"reason":"Use a YouTube video URL, /channel/UC... URL, or @handle channel URL."}
 params={"key":key,"part":"snippet,statistics,contentDetails"}
 async with httpx.AsyncClient(timeout=40) as c:
  if vid:
   r=await c.get("https://www.googleapis.com/youtube/v3/videos",params={**params,"id":vid});r.raise_for_status()
   items=r.json().get("items",[])
   if not items:return {"available":True,"found":False,"kind":"video"}
   x=items[0];s=x["snippet"]
   return {"available":True,"found":True,"kind":"video","video":{"id":vid,"title":s["title"],"description":s.get("description","")[:2000],"channel":s.get("channelTitle"),"published_at":s.get("publishedAt"),"tags":s.get("tags",[])[:30],"statistics":x.get("statistics",{})}}
  lookup={"id":channel.group(1)} if channel else {"forHandle":handle.group(1)}
  r=await c.get("https://www.googleapis.com/youtube/v3/channels",params={**params,**lookup});r.raise_for_status()
  items=r.json().get("items",[])
  if not items:return {"available":True,"found":False,"kind":"channel"}
  x=items[0];sn=x["snippet"];stats=x.get("statistics",{})
  uploads=x.get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads")
  videos=[]
  if uploads:
   p=await c.get("https://www.googleapis.com/youtube/v3/playlistItems",params={"key":key,"part":"snippet,contentDetails","playlistId":uploads,"maxResults":25});p.raise_for_status()
   ids=[it.get("contentDetails",{}).get("videoId") for it in p.json().get("items",[]) if it.get("contentDetails",{}).get("videoId")]
   if ids:
    v=await c.get("https://www.googleapis.com/youtube/v3/videos",params={"key":key,"part":"snippet,statistics,contentDetails","id":",".join(ids)});v.raise_for_status()
    videos=[{"id":it["id"],"title":it["snippet"]["title"],"published_at":it["snippet"].get("publishedAt"),"duration":it.get("contentDetails",{}).get("duration"),"statistics":it.get("statistics",{})} for it in v.json().get("items",[])]
  videos.sort(key=lambda z:int(z.get("statistics",{}).get("viewCount",0)),reverse=True)
  return {"available":True,"found":True,"kind":"channel","channel":{"id":x["id"],"title":sn["title"],"description":sn.get("description","")[:2000],"statistics":stats},"recent_video_sample":videos,"top_sample_by_views":videos[:10],"analysis_note":"Sample is based on up to 25 recent uploads, ranked by public view count; it is not a guarantee of future performance."}
