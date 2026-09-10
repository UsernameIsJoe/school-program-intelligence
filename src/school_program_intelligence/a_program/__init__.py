"""Input A — program world: programs, relationships, schedule/time.

Owns educational/operational intent. Does not own floor geometry or ranking.
"""

from school_program_intelligence.a_program.inspect import show_program_world
from school_program_intelligence.shared.load import load_program_world
from school_program_intelligence.shared.models import ProgramWorld

__all__ = ["ProgramWorld", "load_program_world", "show_program_world"]
