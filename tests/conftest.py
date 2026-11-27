import os

import pytest
from hypothesis import HealthCheck, settings

settings.register_profile(
    "ci",
    derandomize=True,
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.register_profile(
    "dev", max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))


_SCRUBBED = 0


def pytest_configure(config):
    """Drop unrelated credentials from this process before any test or subprocess exists."""
    global _SCRUBBED
    from envscrub import scrub_environment
    _SCRUBBED += scrub_environment(os.environ)


def pytest_report_header(config):
    return f"verdictkit: {_SCRUBBED} credential-like environment variable(s) removed from the test process"


def pytest_collection_modifyitems(config, items):
    """Container-only tests run only where OS-user isolation is actually configured."""
    if os.environ.get("VK_ISOLATION") == "enforced":
        return
    skip = pytest.mark.skip(reason="requires the Linux container with VK_ISOLATION=enforced")
    for item in items:
        if "isolation" in item.keywords:
            item.add_marker(skip)
