from fastapi import APIRouter, Depends
from .. import auth

router = APIRouter()

@router.get("/me")
def me(effective=Depends(auth.get_effective_user)):
    # Return the effective user dict directly for frontend consumption
    return effective
