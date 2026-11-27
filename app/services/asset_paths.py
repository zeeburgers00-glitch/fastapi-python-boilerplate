from pathlib import Path
def safe_upload_path(value:str)->Path:
 root=Path("uploads").resolve()
 root.mkdir(parents=True,exist_ok=True)
 path=Path(value).resolve()
 if root not in path.parents:
  raise ValueError("Media inputs must be inside the ./uploads directory.")
 if not path.is_file():
  raise ValueError(f"Uploaded asset does not exist: {path.name}")
 return path
