import shutil,subprocess
from pathlib import Path
from ..config import get_settings
def synthesize_piper(text:str,filename:str="voice.wav"):
 s=get_settings()
 if not s.piper_model_path:raise RuntimeError("Set PIPER_MODEL_PATH to a downloaded Piper voice model (.onnx).")
 exe=shutil.which(s.piper_binary)
 if not exe:raise RuntimeError("Piper executable not found. Install Piper locally and set PIPER_BINARY.")
 outdir=Path("outputs").resolve();outdir.mkdir(parents=True,exist_ok=True)
 out=outdir/filename
 p=subprocess.run([exe,"--model",s.piper_model_path,"--output_file",str(out)],input=text,text=True,capture_output=True,timeout=600)
 if p.returncode:raise RuntimeError(p.stderr[-2000:])
 return {"audio_path":str(out),"bytes":out.stat().st_size,"engine":"Piper"}
