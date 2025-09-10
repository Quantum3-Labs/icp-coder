from abc import abstractmethod, ABC
from typing import Any
import mcp.types as types

class ToolFactory(ABC):
    _registry = {}
    @classmethod
    def register(cls, key, tool_cls):
        cls._registry[key] = tool_cls

    @classmethod
    def create(cls, key):
        if key not in cls._registry:
            raise KeyError(f"Unknown tool factory: {key}")
        return cls._registry[key]()

