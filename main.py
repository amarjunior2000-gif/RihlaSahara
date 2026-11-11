from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3, os, time, json, hmac, hashlib, base64, secrets
from typing import List
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(os.getenv("RIHLASAHARA_DB_PATH") or Path(__file__).with_name("rihlasahara.db"))

# Two named administrators. Set strong passwords with environment variables before deployment.
ADMIN_AMAR_PASSWORD = os.getenv("ADMIN_AMAR_PASSWORD", "ChangeThis-Amar-360!")
ADMIN_KAOUTAR_PASSWORD = os.getenv("ADMIN_KAOUTAR_PASSWORD", "ChangeThis-Kaoutar-360!")
ADMIN_ACCOUNTS = {
    "ouhemmi.amar": {"name": "OUHEMMI AMAR", "password": ADMIN_AMAR_PASSWORD},
    "kaoutar.bousbibit": {"name": "KAOUTAR BOUSBIBIT", "password": ADMIN_KAOUTAR_PASSWORD},
}
TOKEN_SECRET = os.getenv("RIHLASAHARA_SECRET_KEY", "development-only-change-this-secret-key")
APP_ENV = os.getenv("APP_ENV", "development").lower()
if APP_ENV == "production":
    if ADMIN_AMAR_PASSWORD == "ChangeThis-Amar-360!" or ADMIN_KAOUTAR_PASSWORD == "ChangeThis-Kaoutar-360!":
        raise RuntimeError("Configurez les deux mots de passe administrateur avant le démarrage en production.")
    if TOKEN_SECRET == "development-only-change-this-secret-key":
        raise RuntimeError("Configurez RIHLASAHARA_SECRET_KEY avant le démarrage en production.")
TOKEN_TTL = 60 * 60 * 8

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def _password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)

def _make_token(username: str) -> str:
    payload = _b64(json.dumps({"sub": username, "exp": int(time.time()) + TOKEN_TTL}).encode())
    signature = _b64(hmac.new(TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).digest())
    return payload + "." + signature

def require_admin(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Connexion administrateur requise")
    token = authorization.split(" ", 1)[1]
    try:
        payload_part, signature = token.split(".", 1)
        expected = _b64(hmac.new(TOKEN_SECRET.encode(), payload_part.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature")
        payload = json.loads(base64.urlsafe_b64decode(payload_part + "=" * (-len(payload_part) % 4)))
        username = payload["sub"]
        if payload["exp"] < int(time.time()) or username not in ADMIN_ACCOUNTS:
            raise ValueError("expired")
        return {"username": username, "name": ADMIN_ACCOUNTS[username]["name"]}
    except Exception:
        raise HTTPException(status_code=401, detail="Session invalide ou expirée")

SEED = [
 (1,"Lagune de Dakhla","Dakhla","Nature","Une lagune spectaculaire entre les dunes du désert et l’océan Atlantique.","https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1000&q=85","OCÉAN & NATURE"),
 (2,"Dunes du Sahara","Sahara","Aventure","Des paysages de sable et de grands espaces pour découvrir le désert.","https://images.unsplash.com/photo-1509316785289-025f5b846b35?auto=format&fit=crop&w=1000&q=85","PAYSAGES"),
 (3,"Laâyoune","Laâyoune","Culture","Une porte d’entrée vers le Sud et une ville à découvrir à son rythme.","https://images.unsplash.com/photo-1519608487953-e999c86e7455?auto=format&fit=crop&w=1000&q=85","VILLE & CULTURE"),
 (4,"Smara","Smara","Culture","Une destination pour découvrir des histoires et traditions sahariennes.","https://images.unsplash.com/photo-1473580044384-7ba9967e16a0?auto=format&fit=crop&w=1000&q=85","PATRIMOINE"),
 (5,"Littoral de Dakhla","Dakhla","Nature","Un littoral ouvert sur l’Atlantique et ses paysages changeants.","https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=1000&q=85","LITTORAL"),
 (6,"Rencontre saharienne","Sahara","Culture","Une expérience à organiser avec des hôtes et guides locaux vérifiés.","https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1000&q=85","EXPÉRIENCE LOCALE")
]

def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    with db_connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS destinations (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL,
          category TEXT NOT NULL, description TEXT NOT NULL,
          image_url TEXT NOT NULL, tag TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS itineraries (
          id INTEGER PRIMARY KEY AUTOINCREMENT, destination TEXT NOT NULL,
          duration TEXT NOT NULL, budget TEXT NOT NULL, interests TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        if db.execute("SELECT COUNT(*) FROM destinations").fetchone()[0] == 0:
            db.executemany("INSERT INTO destinations VALUES (?, ?, ?, ?, ?, ?, ?)", SEED)
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield

app = FastAPI(title="RihlaSahara API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "https://localhost", "http://localhost", "capacitor://localhost",
        "ionic://localhost"
    ],
    allow_origin_regex=r"https://.*",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"]
)

class AdminLogin(BaseModel):
    username: str
    password: str

class DestinationCreate(BaseModel):
    name: str
    city: str
    category: str
    description: str
    image_url: str
    tag: str = "NOUVEAU"

class ItineraryRequest(BaseModel):
    destination: str
    duration: str
    budget: str
    interests: List[str] = Field(default_factory=list)

@app.get("/")
def home():
    return {"project":"RihlaSahara","status":"running","docs":"/docs"}

@app.get("/api/health")
def health():
    return {"status":"ok"}

@app.post("/api/admin/login")
def admin_login(data: AdminLogin):
    account = ADMIN_ACCOUNTS.get(data.username.strip().lower())
    if not account or not secrets.compare_digest(data.password, account["password"]):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    return {"access_token": _make_token(data.username.strip().lower()), "token_type": "bearer", "name": account["name"], "expires_in": TOKEN_TTL}

@app.get("/api/admin/me")
def admin_me(admin=Depends(require_admin)):
    return admin

@app.get("/api/destinations")
def list_destinations():
    with db_connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM destinations ORDER BY id").fetchall()]

@app.get("/api/destinations/{destination_id}")
def destination_detail(destination_id: int):
    with db_connect() as db:
        row = db.execute("SELECT * FROM destinations WHERE id = ?", (destination_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Destination introuvable")
    return dict(row)

@app.post("/api/itineraries")
def create_itinerary(data: ItineraryRequest):
    with db_connect() as db:
        cursor = db.execute("INSERT INTO itineraries (destination,duration,budget,interests) VALUES (?,?,?,?)",
            (data.destination,data.duration,data.budget,", ".join(data.interests)))
        itinerary_id = cursor.lastrowid
        db.commit()
    days = [f"Jour 1 : arrivée et première découverte de {data.destination}.",
            f"Jour 2 : activité autour de {', '.join(data.interests) or 'la découverte locale'}."]
    if data.duration != "2 jours":
        days.append("Jour 3 : découverte complémentaire, temps libre et retour.")
    return {"id":itinerary_id,"title":f"Votre escapade à {data.destination}","days":days,
            "note":"Suggestion indicative de démonstration. Vérifiez les prestataires, distances et disponibilités avant le départ."}


@app.post("/api/admin/destinations")
def add_destination(data: DestinationCreate, admin=Depends(require_admin)):
    with db_connect() as db:
        cursor = db.execute(
            "INSERT INTO destinations (name,city,category,description,image_url,tag) VALUES (?,?,?,?,?,?)",
            (data.name, data.city, data.category, data.description, data.image_url, data.tag)
        )
        db.commit()
        row = db.execute("SELECT * FROM destinations WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)

@app.delete("/api/admin/destinations/{destination_id}")
def remove_destination(destination_id: int, admin=Depends(require_admin)):
    with db_connect() as db:
        cursor = db.execute("DELETE FROM destinations WHERE id = ?", (destination_id,))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Destination introuvable")
    return {"deleted": True, "id": destination_id}
