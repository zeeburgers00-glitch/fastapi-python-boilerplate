import uuid
from fastapi import FastAPI,HTTPException,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .db import init_db,create_project,create_job,get_project,list_projects,get_job,update_job,save_result
from .schemas import ProjectCreate,RenderRequest
from .agents.pipeline import run_production
from .services.render import render_slideshow
s=get_settings()
app=FastAPI(title=s.app_name,version="0.1.0",description="Local-first YouTube production backend.")
app.add_middleware(CORSMiddleware,allow_origins=s.allowed_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup():init_db()
@app.get("/")
def root():return {"message":"YouTube AI Factory API","docs":"/docs","health":"/health"}
@app.get("/health")
def health():return {"status":"ok","app":s.app_name,"environment":s.app_env}
@app.get("/api/v1/capabilities")
def capabilities():
 return {"modes":["topic","competitor"],"modules":["competitor-public-metadata","script-and-storyboard-draft","seo-draft","ffmpeg-slideshow-render"],"ollama_configured":True,"youtube_api_configured":bool(s.youtube_data_api_key),"limitations":["Ollama must be running for model-generated packages.","Competitor analysis uses official public metadata only.","Rendering currently assembles user-supplied local images and optional audio."]}
async def process_project(pid,jid,opts):
 try:
  update_job(jid,"running","research_and_script")
  project=get_project(pid)
  result=await run_production(project,opts)
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
@app.post("/api/v1/render/slideshow")
def render(body:RenderRequest):
 try:return render_slideshow(body.image_paths,body.output_name,body.width,body.height,body.fps,body.audio_path)
 except (ValueError,RuntimeError) as exc:raise HTTPException(400,str(exc))
