from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from . import auth, models_ingest, ingest, models
import os
import json

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post('/recipes')
def create_recipe(body: dict, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # simple create
    name = body.get('name')
    steps = body.get('steps', [])
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    r = models_ingest.TransformRecipe(name=name, description=body.get('description'), steps=steps)
    db.add(r)
    db.commit()
    db.refresh(r)
    return {'id': r.id, 'name': r.name}


@router.post('/upload')
def upload_file(file: UploadFile = File(...), recipe_id: int = None, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # save to temp
    tmpdir = '/tmp/taaip_uploads'
    os.makedirs(tmpdir, exist_ok=True)
    path = os.path.join(tmpdir, file.filename)
    with open(path, 'wb') as f:
        f.write(file.file.read())
    recipe = None
    if recipe_id:
        recipe = db.query(models_ingest.TransformRecipe).filter_by(id=recipe_id).one_or_none()
        if not recipe:
            raise HTTPException(status_code=404, detail='recipe not found')
        recipe = {'id': recipe.id, 'steps': recipe.steps}
    result = ingest.run_ingest(path, recipe=recipe, uploaded_by=user.username)
    return result


# New v2 endpoints: upload -> staging + detect + run
@router.post('/v2/upload')
def v2_upload(file: UploadFile = File(...), user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    tmpdir = './data/uploads'
    os.makedirs(tmpdir, exist_ok=True)
    path = os.path.join(tmpdir, file.filename)
    with open(path, 'wb') as f:
        f.write(file.file.read())
    # compute simple hash
    try:
        import hashlib
        h = hashlib.sha256()
        with open(path, 'rb') as fh:
            while True:
                chunk = fh.read(4096)
                if not chunk:
                    break
                h.update(chunk)
        file_hash = h.hexdigest()
    except Exception:
        file_hash = None
    # persist ingest_file row
    sql = "INSERT INTO ingest_file (source_system, original_filename, stored_path, file_hash, uploaded_by, uploaded_at) VALUES (:s, :fn, :p, :h, :u, datetime('now'))"
    db.execute(sql, {"s": None, "fn": file.filename, "p": path, "h": file_hash, "u": user.username})
    db.commit()
    row = db.execute("SELECT last_insert_rowid() as id").fetchone()
    ingest_file_id = row['id'] if row is not None else None
    # profile the file using ingest helpers
    try:
        from . import ingest as ingest_helpers
        profile = ingest_helpers.profile_file(path)
    except Exception:
        profile = {"sheets": [], "columns": []}
    # save profile
    db.execute("INSERT INTO stg_raw_dataset_profile (ingest_file_id, columns_json, sample_json, detected_source_hint) VALUES (:id, :cols, :sample, :hint)", {"id": ingest_file_id, "cols": json.dumps(profile.get('columns', [])), "sample": json.dumps(profile.get('sample', [])), "hint": None})
    db.commit()
    return {"ingest_file_id": ingest_file_id, "profile": profile}


@router.post('/v2/run')
def v2_run(body: dict, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    ingest_file_id = body.get('ingest_file_id')
    importer_id = body.get('importer_id')
    if not ingest_file_id:
        raise HTTPException(status_code=400, detail='ingest_file_id required')
    # load file metadata
    row = db.execute("SELECT * FROM ingest_file WHERE id = :id", {"id": ingest_file_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='ingest_file not found')
    path = row['stored_path']
    # detect if needed
    matched = None
    if not importer_id:
        try:
            from . import ingest as ingest_helpers
            matched = ingest_helpers.detect_importer(path)
            importer_id = matched
        except Exception:
            importer_id = None
    # create ingest_run
    db.execute("INSERT INTO ingest_run (ingest_file_id, importer_id, started_at, status) VALUES (:fid, :imp, datetime('now'), :st)", {"fid": ingest_file_id, "imp": importer_id, "st": 'running'})
    db.commit()
    row = db.execute("SELECT last_insert_rowid() as id").fetchone()
    ingest_run_id = row['id'] if row else None
    # run async-like (synchronous here)
    try:
        from . import ingest as ingest_helpers
        result = ingest_helpers.run_import(path, ingest_run_id=ingest_run_id, importer_id=importer_id, db=db, uploaded_by=user.username)
        db.execute("UPDATE ingest_run SET finished_at = datetime('now'), status = :s, row_count_in = :r_in, row_count_loaded = :r_loaded, errors_json = :errs WHERE id = :id", {"s": result.get('status', 'completed'), "r_in": result.get('row_count_in', 0), "r_loaded": result.get('row_count_loaded', 0), "errs": json.dumps(result.get('errors', [])), "id": ingest_run_id})
        db.commit()
    except Exception as e:
        db.execute("UPDATE ingest_run SET finished_at = datetime('now'), status = :s, errors_json = :errs WHERE id = :id", {"s": 'failed', "errs": str(e), "id": ingest_run_id})
        db.commit()
        raise
    return {"ingest_run_id": ingest_run_id, "status": result.get('status', 'completed'), "matched_importer_id": importer_id}


@router.get('/v2/runs/{run_id}')
def v2_run_status(run_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    row = db.execute("SELECT * FROM ingest_run WHERE id = :id", {"id": run_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='run not found')
    return dict(row)
