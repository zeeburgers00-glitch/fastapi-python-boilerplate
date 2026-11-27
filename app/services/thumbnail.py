from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
def create_thumbnail(title:str,background_path:str|None=None,filename:str="thumbnail.jpg"):
 outdir=Path("outputs").resolve();outdir.mkdir(parents=True,exist_ok=True)
 if background_path and Path(background_path).is_file():
  im=Image.open(background_path).convert("RGB")
  im=ImageOps.fit(im,(1280,720))
 else:
  im=Image.new("RGB",(1280,720),(18,24,40))
  px=im.load()
  for y in range(720):
   for x in range(1280):
    t=x/1280
    px[x,y]=(int(15+25*t),int(24+15*t),int(45+65*t))
 draw=ImageDraw.Draw(im)
 try:font=ImageFont.truetype("DejaVuSans-Bold.ttf",82)
 except OSError:font=ImageFont.load_default()
 words=title.upper().split();lines=[];line=""
 for word in words:
  test=(line+" "+word).strip()
  if draw.textbbox((0,0),test,font=font,stroke_width=2)[2]>1100 and line:
   lines.append(line);line=word
  else:line=test
 if line:lines.append(line)
 lines=lines[:4]; y=max(70,(720-len(lines)*100)//2)
 for line in lines:
  draw.text((64,y),line,font=font,fill="white",stroke_width=4,stroke_fill="#101522")
  y+=100
 out=outdir/filename;im.save(out,quality=92)
 return {"thumbnail_path":str(out),"width":1280,"height":720,"bytes":out.stat().st_size}
