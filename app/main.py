import uuid
import re
from pathlib import Path
from fastapi import FastAPI,HTTPException,BackgroundTasks,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .config import get_settings
from .db import init_db,create_project,create_job,get_project,list_projects,get_job,update_job,save_result
from .schemas import (ProjectCreate,RenderRequest,VoiceRequest,MediaSearchRequest,
                      ThumbnailRequest,StockDownloadRequest,VideoEditRequest,AvatarRequest)
from .agents.pipeline import run_production
from .services.render import render_slideshow
from .services.voice import synthesize_piper,synthesize_edge,list_edge_voices
from .services.media import search_pexels,download_pexels_video
from .services.thumbnail import create_thumbnail
from .services.editor import render_video
from .services.avatar import render_talking_avatar
from .services.ollama import provider_status

s=get_settings()
app=FastAPI(title=s.app_name,version="0.3.0",description="Local-first AI YouTube production backend.")
app.add_middleware(CORSMiddleware,allow_origins=s.allowed_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()
    Path("uploads").mkdir(exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)

@app.get("/")
def root():
    return {"message":"YouTube AI Factory API","docs":"/docs","health":"/health"}

@app.get("/health")
def health():
    return {"status":"ok","app":s.app_name,"environment":s.app_env}

@app.get("/api/v1/capabilities")
def capabilities():
    return {"modes":["topic","competitor"],"formats":["short","long","both"],
            "publishing":["download_only"],
            "agents":["research","script","storyboard","seo","quality-review"],
            "modules":["multi-provider-llm","pexels-stock-search-and-download","ffmpeg-multiclip-editor",
                       "srt-caption-burn-in","edge-neural-tts","piper-local-tts","sadtalker-avatar-adapter",
                       "pillow-thumbnail","official-youtube-metadata"],
            "providers":{"llm":provider_status(),"youtube_data_api":bool(s.youtube_data_api_key),
                         "pexels":bool(s.pexels_api_key),"piper_model":bool(s.piper_model_path),
                         "edge_tts":"optional online service","sadtalker":bool(s.sadtalker_path)},
            "notes":["No provider is guaranteed unlimited or permanently free.",
                     "SadTalker requires a separate local checkout and model weights.",
                     "Stock assets must be checked against the provider license before publication.",
                     "Competitor analysis reads public metadata only; it does not copy videos.",
                     "This API does not upload or schedule videos to YouTube."]}

async def process_project(pid,jid,opts):
    try:
        update_job(jid,"running","research_and_script")
        project=get_project(pid)
        result=await run_production(project,opts)
        save_result(pid,result)
        update_job(jid,"completed",result.get("status","completed"))
    except Exception as exc:
        update_job(jid,"failed","error",str(exc)[:1000])

@app.post("/api/v1/projects",status_code=202)
async def new_project(body:ProjectCreate,bg:BackgroundTasks):
    if body.mode=="competitor" and not body.competitor_url:
        raise HTTPException(400,"competitor_url is required for competitor mode.")
    pid,jid=str(uuid.uuid4()),str(uuid.uuid4())
    data={"id":pid,"title":body.title or body.topic[:80],"topic":body.topic,
          "mode":body.mode,"competitor_url":str(body.competitor_url) if body.competitor_url else None}
    create_project(data)
    create_job(jid,pid)
    bg.add_task(process_project,pid,jid,body.model_dump(mode="json"))
    return {"project_id":pid,"job_id":jid,"status":"queued","poll_url":f"/api/v1/jobs/{jid}"}

@app.get("/api/v1/projects")
def projects():
    return {"items":list_projects()}

@app.get("/api/v1/projects/{pid}")
def project_detail(pid):
    p=get_project(pid)
    if not p: raise HTTPException(404,"Project not found")
    return p

@app.get("/api/v1/jobs/{jid}")
def job_detail(jid):
    j=get_job(jid)
    if not j: raise HTTPException(404,"Job not found")
    return j

@app.post("/api/v1/assets/upload")
async def upload_asset(file:UploadFile=File(...)):
    allowed={".png",".jpg",".jpeg",".webp",".wav",".mp3",".m4a",".mp4",".mov",".srt",".vtt"}
    ext=Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(400,"Supported: images, audio, video, SRT and VTT.")
    name=uuid.uuid4().hex+ext
    target=Path("uploads")/name
    target.parent.mkdir(exist_ok=True)
    total=0
    limit=s.max_upload_mb*1024*1024
    try:
        with target.open("wb") as out:
            while True:
                chunk=await file.read(1024*1024)
                if not chunk: break
                total+=len(chunk)
                if total>limit: raise HTTPException(413,"Upload exceeds MAX_UPLOAD_MB.")
                out.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return {"asset_path":str(target),"filename":name,"bytes":total,"content_type":file.content_type}

@app.post("/api/v1/voice/synthesize")
def voice(body:VoiceRequest):
    try:
        if body.engine=="piper":
            if not body.filename.lower().endswith(".wav"):
                raise HTTPException(400,"Piper output filename must end in .wav.")
            return synthesize_piper(body.text,body.filename)
        if not body.filename.lower().endswith(".mp3"):
            raise HTTPException(400,"Edge TTS output filename must end in .mp3.")
        return synthesize_edge(body.text,body.filename,body.voice)
    except RuntimeError as exc:
        raise HTTPException(503,str(exc))

@app.get("/api/v1/voice/voices")
def voice_catalog():
    try:
        voices=list_edge_voices()
        return {"count":len(voices),"voices":[{"name":v.get("Name"),"short_name":v.get("ShortName"),
                "locale":v.get("Locale"),"gender":v.get("Gender")} for v in voices]}
    except RuntimeError as exc:
        raise HTTPException(503,str(exc))

@app.post("/api/v1/media/search")
async def media(body:MediaSearchRequest):
    try:
        return {"items":await search_pexels(body.query,body.per_page)}
    except RuntimeError as exc:
        raise HTTPException(503,str(exc))
    except Exception as exc:
        raise HTTPException(502,str(exc)[:500])

@app.post("/api/v1/media/download")
async def media_download(body:StockDownloadRequest):
    try:
        return await download_pexels_video(body.video_id,body.quality)
    except RuntimeError as exc:
        raise HTTPException(503,str(exc))
    except Exception as exc:
        raise HTTPException(502,str(exc)[:500])

@app.post("/api/v1/thumbnails/generate")
def thumbnail(body:ThumbnailRequest):
    try:
        return create_thumbnail(body.title,body.background_path,body.filename)
    except (ValueError,OSError) as exc:
        raise HTTPException(400,str(exc))

@app.post("/api/v1/render/slideshow")
def render(body:RenderRequest):
    try:
        return render_slideshow(body.image_paths,body.output_name,body.width,body.height,body.fps,body.audio_path)
    except (ValueError,RuntimeError) as exc:
        raise HTTPException(400,str(exc))

@app.post("/api/v1/render/video")
def edit_video(body:VideoEditRequest):
    try:
        return render_video(body.clip_paths,body.narration_path,body.music_path,body.subtitle_path,
                            body.output_name,body.width,body.height,body.fps,body.music_volume)
    except (ValueError,RuntimeError) as exc:
        raise HTTPException(400,str(exc))

@app.post("/api/v1/avatar/talking")
def talking_avatar(body:AvatarRequest):
    try:
        return render_talking_avatar(body.image_path,body.audio_path,body.filename)
    except (ValueError,RuntimeError) as exc:
        raise HTTPException(503,str(exc))

@app.get("/api/v1/outputs/{filename}")
def get_output(filename:str):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+",filename):
        raise HTTPException(400,"Invalid filename.")
    path=(Path("outputs")/filename).resolve()
    if Path("outputs").resolve() not in path.parents or not path.is_file():
        raise HTTPException(404,"Output not found.")
    return FileResponse(path,filename=filename)
