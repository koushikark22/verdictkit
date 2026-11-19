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


def pytest_collection_modifyitems(config, items):
    """Container-only tests run only where OS-user isolation is actually configured."""
    if os.environ.get("VK_ISOLATION") == "enforced":
        return
    skip = pytest.mark.skip(reason="requires the Linux container with VK_ISOLATION=enforced")
    for item in items:
        if "isolation" in item.keywords:
            item.add_marker(skip)
