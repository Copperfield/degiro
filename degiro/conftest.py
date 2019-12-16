import os

import pytest


@pytest.fixture
def credentials():
    os.environ['username'] = "user_name"
    os.environ['password'] = 'passd'
