from __future__ import annotations
import shutil, tempfile, uuid, zipfile
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from src.pdf_splitter.pdf_tools import add_watermark, images_to_pdf, number_pages, pdf_to_images, protect_pdf, reorder_pdf, set_metadata
router=APIRouter(prefix='/api/pdf',tags=['PDF Advanced']); _JOBS={}
def _tmp(suffix='.pdf'): return Path(tempfile.gettempdir())/f'docsplit_{uuid.uuid4().hex}{suffix}'
async def _save(file,images=False):
    allowed=('.jpg','.jpeg','.png','.webp') if images else ('.pdf',)
    if not file.filename or not file.filename.lower().endswith(allowed): raise HTTPException(400,'Tipo de arquivo não permitido.')
    p=_tmp(Path(file.filename).suffix.lower())
    with p.open('wb') as f: shutil.copyfileobj(file.file,f)
    return p
def _store(p,name,media='application/pdf'):
    j=uuid.uuid4().hex; s=_tmp(p.suffix or '.bin'); shutil.copy2(p,s); _JOBS[j]=(s,name,media); return {'success':True,'download_id':j,'download_url':f'/api/pdf/advanced-download/{j}','filename':name}
@router.get('/advanced-download/{job_id}')
def download(job_id):
    item=_JOBS.get(job_id)
    if not item or not item[0].exists(): raise HTTPException(404,'Arquivo não encontrado ou expirado.')
    return FileResponse(item[0],media_type=item[2],filename=item[1])
@router.post('/reorder')
async def reorder(file=File(...),order:str=Form(...)):
    p=await _save(file)
    try: out=_tmp(); reorder_pdf(p,out,[int(x.strip()) for x in order.split(',') if x.strip()]); return _store(out,'pdf_reordenado.pdf')
    except ValueError as e: raise HTTPException(400,str(e)) from e
    finally: p.unlink(missing_ok=True)
@router.post('/pdf-to-images')
async def pdf_to_images_api(file=File(...),dpi:int=Form(150)):
    p=await _save(file); d=Path(tempfile.mkdtemp(prefix='docsplit_img_'))
    try:
        files=pdf_to_images(p,d,dpi); z=_tmp('.zip')
        with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:
            for item in files: f.write(item,item.name)
        return _store(z,'pdf_imagens.zip','application/zip')
    except ValueError as e: raise HTTPException(400,str(e)) from e
    finally: p.unlink(missing_ok=True); shutil.rmtree(d,ignore_errors=True)
@router.post('/images-to-pdf')
async def images_to_pdf_api(files=list[UploadFile]=File(...)):
    paths=[await _save(f,True) for f in files]
    try: out=_tmp(); images_to_pdf(paths,out); return _store(out,'imagens.pdf')
    finally:
        for p in paths: p.unlink(missing_ok=True)
@router.post('/watermark')
async def watermark(file=File(...),text:str=Form(...),opacity:float=Form(.25)):
    p=await _save(file)
    try: out=_tmp(); add_watermark(p,out,text,opacity); return _store(out,'pdf_marca_dagua.pdf')
    except ValueError as e: raise HTTPException(400,str(e)) from e
    finally: p.unlink(missing_ok=True)
@router.post('/number-pages')
async def number(file=File(...),position:str=Form('bottom-right')):
    p=await _save(file)
    try: out=_tmp(); number_pages(p,out,position); return _store(out,'pdf_numerado.pdf')
    except ValueError as e: raise HTTPException(400,str(e)) from e
    finally: p.unlink(missing_ok=True)
@router.post('/metadata')
async def metadata(file=File(...),title:str=Form(''),author:str=Form(''),subject:str=Form('')):
    p=await _save(file)
    try: out=_tmp(); set_metadata(p,out,title,author,subject); return _store(out,'pdf_metadados.pdf')
    finally: p.unlink(missing_ok=True)
@router.post('/protect')
async def protect(file=File(...),password:str=Form(...)):
    p=await _save(file)
    try: out=_tmp(); protect_pdf(p,out,password); return _store(out,'pdf_protegido.pdf')
    except ValueError as e: raise HTTPException(400,str(e)) from e
    finally: p.unlink(missing_ok=True)
