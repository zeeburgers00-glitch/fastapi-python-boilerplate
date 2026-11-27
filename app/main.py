import uuid,re
from pathlib import Path
from fastapi import FastAPI,HTTPException,BackgroundTasks,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .config import get_settings
from .db import init_db,create_project,create_job,get_project,list_projects,get_job,update_job,save_result
from .schemas import ProjectCreate,RenderRequest,VoiceRequest,MediaSearchRequest,ThumbnailRequest
from .agents.pipeline import run_production
from .services.render import render_slideshow
from .services.voice import synthesize_piper
from .services.media import search_pexels
from .services.thumbnail import create_thumbnail
from .services.ollama import provider_status
s=get_settings()
app=FastAPI(title=s.app_name,version="0.2.0",description="Local-first YouTube production backend.")
app.add_middleware(CORSMiddleware,allow_origins=s.allowed_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup():
 init_db();Path("uploads").mkdir(exist_ok=True);Path("outputs").mkdir(exist_ok=True)
@app.get("/")
def root():return {"message":"YouTube AI Factory API","docs":"/docs","health":"/health"}
@app.get("/health")
def health():return {"status":"ok","app":s.app_name,"environment":s.app_env}
@app.get("/api/v1/capabilities")
def capabilities():
 return {"modes":["topic","competitor"],"formats":["short","long","both"],"publishing":["download_only"],"agents":["research","script","storyboard","seo","quality-review"],"modules":["official-youtube-metadata","ollama-generation","piper-local-tts","pexels-stock-search","pillow-thumbnail","ffmpeg-render"],"providers":{"llm":provider_status(),"youtube_data_api":bool(s.youtube_data_api_key),"pexels":bool(s.pexels_api_key),"piper_model":bool(s.piper_model_path)},"notes":["AI drafts require fact-checking and human review.","Competitor analysis reads public metadata only; it does not copy videos.","Render and thumbnail inputs must be uploaded through this API first."]}
async def process_project(pid,jid,opts):
 try:
  update_job(jid,"running","research_and_script")
  project=get_project(pid);result=await run_production(project,opts)
  save_result(pid,result);update_job(jid,"completed","draft_ready")
 except Exception as exc:update_job(jid,"failed","error",str(exc)[:1000])
@app.post("/api/v1/projects",status_code=202)
async def new_project(body:ProjectCreate,bg:BackgroundTasks):
 if body.mode=="competitor" and not body.competitor_url:raise HTTPException(400,"competitor_url is required for competitor mode.")
 pid,jid=str(uuid.uuid4()),str(uuid.uuid4())
 data={"id":pid,"title":body.title or body.topic[:80],"topic":body.topic,"mode":body.mode,"competitor_url":str(body.competitor_url) if body.competitor_url else None}
 create_project(data);create_job(jid,pid);bg.add_task(process_project,pid,jid,body.model_dump(mode="json"))
 return {"project_id":pid,"job_id":jid,"status":"queued","poll_url":f"/api/v1/jobs/{jid}"}
@app.get("/api/v1/projects")
def projects():return {"items":list_projects()}
@app.get("/api/v1/projects/{pid}")
def project_detail(pid):
 p=get_project(pid)
 if not p:raise HTTPException(404,"Project not found")
 return p
@app.get("/api/v1/jobs/{jid}")
def job_detail(jid):
 j=get_job(jid)
 if not j:raise HTTPException(404,"Job not found")
 return j
@app.post("/api/v1/assets/upload")
async def upload_asset(file:UploadFile=File(...)):
 allowed={".png",".jpg",".jpeg",".webp",".wav",".mp3",".m4a",".mp4",".mov"}
 ext=Path(file.filename or "").suffix.lower()
 if ext not in allowed:raise HTTPException(400,"Supported formats: images, WAV/MP3/M4A audio, MP4/MOV video.")
 name=uuid.uuid4().hex+ext;target=Path("uploads")/name;target.parent.mkdir(exist_ok=True)
 total=0;limit=s.max_upload_mb*1024*1024
 try:
  with target.open("wb") as out:
   while True:
    chunk=await file.read(1024*1024)
    if not chunk:break
    total+=len(chunk)
    if total>limit:raise HTTPException(413,"Upload exceeds MAX_UPLOAD_MB.")
    out.write(chunk)
 except Exception:
  target.unlink(missing_ok=True);raise
 finally:
  await file.close()
 return {"asset_path":str(target),"filename":name,"bytes":total,"content_type":file.content_type}
@app.post("/api/v1/voice/synthesize")
def voice(body:VoiceRequest):
 try:return synthesize_piper(body.text,body.filename)
 except RuntimeError as exc:raise HTTPException(503,str(exc))
@app.post("/api/v1/media/search")
async def media(body:MediaSearchRequest):
 try:return {"items":await search_pexels(body.query,body.per_page)}
 except RuntimeError as exc:raise HTTPException(503,str(exc))
 except Exception as exc:raise HTTPException(502,str(exc)[:500])
@app.post("/api/v1/thumbnails/generate")
def thumbnail(body:ThumbnailRequest):
 try:return create_thumbnail(body.title,body.background_path,body.filename)
 except (ValueError,OSError) as exc:raise HTTPException(400,str(exc))
@app.post("/api/v1/render/slideshow")
def render(body:RenderRequest):
 try:return render_slideshow(body.image_paths,body.output_name,body.width,body.height,body.fps,body.audio_path)
 except (ValueError,RuntimeError) as exc:raise HTTPException(400,str(exc))
@app.get("/api/v1/outputs/{filename}")
def get_output(filename:str):
 if not re.fullmatch(r"[A-Za-z0-9_.-]+",filename):raise HTTPException(400,"Invalid filename.")
 path=(Path("outputs")/filename).resolve()
 if Path("outputs").resolve() not in path.parents or not path.is_file():raise HTTPException(404,"Output not found.")
 return FileResponse(path,filename=filename)
