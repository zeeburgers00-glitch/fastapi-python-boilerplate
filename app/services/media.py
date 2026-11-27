import httpx
from ..config import get_settings
async def search_pexels(query:str,per_page:int=12):
 key=get_settings().pexels_api_key
 if not key:raise RuntimeError("Set PEXELS_API_KEY to enable stock-media search.")
 async with httpx.AsyncClient(timeout=30) as c:
  r=await c.get("https://api.pexels.com/videos/search",headers={"Authorization":key},params={"query":query,"per_page":max(1,min(per_page,30))})
  r.raise_for_status(); data=r.json()
 return [{"id":v["id"],"url":v["url"],"duration":v.get("duration"),"photographer":v.get("user",{}).get("name"),"files":[{"quality":f.get("quality"),"width":f.get("width"),"height":f.get("height"),"link":f.get("link")} for f in v.get("video_files",[])[:5]]} for v in data.get("videos",[])]
