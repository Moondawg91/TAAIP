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
