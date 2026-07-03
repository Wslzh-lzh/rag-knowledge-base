from __future__ import annotations

import asyncio
import logging
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskInfo:
    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    """轻量级异步任务队列。

    基于 asyncio 的内存任务队列，适合中小型部署。
    生产环境可替换为 Celery/RQ + Redis。
    """

    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers
        self._tasks: dict[str, TaskInfo] = {}
        self._queue: deque[str] = deque()
        self._running: set[str] = set()
        self._lock = asyncio.Lock()
        self._task_funcs: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._started = False
        self._worker_tasks: list[asyncio.Task] = []

    def register_task(self, name: str, func: Callable[..., Awaitable[Any]]) -> None:
        self._task_funcs[name] = func
        logger.info(f"Task registered: {name}")

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        for i in range(self._max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)
        logger.info(f"Task queue started with {self._max_workers} workers")

    async def stop(self) -> None:
        self._started = False
        for task in self._worker_tasks:
            task.cancel()
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        logger.info("Task queue stopped")

    async def submit(self, task_name: str, *args, **kwargs) -> str:
        if task_name not in self._task_funcs:
            raise ValueError(f"Unknown task: {task_name}")

        task_id = str(uuid.uuid4())
        task_info = TaskInfo(
            task_id=task_id,
            name=task_name,
            meta={"args": list(args), "kwargs": kwargs},
        )

        async with self._lock:
            self._tasks[task_id] = task_info
            self._queue.append(task_id)

        logger.info(f"Task submitted: {task_name} ({task_id})")
        return task_id

    async def get_status(self, task_id: str) -> TaskInfo | None:
        async with self._lock:
            return self._tasks.get(task_id)

    async def _worker(self, worker_name: str) -> None:
        logger.debug(f"Worker {worker_name} started")
        while self._started:
            task_id = None
            async with self._lock:
                if self._queue:
                    task_id = self._queue.popleft()
                    if task_id:
                        self._running.add(task_id)

            if task_id is None:
                await asyncio.sleep(0.1)
                continue

            task_info = self._tasks[task_id]
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.utcnow()

            try:
                logger.info(f"Worker {worker_name} running task {task_info.name} ({task_id})")
                func = self._task_funcs[task_info.name]
                result = await func(*task_info.meta.get("args", []), **task_info.meta.get("kwargs", {}))
                task_info.result = result
                task_info.status = TaskStatus.COMPLETED
                task_info.progress = 1.0
                logger.info(f"Task completed: {task_info.name} ({task_id})")
            except Exception as e:
                task_info.error = str(e)
                task_info.status = TaskStatus.FAILED
                logger.error(f"Task failed: {task_info.name} ({task_id}): {e}", exc_info=True)
            finally:
                task_info.completed_at = datetime.utcnow()
                async with self._lock:
                    self._running.discard(task_id)

    async def update_progress(self, task_id: str, progress: float, message: str | None = None) -> None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.progress = progress
                if message:
                    task.meta["message"] = message


_task_queue: TaskQueue | None = None


def get_task_queue() -> TaskQueue:
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(max_workers=4)
    return _task_queue
