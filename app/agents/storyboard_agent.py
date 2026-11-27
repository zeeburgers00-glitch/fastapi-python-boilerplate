from ..services.ollama import generate_text
async def make_storyboard(script:str)->str:
 return await generate_text("Turn this original script into a scene-by-scene storyboard. For each scene give narration cue, duration estimate, visual idea, asset type, on-screen text, and transition. Prefer original graphics or properly licensed footage. Script:\\n"+script,"You are a video director and editor. Be concrete and production-ready.")
