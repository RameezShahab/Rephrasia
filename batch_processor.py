"""
batch_processor.py — Synchronous batch processing for rephrase/translate.

NOTE: Jobs are processed sequentially in the calling thread.
For production workloads with many items, consider migrating to Celery + Redis.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from config import MAX_BATCH_SIZE

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"


class BatchJob:
    """Represents a single batch processing job."""

    def __init__(self, job_type: str, items: List[Any], metadata: Optional[Dict] = None):
        self.job_id      = uuid.uuid4().hex
        self.job_type    = job_type
        self.items       = items
        self.metadata    = metadata or {}
        self.status      = JobStatus.PENDING
        self.results: List[Any] = []
        self.errors: List[str]  = []
        self.created_at  = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.progress    = 0
        self.total       = len(items)

    def update_progress(self, completed: int) -> None:
        self.progress = completed

    def complete(self, results: List[Any]) -> None:
        self.results      = results
        self.status       = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        self.status       = JobStatus.FAILED
        self.errors.append(error)
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "job_id":       self.job_id,
            "job_type":     self.job_type,
            "status":       self.status.value,
            "progress":     self.progress,
            "total":        self.total,
            "created_at":   self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results":      self.results if self.status == JobStatus.COMPLETED else None,
            "errors":       self.errors  if self.errors  else None,
        }


class BatchProcessor:
    """In-memory batch job queue. Jobs run synchronously in the request thread."""

    def __init__(self) -> None:
        self._jobs: Dict[str, BatchJob] = {}

    def create_job(
        self,
        job_type: str,
        items: List[Any],
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Create a new batch job and return its job_id.

        Raises:
            ValueError: If items list exceeds MAX_BATCH_SIZE.
        """
        if len(items) > MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch size {len(items)} exceeds maximum of {MAX_BATCH_SIZE}."
            )
        job = BatchJob(job_type, items, metadata)
        self._jobs[job.job_id] = job
        logger.debug("Batch job created: %s (%d items, type=%s)", job.job_id, len(items), job_type)
        return job.job_id

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Return the BatchJob with *job_id*, or None if not found."""
        return self._jobs.get(job_id)

    def process_job(self, job_id: str, processor_func: Callable) -> None:
        """
        Execute *processor_func* sequentially over all items in the job.
        Updates job status throughout; marks FAILED on any exception.
        """
        job = self.get_job(job_id)
        if not job:
            logger.warning("process_job called with unknown job_id: %s", job_id)
            return

        job.status = JobStatus.PROCESSING
        results: List[Any] = []

        try:
            for idx, item in enumerate(job.items):
                result = processor_func(item)
                results.append(result)
                job.update_progress(idx + 1)
                logger.debug("Batch job %s: %d/%d done.", job_id, idx + 1, job.total)

            job.complete(results)
            logger.info("Batch job %s completed (%d items).", job_id, job.total)

        except Exception as exc:
            logger.exception("Batch job %s failed at item %d.", job_id, job.progress)
            job.fail(str(exc))

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove completed/failed jobs older than *max_age_hours*.

        Returns:
            Number of jobs removed.
        """
        current_time = datetime.utcnow()
        to_delete = [
            job_id
            for job_id, job in self._jobs.items()
            if job.completed_at
            and (current_time - job.completed_at).total_seconds() / 3600 > max_age_hours
        ]
        for job_id in to_delete:
            del self._jobs[job_id]

        if to_delete:
            logger.info("Cleaned up %d old batch job(s).", len(to_delete))
        return len(to_delete)


batch_processor = BatchProcessor()
