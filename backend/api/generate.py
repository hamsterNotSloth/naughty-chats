from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1/generate")

class GenerateRequest(BaseModel):
    character_id: Optional[str] = None
    prompt: str
    pose_preset: Optional[str] = "standing"
    count: int = 1
    orientation: str = "portrait"
    style: str = "realistic"
    quality: str = "balanced"

class GenerationJob(BaseModel):
    id: str
    status: str
    progress: float
    images: List[str] = []
    failure_reason: Optional[str] = None
    estimated_cost: int
    estimated_time: int

# Mock job storage
GENERATION_JOBS = {}

@router.post("")
def submit_generation_job(req: GenerateRequest, user=Depends(get_current_user)):
    """Submit an image generation job"""
    
    # Calculate cost based on quality and count
    quality_multipliers = {"fast": 1, "balanced": 2, "high": 4}
    base_cost = 10
    total_cost = base_cost * quality_multipliers.get(req.quality, 2) * req.count
    
    job_id = f"job_{len(GENERATION_JOBS) + 1}"
    job = {
        "id": job_id,
        "status": "queued",
        "progress": 0.0,
        "images": [],
        "failure_reason": None,
        "estimated_cost": total_cost,
        "estimated_time": 30 * req.count,  # 30 seconds per image
        "user_id": user["user_id"],
        "request": req.dict()
    }
    
    GENERATION_JOBS[job_id] = job
    
    return {
        "job_id": job_id,
        "estimated_cost": total_cost,
        "estimated_time": job["estimated_time"]
    }

@router.get("/jobs/{job_id}")
def get_generation_job(job_id: str, user=Depends(get_current_user)):
    """Get status of a generation job"""
    job = GENERATION_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    
    if job["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return job

@router.get("/jobs")
def list_generation_jobs(status: Optional[str] = None, user=Depends(get_current_user)):
    """List user's generation jobs"""
    user_jobs = [job for job in GENERATION_JOBS.values() if job["user_id"] == user["user_id"]]
    
    if status:
        user_jobs = [job for job in user_jobs if job["status"] == status]
    
    return {"jobs": user_jobs}