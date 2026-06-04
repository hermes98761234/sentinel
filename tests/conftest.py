import pytest

VALID_API_KEY = "test-api-key-12345"


@pytest.fixture
def valid_api_key():
    return VALID_API_KEY
