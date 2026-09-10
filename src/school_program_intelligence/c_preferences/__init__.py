"""Input C — preference prompt → editable weights. Does not measure or search."""

from school_program_intelligence.c_preferences.interpreter import (
    PriorityInterpretation,
    interpret_priorities,
    weights_from_levels,
)
from school_program_intelligence.shared.load import load_preferences
from school_program_intelligence.shared.models import Preferences, PriorityWeights

__all__ = [
    "Preferences",
    "PriorityWeights",
    "PriorityInterpretation",
    "interpret_priorities",
    "weights_from_levels",
    "load_preferences",
]
