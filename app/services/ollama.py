import httpx
from ..config import get_settings
async def generate_text(prompt,system=""):
 s=get_settings()
 try:
  async with httpx.AsyncClient(timeout=180) as c:
   r=await c.post(s.ollama_base_url.rstrip("/")+"/api/generate",json={"model":s.ollama_model,"prompt":prompt,"system":system,"stream":False})
   r.raise_for_status(); return r.json().get("response","").strip()
 except (httpx.HTTPError,ValueError,KeyError): return ""
