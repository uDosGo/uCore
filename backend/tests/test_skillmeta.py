import pytest

from app.skills.base import SkillMeta


def test_skillmeta_has_requires_confirmation_default_false():
    meta = SkillMeta(id="x", name="x")
    assert hasattr(meta, "requires_confirmation")
    assert meta.requires_confirmation is False
