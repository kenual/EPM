import tomllib
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from epm.essbase import connect, get_applications, UserProfile

def get_live_test_instance():
    with open("test_config.toml", "rb") as f:
        config = tomllib.load(f)
    return dict(config["essbase_test_instance"])

@pytest_asyncio.fixture
def profile():
    return UserProfile(url="http://localhost", user="admin", pwd="welcome1")

@pytest.mark.asyncio
async def test_connect_success(profile):
    mock_response = AsyncMock()
    mock_response.headers = {"Content-Type": "application/json"}
    # Return value should not matter since it's not parsed
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        result = await connect(profile)
    # Should be a UserProfile dict
    assert isinstance(result, dict)
    assert result["user"] == "admin"
    assert result["pwd"] == "welcome1"
    assert "/about" in result["url"]

@pytest.mark.asyncio
async def test_connect_content_type_error(profile):
    mock_response = AsyncMock()
    mock_response.headers = {"Content-Type": "text/html"}
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        result = await connect(profile)
    assert isinstance(result, str)
    assert "Unexpected Content-Type" in result

@pytest.mark.asyncio
async def test_connect_httpx_exception(profile):
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=Exception("Connection error"))):
        # Exception isn't caught inside connect, so should propagate
        with pytest.raises(Exception) as excinfo:
            await connect(profile)
        assert "Connection error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_connect_live_no_mock():
    """
    Live integration test: tries to connect to a real Essbase instance with actual credentials.
    """
    live_profile = get_live_test_instance()
    result = await connect(live_profile)
    print(result)
    assert isinstance(result, dict), f"Expected UserProfile dict, got: {result}"
    assert result["user"] == "admin"
    assert result["pwd"] == "welcome1"
    assert "/about" in result["url"]

@pytest.mark.asyncio
async def test_get_applications_error_mock(profile):
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        result = await get_applications(profile)
    # Should return an error string indicating 403
    assert isinstance(result, str)
    assert "HTTP 403" in result

@pytest.mark.asyncio
async def test_get_applications_live_no_mock():
    """
    Live integration test: retrieves the list of Essbase applications for the user profile from a real Essbase instance.
    """
    from epm.essbase import get_applications

    live_profile = get_live_test_instance()
    result = await get_applications(live_profile)
    print(result)
    assert isinstance(result, list), f"Expected list payload from API, got: {type(result)}"
