from datetime import datetime,timezone
from .research_agent import research_brief
from .script_agent import write_script
from .storyboard_agent import make_storyboard
from .seo_agent import optimize_seo
from .quality_agent import review_package
from ..services.youtube import analyze
async def run_production(project,opts):
    competitor=None
    if project["mode"]=="competitor" and project.get("competitor_url"):
        competitor=await analyze(project["competitor_url"])
    topic=project["topic"];language=opts.get("language","English")
    audience=opts.get("audience","general audience");tone=opts.get("tone","engaging, clear, factual")
    duration=opts.get("target_minutes",5)
    research=await research_brief(topic,language)
    if not research:research=f"Research plan for {topic}: verify primary sources, dates, statistics, opposing viewpoints and claims."
    context=""
    if competitor and competitor.get("kind")=="channel":
        channel=competitor.get("channel",{})
        top=competitor.get("top_sample_by_views",[])
        context=f"Channel: {channel.get('title')}; public stats: {channel.get('statistics')}; high-view recent sample: {[{'title':v.get('title'),'views':v.get('statistics',{}).get('viewCount'),'duration':v.get('duration')} for v in top]}. Treat as broad audience-interest signals only."
    elif competitor and competitor.get("kind")=="video":
        context=f"Reference video's public metadata: {competitor.get('video')}. Use only as a topic/interest signal, not as a template to reproduce."
    script=await write_script(topic,language,audience,tone,duration,research,context)
    if not script:script=f"HOOK: What should viewers know about {topic}?\n\nOUTLINE: Context, evidence-backed key points, counterpoint, conclusion.\n\n[Start Ollama for full AI narration.]"
    storyboard=await make_storyboard(script)
    if not storyboard:storyboard="Create one scene per script section. Use licensed footage or original graphics; align visuals to narration."
    seo=await optimize_seo(topic,script,language)
    if not seo:seo=f"SEO draft: accurate title and description for {topic}; natural keywords, no keyword stuffing."
    qa=await review_package(script,storyboard,seo)
    if not qa:qa="Manual QA required: fact-check all claims, review pacing, verify media rights, captions and metadata."
    return {"project_id":project["id"],"created_at":datetime.now(timezone.utc).isoformat(),
            "competitor_analysis":competitor,
            "agents":{"research":{"status":"completed","output":research},"script":{"status":"completed","output":script},
                      "storyboard":{"status":"completed","output":storyboard},"seo":{"status":"completed","output":seo},
                      "quality_review":{"status":"completed","output":qa}},
            "status":"draft_ready","requires_human_review":True,
            "next_steps":["Review research and verify claims","Approve narration and storyboard",
                          "Find licensed visuals and generate voiceover","Render and review final video"]}
