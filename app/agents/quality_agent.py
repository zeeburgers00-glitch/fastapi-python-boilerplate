from ..services.ollama import generate_text
async def review_package(script:str,storyboard:str,seo:str)->str:
 return await generate_text(f"Audit this video package. Check factual-risk markers, unsupported claims, repetition, hook clarity, retention pacing, visual coverage, accessibility, and whether SEO matches the content. Return critical fixes and a publish-readiness checklist.\\nSCRIPT:\\n{script[:10000]}\\nSTORYBOARD:\\n{storyboard[:8000]}\\nSEO:\\n{seo[:4000]}","You are a strict editorial QA reviewer. Do not certify factual accuracy without sources.")
