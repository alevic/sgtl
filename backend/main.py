import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Body, Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
import httpx
import logging

import models
from database import Base, engine, get_db


app = FastAPI(title="SGTL API", version="0.1.0")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://jjeturismo.com.br",
    "https://www.jjeturismo.com.br",
    "https://sgtl.jjeturismo.com.br",
    "https://www.sgtl.jjeturismo.com.br",
    "https://api-sgtl.jjeturismo.com.br",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

ADMIN_USERNAME = os.environ["ADMIN_USERNAME"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
logger = logging.getLogger("sgtl")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def notify_n8n(link_obj: models.Link, event: str) -> None:
    if not N8N_WEBHOOK_URL:
        return
    payload = {
        "event": event,
        "id": link_obj.id,
        "titulo": link_obj.titulo,
        "url": link_obj.url,
        "ordem": link_obj.ordem,
        "descricao": link_obj.descricao,
        "icone": link_obj.icone,
    }
    try:
        resp = httpx.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code >= 400:
            logger.warning("n8n webhook failed: %s %s", resp.status_code, resp.text)
    except Exception as exc:
        # Evita quebrar o fluxo principal se o webhook falhar
        logger.warning("n8n webhook exception: %s", exc)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if username != ADMIN_USERNAME:
        raise credentials_exception
    return username


class LinkCreate(BaseModel):
    titulo: str
    url: HttpUrl
    ordem: Optional[int] = None
    descricao: Optional[str] = None
    icone: Optional[str] = None

    @field_validator("url", mode="before")
    @classmethod
    def ensure_scheme(cls, v: str) -> str:
        if isinstance(v, str) and not v.startswith(("http://", "https://")):
            return f"https://{v}"
        return v

    @field_validator("titulo")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Titulo nao pode ser vazio")
        return v


class LinkUpdate(LinkCreate):
    pass


class LinkRead(BaseModel):
    id: int
    titulo: str
    url: HttpUrl
    ordem: int
    descricao: Optional[str] = None
    icone: Optional[str] = None

    class Config:
        from_attributes = True


@app.get("/links", response_model=List[LinkRead])
def list_links(db: Session = Depends(get_db)):
    links = db.execute(select(models.Link).order_by(models.Link.ordem)).scalars().all()
    return links


@app.post("/links", response_model=LinkRead, status_code=201, dependencies=[Depends(get_current_user)])
def create_link(
    payload: LinkCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    data["url"] = str(payload.url)
    if data.get("ordem") is None:
        max_ordem = db.execute(select(func.max(models.Link.ordem))).scalar()
        data["ordem"] = (max_ordem or 0) + 1
    link = models.Link(**data)
    db.add(link)
    db.commit()
    db.refresh(link)
    background_tasks.add_task(notify_n8n, link, "created")
    return link


@app.put("/links/{link_id}", response_model=LinkRead, dependencies=[Depends(get_current_user)])
def update_link(
    link_id: int,
    payload: LinkUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    data["url"] = str(payload.url)
    link = db.get(models.Link, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link nao encontrado")
    for key, value in data.items():
        setattr(link, key, value)
    db.commit()
    db.refresh(link)
    background_tasks.add_task(notify_n8n, link, "updated")
    return link


@app.delete("/links/{link_id}", status_code=204, dependencies=[Depends(get_current_user)])
def delete_link(
    link_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    link = db.get(models.Link, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link nao encontrado")
    background_tasks.add_task(notify_n8n, link, "deleted")
    db.delete(link)
    db.commit()
    return None


@app.post("/links/reorder", status_code=204, dependencies=[Depends(get_current_user)])
def reorder_links(order_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    existing_ids = set(db.execute(select(models.Link.id)).scalars().all())
    if set(order_ids) != existing_ids:
        raise HTTPException(
            status_code=400,
            detail="Lista de IDs nao corresponde aos links existentes",
        )
    for position, link_id in enumerate(order_ids, start=1):
        db.execute(
            models.Link.__table__.update()
            .where(models.Link.id == link_id)
            .values(ordem=position)
        )
    db.commit()
    return None


@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario ou senha invalidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
