from __future__ import annotations
from typing import Any
from pydantic import BaseModel

class SkillParam(BaseModel):
    name: str; type: str = "string"; description: str = ""
    required: bool = False; default: Any = None

class SkillMeta(BaseModel):
    id: str; name: str; description: str = ""
    category: str = "general"; params: list[SkillParam] = []
    timeout: int = 60
    requires_confirmation: bool = False

class BaseSkill:
    meta: SkillMeta
    async def run(self, **kwargs) -> dict:
        raise NotImplementedError
    def validate(self, **kwargs) -> list[str]:
        return [f"Missing: {p.name}" for p in self.meta.params if p.required and p.name not in kwargs]
