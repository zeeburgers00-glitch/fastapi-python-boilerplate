from ..services.ollama import generate_text
async def research_brief(topic:str,language:str)->str:
 prompt=f"Create a research plan for a YouTube video about: {topic}. Language: {language}. List key questions, likely primary sources to consult, claims requiring verification, and opposing viewpoints. Do not invent facts, URLs, citations, or statistics."
 return await generate_text(prompt,"You are a cautious research planner. Separate known context from claims that need external verification.")
