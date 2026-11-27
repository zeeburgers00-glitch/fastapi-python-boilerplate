import shutil,subprocess
from pathlib import Path
from ..config import get_settings
def render_slideshow(image_paths,output_name,width,height,fps,audio_path=None):
 ff=shutil.which(get_settings().ffmpeg_binary)
 if not ff:raise RuntimeError("FFmpeg not installed or not on PATH.")
 paths=[Path(p).resolve() for p in image_paths]
 if not paths or any(not p.is_file() for p in paths):raise ValueError("All image_paths must be existing local files.")
 outdir=Path("outputs").resolve();outdir.mkdir(parents=True,exist_ok=True);out=outdir/output_name
 cmd=[ff,"-y"]
 for p in paths:cmd += ["-loop","1","-t","4","-i",str(p)]
 filters=[];labels=[]
 for i in range(len(paths)):
  label=f"v{i}";filters.append(f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[{label}]");labels.append(f"[{label}]")
 filters.append("".join(labels)+f"concat=n={len(paths)}:v=1:a=0[outv]")
 cmd += ["-filter_complex",";".join(filters),"-map","[outv]"]
 if audio_path:
  a=Path(audio_path).resolve()
  if not a.is_file():raise ValueError("audio_path does not exist.")
  cmd += ["-i",str(a),"-map",f"{len(paths)}:a","-shortest"]
 cmd += ["-c:v","libx264","-preset","veryfast","-crf","20",str(out)]
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=1800)
 if p.returncode:raise RuntimeError(p.stderr[-2500:])
 return {"output_path":str(out),"bytes":out.stat().st_size,"format":"mp4"}
