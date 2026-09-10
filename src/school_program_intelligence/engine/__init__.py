"""Engine package — simulate A×B for one assignment; diagnose from metrics."""

from school_program_intelligence.engine.diagnosis import diagnose
from school_program_intelligence.engine.simulate import simulate

__all__ = ["simulate", "diagnose"]
