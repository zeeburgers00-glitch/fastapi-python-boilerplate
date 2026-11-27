from ..services.ollama import generate_text
async def write_script(topic:str,language:str,audience:str,tone:str,duration:int,research:str,competitor_context:str="")->str:
 prompt=f"""Write an original {duration}-minute YouTube narration about {topic}. Language: {language}. Audience: {audience}. Tone: {tone}.
Research plan: {research}
Competitor strategy context (high-level patterns only; never copy titles, scripts, voice, scenes or branding): {competitor_context}
Use a distinct angle, strong accurate hook, clear story arc, spoken-language narration, scene headings and concise conclusion. Never invent facts; mark unsupported claims [VERIFY]."""
 return await generate_text(prompt,"You are an experienced YouTube writer. Create original work and never imitate a named creator.")
