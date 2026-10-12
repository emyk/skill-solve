from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    created_at: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
