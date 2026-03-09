"""
Utilities package for EVOLV.

:requirement: URS-15.0 - Utility functions for PDF/Word generation
              and enterprise audit logging.
"""
from utils.audit_decorator import audit_log

__all__ = ["audit_log"]
