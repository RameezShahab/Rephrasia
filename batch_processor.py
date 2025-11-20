"""Batch processing for bulk operations."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Any
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchJob:
    def __init__(self, job_type: str, items: List[Any], metadata: Dict = None):
        self.job_id = uuid.uuid4().hex
        self.job_type = job_type
        self.items = items
        self.metadata = metadata or {}
        self.status = JobStatus.PENDING
        self.results = []
        self.errors = []
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.progress = 0
        self.total = len(items)

    def update_progress(self, completed: int):
        self.progress = completed

    def complete(self, results: List[Any]):
        self.results = results
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail(self, error: str):
        self.status = JobStatus.FAILED
        self.errors.append(error)
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "progress": self.progress,
            "total": self.total,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": self.results if self.status == JobStatus.COMPLETED else None,
            "errors": self.errors if self.errors else None
        }


class BatchProcessor:
    def __init__(self):
        self._jobs: Dict[str, BatchJob] = {}

    def create_job(self, job_type: str, items: List[Any], metadata: Dict = None) -> str:
        job = BatchJob(job_type, items, metadata)
        self._jobs[job.job_id] = job
        return job.job_id

    def get_job(self, job_id: str) -> BatchJob | None:
        return self._jobs.get(job_id)

    def process_job(self, job_id: str, processor_func):
        job = self.get_job(job_id)
        if not job:
            return

        job.status = JobStatus.PROCESSING
        results = []
        
        try:
            for idx, item in enumerate(job.items):
                result = processor_func(item)
                results.append(result)
                job.update_progress(idx + 1)
            
            job.complete(results)
        except Exception as e:
            job.fail(str(e))

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove jobs older than max_age_hours."""
        current_time = datetime.utcnow()
        to_delete = []
        
        for job_id, job in self._jobs.items():
            if job.completed_at:
                age = (current_time - job.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_delete.append(job_id)
        
        for job_id in to_delete:
            del self._jobs[job_id]


batch_processor = BatchProcessor()
