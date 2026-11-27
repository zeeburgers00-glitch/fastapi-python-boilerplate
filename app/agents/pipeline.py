from datetime import datetime,timezone
from ..services.ollama import generate_text
from ..services.youtube import analyze
SYSTEM=("You are a careful YouTube production assistant. Create original content. Never copy a competitor's script, footage, voice, or thumbnail. Never promise virality. Do not invent facts or citations.")
async def run_production(project,opts):
 competitor=None
 if project["mode"]=="competitor" and project.get("competitor_url"):
  competitor=await analyze(project["competitor_url"])
 prompt=f"""Build a production-ready original YouTube package.
Topic: {project['topic']}
Format: {opts.get('target_format','long')}; duration: {opts.get('target_minutes',5)} minutes.
Language: {opts.get('language','English')}; audience: {opts.get('audience','general')}; tone: {opts.get('tone','engaging')}.
Public competitor metadata for high-level inspiration only: {competitor}
Return: audience angle, 3 titles, opening hook, full narration script with scene headings,
storyboard/visual plan, thumbnail concept, description, chapters, keywords,
fact-check checklist, and editing notes. Flag claims needing verification."""
 output=await generate_text(prompt,SYSTEM)
 if not output:
  output=f"""DRAFT PRODUCTION BRIEF: {project['topic']}
Ollama is unavailable. Start Ollama and pull the configured model to generate a full package.
HOOK: Discover the most important things to understand about {project['topic']}.
SCRIPT OUTLINE: Hook; context; three evidence-backed sections; counterpoint; conclusion.
VISUALS: Use original graphics and media you have permission to use.
SEO: Create an accurate title and description; avoid keyword stuffing.
FACT CHECK: Verify every statistic, quotation, date and claim before publication."""
 return {"project_id":project["id"],"created_at":datetime.now(timezone.utc).isoformat(),"competitor_analysis":competitor,"production_package":output,"status":"draft_ready","requires_human_review":True}
