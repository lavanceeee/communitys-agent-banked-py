from IPython.terminal.embed import embed
from fastapi import APIRouter, Depends
from app.utils.JWTutils.authentication import verify_token
from app.services.title_generator import generate_title

router = APIRouter(prefix="/message", tags=["消息"])
