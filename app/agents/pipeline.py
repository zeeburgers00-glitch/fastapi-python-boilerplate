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
    topic=project["topic"]
    language=opts.get("language","English")
    audience=opts.get("audience","general audience")
    tone=opts.get("tone","engaging, clear, factual")
    duration=opts.get("target_minutes",5)
    research=await research_brief(topic,language)
    if not research:
        research=f"Research plan for {topic}: verify primary sources, dates, statistics, opposing viewpoints and any claims before publication."
    script=await write_script(topic,language,audience,tone,duration,research)
    if not script:
        script=f"HOOK: What should viewers know about {topic}?\n\nOUTLINE: Context, key points supported by verified evidence, counterpoint, conclusion.\n\n[Start Ollama for full AI narration.]"
    storyboard=await make_storyboard(script)
    if not storyboard:
        storyboard="Create one scene per script section. Use licensed footage or original graphics; align every visual to narration."
    seo=await optimize_seo(topic,script,language)
    if not seo:
        seo=f"SEO draft: create an accurate title and description for {topic}; use natural keywords and avoid keyword stuffing."
    qa=await review_package(script,storyboard,seo)
    if not qa:
        qa="Manual QA required: fact-check all claims, review pacing, verify media rights, captions and metadata."
    return {
        "project_id":project["id"],
        "created_at":datetime.now(timezone.utc).isoformat(),
        "competitor_analysis":competitor,
        "agents":{"research":{"status":"completed","output":research},
                  "script":{"status":"completed","output":script},
                  "storyboard":{"status":"completed","output":storyboard},
                  "seo":{"status":"completed","output":seo},
                  "quality_review":{"status":"completed","output":qa}},
        "status":"draft_ready",
        "requires_human_review":True,
        "next_steps":["Review research and verify factual claims","Approve narration and storyboard",
                      "Create or attach licensed visuals and voiceover","Render and review final video"]
    }
