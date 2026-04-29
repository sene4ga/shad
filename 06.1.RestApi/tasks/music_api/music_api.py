from typing import List, Optional
import secrets
import string
from fastapi import FastAPI, APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI()

trdb = {}
trset = set()
counter = 1

class CreateUser(BaseModel):
    name : str
    age :int

class CreateTrack(BaseModel):
    name: str
    artist: str
    year: Optional[int] = None
    genres: List[str] = []

def VerifyToken(x_token: Optional[str] = Header(None)):
    if x_token is None:
        raise HTTPException(status_code=401, detail='Missing token')
    if x_token not in trset:
        raise HTTPException(status_code=401, detail='Incorrect token')

reg_router = APIRouter(prefix="/api/v1/registration")
tracks_router = APIRouter(prefix="/api/v1/tracks", dependencies=[Depends(VerifyToken)])


@reg_router.post('/register_user')
def register_user(user : CreateUser):
    token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
    trset.add(token)
    return {"token": token}

@tracks_router.post('/add_track', status_code=201)
def add_track(track: CreateTrack):
    global counter
    t_counter = counter
    trdb[t_counter] = {
        "name": track.name,
        "artist": track.artist,
        "year": track.year,
        "genres": track.genres
    }
    counter += 1
    return {"track_id": t_counter}

@tracks_router.get('/all')
def get_all_tracks():
    return list(trdb.values())

@tracks_router.get('/search')
def search_tracks(name: Optional[str] = None, artist: Optional[str] = None):
    if name is None and artist is None:
        raise HTTPException(status_code=422, detail='You should specify at least one search argument')

    track_id = []
    for t_id, track in trdb.items():
        ok = True
        if name is not None and track["name"] != name:
            ok = False
        if artist is not None and track["artist"] != artist:
            ok = False

        if ok:
            track_id.append(t_id)

    return {"track_ids" : track_id}

@tracks_router.get('/{track_id}')
def get_track(track_id : int):
    if track_id not in trdb:
        raise HTTPException(status_code=404, detail='Invalid track_id')
    track = trdb[track_id]
    return {"name" : track["name"], "artist" : track["artist"]}

@tracks_router.delete('/{track_id}')
def delete_track(track_id : int):
    if track_id not in trdb:
        raise HTTPException(status_code=404, detail='Invalid track_id')
    del trdb[track_id]
    return {"status" : "track removed"}

app.include_router(reg_router)
app.include_router(tracks_router)
