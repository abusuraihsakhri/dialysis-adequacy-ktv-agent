"""
Shared test configuration for Dialysis Adequacy Ktv Agent test suite.
"""
import os

# Set a deterministic audit key for tests to suppress ephemeral key warning
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-for-test-suite")
