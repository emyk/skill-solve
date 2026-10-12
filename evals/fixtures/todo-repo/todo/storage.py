"""Persistence for tasks: one JSON file holding every task."""
import json
import os

from .models import Task

DEFAULT_PATH = os.path.expanduser("~/.todo.json")


class JsonStore:
    def __init__(self, path=DEFAULT_PATH):
        self.path = path

    def _load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return [Task.from_dict(d) for d in json.load(f)]

    def _save(self, tasks):
        with open(self.path, "w") as f:
            json.dump([t.to_dict() for t in tasks], f)

    def add(self, title):
        tasks = self._load()
        task = Task(id=max((t.id for t in tasks), default=0) + 1, title=title)
        tasks.append(task)
        self._save(tasks)
        return task

    def list(self, include_done=False):
        return [t for t in self._load() if include_done or not t.done]

    def complete(self, task_id):
        tasks = self._load()
        for t in tasks:
            if t.id == task_id:
                t.done = True
                self._save(tasks)
                return t
        raise KeyError(task_id)
