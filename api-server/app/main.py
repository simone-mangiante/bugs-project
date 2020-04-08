from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import time
import os
import redis
import json

# model for bug creation from users (POST body)
class BugRequest(BaseModel):
    user: str
    description: str
    
# model for bugs stored in Redis
class Bug(BaseModel):
    id: str
    timestamp: str
    user: str
    description: str

# model for POST response
class OutputPost(BaseModel):
    environment: str = None
    bug_id: str

# model for GET response
class OutputGet(BaseModel):
    environment: str = None
    bugs: List[Bug]

# main FastAPI application
app = FastAPI()

# directory where HTML templates are
templates = Jinja2Templates(directory="templates")

# get environment (dev or prod)
BUGS_ENV = os.getenv('BUGS_ENV')

# get Redis host
REDIS_HOST = os.getenv('REDIS_HOST')

@app.get("/api/bugs", response_model=OutputGet)
@app.get("/web/bugs")
def get_bugs(request: Request):
    # get bugs list from redis
    bugs_list = []
    redis_client = redis.Redis(host=REDIS_HOST)
    for key in redis_client.scan_iter():
       bugs_list.append(Bug(**json.loads(redis_client.get(key))))
    
    # create the response
    response = OutputGet(bugs=bugs_list)
    if BUGS_ENV and BUGS_ENV == 'dev':
        response.environment = BUGS_ENV
    
    # /api/* is for json response
    if 'api' in request.url.path:
        return response
    return templates.TemplateResponse("bugs.html", {'request': request, 'bugs': bugs_list, 'env': BUGS_ENV})

@app.post("/api/bugs", response_model=OutputPost, status_code=201)
def create_bug(bug_request: BugRequest):
    # check request parameters
    if not bug_request.user:
        raise HTTPException(status_code=400, detail="The reques did not contain the 'user' parameter")
    if not bug_request.description:
        raise HTTPException(status_code=400, detail="The reques did not contain the 'description' parameter")
        
    # connect to Redis
    redis_client = redis.Redis(host=REDIS_HOST)
    
    # get time from Redis
    epochs, micros = redis_client.time()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epochs))
    
    # build the bug object
    bug = Bug(id=str(epochs)+':'+str(micros), timestamp=timestamp, user=bug_request.user, description=bug_request.description)
    
    # put the bug object in Redis
    if not redis_client.set(bug.id, json.dumps(bug.dict())):
        raise HTTPException(status_code=500, detail="Database not available")
        
    # create the response
    response = OutputPost(bug_id=bug.id)
    if BUGS_ENV and BUGS_ENV == 'dev':
       response.environment = BUGS_ENV
    
    return response
