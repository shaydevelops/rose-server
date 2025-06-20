"""Laravel-style queue facade for elegant job dispatching."""

from typing import Any, Dict, Type

from ..services import get_job_store


class Queueable:
    """Base class for queueable jobs."""

    queue_name: str = "default"
    max_attempts: int = 3

    @classmethod
    async def dispatch(cls, *args, **kwargs) -> int:
        """Dispatch job to queue."""
        job_store = get_job_store()
        payload = cls.prepare_payload(*args, **kwargs)
        job = await job_store.enqueue(job_type=cls.get_job_type(), payload=payload, max_attempts=cls.max_attempts)
        return job.id

    @classmethod
    def prepare_payload(cls, *args, **kwargs) -> Dict[str, Any]:
        """Prepare job payload from arguments."""
        return kwargs

    @classmethod
    def get_job_type(cls) -> str:
        """Get job type identifier."""
        return cls.__name__.lower().replace("job", "")

    @classmethod
    def attempts(cls, max_attempts: int) -> Type["Queueable"]:
        """Set max attempts (fluent interface)."""
        cls.max_attempts = max_attempts
        return cls


class TrainingJob(Queueable):
    """Fine-tuning training job."""

    @classmethod
    def prepare_payload(cls, model: str, training_file: str, **kwargs) -> Dict[str, Any]:
        return {
            "model": model,
            "training_file": training_file,
            "job_id": kwargs.get("job_id"),
            "hyperparameters": kwargs.get("hyperparameters", {}),
            "suffix": kwargs.get("suffix", "custom"),
        }

    @classmethod
    def get_job_type(cls) -> str:
        return "training"


class EvalJob(Queueable):
    """Model evaluation job."""

    @classmethod
    def prepare_payload(cls, eval_id: str, model: str, eval: str, **kwargs) -> Dict[str, Any]:
        return {
            "eval_id": eval_id,
            "model": model,
            "eval": eval,
            "metadata": kwargs.get("metadata", {}),
        }

    @classmethod
    def get_job_type(cls) -> str:
        return "eval"


class Queue:
    """Laravel-style queue helper."""

    @staticmethod
    async def push(job_type: str, payload: dict, max_attempts: int = 3) -> int:
        """Push a raw job to queue."""
        job_store = get_job_store()
        job = await job_store.enqueue(job_type=job_type, payload=payload, max_attempts=max_attempts)
        return job.id

    @staticmethod
    async def cancel(job_id: int) -> bool:
        """Cancel a job."""
        job_store = get_job_store()
        return await job_store.request_cancel(job_id)
