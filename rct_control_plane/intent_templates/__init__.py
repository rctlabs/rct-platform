"""
Intent Templates - Predefined execution patterns

Templates provide pre-built execution plans for common intent types.
Each template defines how to transform an IntentObject into an execution graph.
"""

from .refactor_template import RefactorTemplate
from .build_app_template import BuildAppTemplate

__all__ = [
    "RefactorTemplate",
    "BuildAppTemplate",
]
