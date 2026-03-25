import pytest
from fastapi.testclient import TestClient
from app.main import app
from fastapi_limiter.depends import RateLimiter 

async def mock_rate_limiter(*args, **kwargs):
    return None

@pytest.fixture(scope="session", autouse=True)
def test_client():

    app.dependency_overrides[RateLimiter] = mock_rate_limiter
    
    with TestClient(app) as client:
        yield client
    
    # 3. Clean up after tests
    app.dependency_overrides.clear()
