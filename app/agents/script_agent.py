from ..services.ollama import generate_text
async def write_script(topic:str,language:str,audience:str,tone:str,duration:int,research:str)->str:
 prompt=f"Write an original {duration}-minute YouTube narration about {topic}. Language: {language}. Audience: {audience}. Tone: {tone}. Use this research plan: {research}. Include a strong but accurate hook, clear story arc, spoken-language narration, scene headings, and a concise conclusion. Never invent facts; mark placeholders [VERIFY]."
 return await generate_text(prompt,"You are an experienced YouTube writer. Do not imitate any named creator or reproduce copyrighted scripts.")
