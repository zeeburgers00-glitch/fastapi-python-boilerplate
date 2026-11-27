from ..services.ollama import generate_text
async def optimize_seo(topic:str,script:str,language:str)->str:
 return await generate_text(f"Create an honest YouTube SEO draft for topic {topic} in {language}. Based on this script: {script[:12000]}. Return 5 accurate title options, concise description, chapters if timestamps are unavailable label them estimated, 10 relevant keyword phrases, and 3 thumbnail concepts. Avoid keyword stuffing and do not claim guaranteed ranking or virality.","You are a YouTube metadata editor. Metadata must accurately describe the actual video.")
