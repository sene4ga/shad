import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel


app = FastAPI()

class ToShort(BaseModel):
    url: str

class Shorted(BaseModel):
    url: str
    key : str

keysdb = {}
urlsdb = {}

@app.post('/shorten', response_model=Shorted, status_code=201)
def short_url(data : ToShort):
    if data.url in urlsdb:
        return Shorted(key=urlsdb[data.url], url=data.url)

    key = str(uuid.uuid4())
    keysdb[key] = data.url
    urlsdb[data.url] = key

    return Shorted(key=key, url=data.url)


@app.get('/go/{key}'
        , status_code=307
        , responses=
         {
             307: {
                "content": {
                    "application/json": {
                        "schema": {"title": "Response Redirect To Url Go  Key  Get"}
                    }
                }
             }
        }
         )
def redirect_to_url(key : str):
    url = keysdb.get(key)
    if not url:
        raise HTTPException(status_code=404, detail='Key not found')
    return RedirectResponse(url=url, status_code=307)
