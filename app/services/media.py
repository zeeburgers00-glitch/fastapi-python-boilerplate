import re
from pathlib import Path
import httpx
from ..config import get_settings

async def search_pexels(query:str,per_page:int=12):
 key=get_settings().pexels_api_key
 if not key:raise RuntimeError("Set PEXELS_API_KEY to enable stock-media search.")
 async with httpx.AsyncClient(timeout=30) as c:
  r=await c.get("https://api.pexels.com/videos/search",headers={"Authorization":key},params={"query":query,"per_page":max(1,min(per_page,30))})
  r.raise_for_status(); data=r.json()
 return [{"id":v["id"],"url":v["url"],"duration":v.get("duration"),"photographer":v.get("user",{}).get("name"),"files":[{"quality":f.get("quality"),"width":f.get("width"),"height":f.get("height"),"link":f.get("link")} for f in v.get("video_files",[])[:10]]} for v in data.get("videos",[])]

async def download_pexels_video(video_id:int,quality:str="hd"):
 s=get_settings()
 if not s.pexels_api_key:raise RuntimeError("Set PEXELS_API_KEY to enable stock-video downloads.")
 async with httpx.AsyncClient(timeout=60,follow_redirects=True) as client:
  response=await client.get(f"https://api.pexels.com/videos/videos/{video_id}",headers={"Authorization":s.pexels_api_key})
  response.raise_for_status(); video=response.json()
  files=video.get("video_files",[])
  if not files:raise RuntimeError("Pexels did not return downloadable video files.")
  rank={"uhd":3,"hd":2,"sd":1}
  candidates=[f for f in files if f.get("link") and f.get("file_type","").startswith("video/")]
  if not candidates: candidates=[f for f in files if f.get("link")]
  candidates.sort(key=lambda f:(f.get("quality")=="hd",f.get("width",0)*f.get("height",0)),reverse=True)
  chosen=next((f for f in candidates if f.get("quality")==quality),None) or candidates[0]
  url=chosen["link"]
  if not url.startswith("https://videos.pexels.com/"):
   raise RuntimeError("Unexpected stock asset host; refusing download.")
  outdir=Path("uploads").resolve();outdir.mkdir(parents=True,exist_ok=True)
  target=outdir/f"pexels_{video_id}_{chosen.get('id','asset')}.mp4"
  total=0;limit=s.max_stock_download_mb*1024*1024
  async with client.stream("GET",url) as stream:
   stream.raise_for_status()
   with target.open("wb") as handle:
    async for chunk in stream.aiter_bytes(1024*1024):
     total+=len(chunk)
     if total>limit:
      target.unlink(missing_ok=True)
      raise RuntimeError(f"Stock video exceeds MAX_STOCK_DOWNLOAD_MB ({s.max_stock_download_mb}).")
     handle.write(chunk)
  return {"asset_path":str(target),"filename":target.name,"bytes":total,"provider":"Pexels",
          "pexels_video_id":video_id,"source_url":video.get("url"),
          "photographer":video.get("user",{}).get("name"),"license":"Review Pexels license and asset terms before publication.",
          "width":chosen.get("width"),"height":chosen.get("height"),"quality":chosen.get("quality")}
