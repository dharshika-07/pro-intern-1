import uuid
from typing import  Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal
from models.story import Story, StoryNode
from models.job import StoryJob
from schemas.story import ( CompleteStoryNodeResponse, CompleteStoryResponse)
from schemas.story import CreateStoryRequest


from schemas.job import StoryJobResponse
from core.story_generator import StoryGenerator

router = APIRouter(
    prefix="/stories",
    tags=["stories"]
)

def get_session_id(session_id: Optional[str] = Cookie(None)):
    if  not session_id:
        session_id = str(uuid.uuid4())
    return session_id


@router.post("/create", response_model=StoryJobResponse)
def create_story(
         request: CreateStoryRequest,
         background_tasks: BackgroundTasks,
         response: Response,
         session_id: str = Depends(get_session_id),
         db: Session = Depends(get_db)
):
    import os
    import traceback
    from db.database import engine
    
    print(f"[TEMP LOG] POST /api/stories/create - Request URL: /api/stories/create", flush=True)
    print(f"[TEMP LOG] POST /api/stories/create - Request payload: theme={request.theme}", flush=True)
    print(f"[TEMP LOG] POST /api/stories/create - Current working directory: {os.getcwd()}", flush=True)
    print(f"[TEMP LOG] POST /api/stories/create - Absolute SQLite database path: {os.path.abspath(str(engine.url.database)) if engine.url.database else 'None'}", flush=True)

    try:
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        job_id = str(uuid.uuid4())
        print(f"[TEMP LOG] POST /api/stories/create - Generated job_id: {job_id}", flush=True)

        job = StoryJob(
            job_id=job_id,
            session_id=session_id,
            theme=request.theme,
            status="pending",
        )  
        db.add(job)
        db.commit()

        background_tasks.add_task(
            generate_story_task,
            job_id=job_id,
            theme=request.theme,
            session_id=session_id
        )
        print(f"[TEMP LOG] POST /api/stories/create - Response status: 200", flush=True)
        print(f"[TEMP LOG] POST /api/stories/create - Response body: job_id={job.job_id}, status={job.status}, story_id={job.story_id}", flush=True)
        return job
    except Exception as e:
        print(f"[TEMP LOG] POST /api/stories/create - Exception: {e}", flush=True)
        traceback.print_exc()
        raise e

def generate_story_task(job_id: str, theme: str, session_id: str):
    import os
    import traceback
    from db.database import engine, SessionLocal
    
    print(f"[TEMP LOG] generate_story_task - Task started", flush=True)
    print(f"[TEMP LOG] generate_story_task - job_id: {job_id}", flush=True)
    print(f"[TEMP LOG] generate_story_task - Current working directory: {os.getcwd()}", flush=True)
    print(f"[TEMP LOG] generate_story_task - Absolute SQLite database path: {os.path.abspath(str(engine.url.database)) if engine.url.database else 'None'}", flush=True)
    
    db = SessionLocal()
    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
        if not job:
            print(f"[TEMP LOG] generate_story_task - Job {job_id} not found in database!", flush=True)
            return
        
        try:
            job.status = "processing"
            db.commit()

            story = StoryGenerator.generate_story(db, session_id, theme)
            
            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
            
            print(f"[TEMP LOG] generate_story_task - story_id: {story.id}", flush=True)
        except Exception as e: 
            print(f"[TEMP LOG] generate_story_task - Exception: {e}", flush=True)
            traceback.print_exc()
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = str(e)
            db.commit()
    finally:
        db.close()       
                 
             
@router.get(path="/{story_id}/complete", response_model= CompleteStoryResponse)
def get_complete_story(story_id: int, db: Session =Depends(get_db)):
    import os
    import traceback
    from db.database import engine
    
    print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - Request URL: /api/stories/{story_id}/complete", flush=True)
    print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - story_id: {story_id}", flush=True)
    print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - Absolute SQLite database path: {os.path.abspath(str(engine.url.database)) if engine.url.database else 'None'}", flush=True)
    
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        story_exists = story is not None
        print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - Whether the story exists: {story_exists}", flush=True)
        
        if not story:
            print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - Response status: 404", flush=True)
            print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - Response body: Story not found", flush=True)
            raise HTTPException(status_code=404, detail="Story not found")
        
        complete_story = build_complete_story_tree(db, story)
        print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - Response status: 200", flush=True)
        print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - Response body: story_id={complete_story.id}, title={complete_story.title}", flush=True)
        return complete_story
    except Exception as e:
        print(f"[TEMP LOG] GET /api/stories/{story_id}/complete - Exception: {e}", flush=True)
        if not isinstance(e, HTTPException):
            traceback.print_exc()
        raise e


def build_complete_story_tree(db: Session, story: Story) -> CompleteStoryResponse:
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()

    node_dict = {}
    for node in nodes:
        node_response = CompleteStoryNodeResponse(
            id=node.id,
            content=node.content,
            is_ending=node.is_ending,
            is_winning_ending=node.is_winning_ending,
            options=node.options
        )
        node_dict[node.id] = node_response

    root_node = next((node for node in nodes if node.is_root), None)
    if not root_node:
        raise HTTPException(status_code=500, detail="Story root node not found")

    return CompleteStoryResponse(
        id=story.id,
        title= story.title,
        session_id=story.session_id,
        created_at=story.created_at,
        root_node=node_dict[root_node.id],
        all_nodes=node_dict
    )