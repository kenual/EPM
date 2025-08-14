import tomllib
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, Mock
from epm.essbase import connect, list_applications, list_databases, Application, UserProfile


def get_live_test_instance():
    with open("test/test_config.toml", "rb") as f:
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
    assert isinstance(
        result, dict), f"Expected UserProfile dict, got: {result}"
    assert result["user"] == "admin"
    assert result["pwd"] == "welcome1"
    assert "/about" in result["url"]


@pytest.mark.asyncio
async def test_list_applications_success(profile):
    # Mock the JSON response data
    mock_json_data = ["DemoApp1", "DemoApp2"]

    # Create a mock response
    mock_response = Mock()  # Use Mock, not AsyncMock for the response object
    mock_response.status_code = 200
    # json() is sync, not async
    mock_response.json = Mock(return_value=mock_json_data)

    # Mock the async client
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    # Patch the AsyncClient context manager
    with patch("httpx.AsyncClient") as mock_async_client:
        mock_async_client.return_value.__aenter__.return_value = mock_client

        result = await list_applications(profile)

    assert isinstance(result, list)
    assert result == ["DemoApp1", "DemoApp2"]


@pytest.mark.asyncio
async def test_list_applications_error_mock(profile):
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        result = await list_applications(profile)
    # Should return an error string indicating 403
    assert isinstance(result, str)
    assert "HTTP 403" in result


@pytest.mark.asyncio
async def test_list_applications_live_no_mock():
    """
    Live integration test: retrieves the list of Essbase applications for the user profile from a real Essbase instance.
    """
    live_profile = get_live_test_instance()
    result = await list_applications(live_profile)
    print(result)
    assert isinstance(
        result, list), f"Expected list payload from API, got: {type(result)}"


@pytest.mark.asyncio
async def test_list_databases_live_no_mock():
    """
    Live integration test: lists databases for the first application on a real Essbase instance.
    """
    live_profile = get_live_test_instance()
    app_list = await list_applications(live_profile)
    assert isinstance(
        app_list, list), f"Expected application list, got: {type(app_list)}"
    assert len(app_list) > 0, "No applications found to test database listing"

    first_app_name = app_list[0]
    # Build Application dict (subclass of UserProfile with 'app')
    app_profile = Application(
        url=live_profile["url"],
        user=live_profile["user"],
        pwd=live_profile["pwd"],
        app=first_app_name
    )
    result = await list_databases(app_profile)
    print(f"Databases for app '{first_app_name}':", result)
    assert isinstance(
        result, list), f"Expected list of databases, got: {type(result)}"
    assert len(
        result) > 0, f"No databases returned for application '{first_app_name}'"


@pytest.mark.asyncio
async def test_list_dimensions_live_no_mock():
    """
    Live integration test: lists dimensions for the first database of the first application on a real Essbase instance.
    """
    from epm.essbase import list_dimensions, Database

    live_profile = get_live_test_instance()
    app_list = await list_applications(live_profile)
    assert isinstance(
        app_list, list), f"Expected application list, got: {type(app_list)}"
    assert len(app_list) > 0, "No applications found to test dimension listing"

    first_app_name = app_list[0]
    app_profile = Application(
        url=live_profile["url"],
        user=live_profile["user"],
        pwd=live_profile["pwd"],
        app=first_app_name
    )
    db_list = await list_databases(app_profile)
    assert isinstance(
        db_list, list), f"Expected list of databases, got: {type(db_list)}"
    assert len(
        db_list) > 0, f"No databases returned for application '{first_app_name}'"

    first_db_name = db_list[0]
    db_profile = Database(
        url=live_profile["url"],
        user=live_profile["user"],
        pwd=live_profile["pwd"],
        app=first_app_name,
        db=first_db_name
    )
    dim_result = await list_dimensions(db_profile)
    print(
        f"Dimensions for db '{first_db_name}' in app '{first_app_name}':", dim_result)
    assert isinstance(
        dim_result, list), f"Expected list of dimensions, got: {type(dim_result)}"
    assert len(
        dim_result) > 0, f"No dimensions returned for database '{first_db_name}' in application '{first_app_name}'"


@pytest.mark.asyncio
async def test_search_members_live_no_mock():
    """
    Live integration test: searches for a member in the first database of the first application on a real Essbase instance.
    """
    from epm.essbase import search_members, Database, Member

    live_profile = get_live_test_instance()
    app_list = await list_applications(live_profile)
    assert isinstance(
        app_list, list), f"Expected application list, got: {type(app_list)}"
    assert len(app_list) > 0, "No applications found to test member search"

    if 'Sample' in app_list:
        test_app_name = 'Sample'
        test_db_name = 'Basic'
        db_profile = Database(
            url=live_profile["url"],
            user=live_profile["user"],
            pwd=live_profile["pwd"],
            app=test_app_name,
            db=test_db_name
        )

        search_entities = ["Market", "Jan", "California", "100", "Sales"]
        search_result = await search_members(db_profile, search_entities)
        print(
            f"Search results for {search_entities} in db '{test_db_name}' of app '{test_app_name}':", search_result)
        assert isinstance(
            search_result, dict), f"Expected dict result, got: {type(search_result)}"
        # Ensure that every entity searched is a key, and its value is a dict (Member) or not None
        for entity in search_entities:
            assert entity in search_result, f"Key '{entity}' not found in search_result"
            member = search_result[entity]
            assert member is not None, f"No member found for query '{entity}' in database '{test_db_name}'"
            assert isinstance(member, dict), f"Returned value for '{entity}' is not a dict: {type(member)}"
            for k in ("dimension", "name", "unique_name"):
                assert k in member, f"Key '{k}' missing from returned member for '{entity}': {member}"
                assert isinstance(member[k], str), f"Value for key '{k}' in member for '{entity}' is not a string: {type(member[k])}"
