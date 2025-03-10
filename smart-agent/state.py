from pydantic import BaseModel
from typing import Dict, Any

class State(BaseModel):
    data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def update(self, values: Dict[str, Any]) -> None:
        self.data.update(values)

    def clear(self, key: str = None) -> None:
        if key is None:
            self.data.clear()
        else:
            self.data.pop(key, None)

    def delete(self, key: str) -> None:
        self.data.pop(key, None)