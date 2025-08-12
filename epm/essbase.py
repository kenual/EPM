from typing import List, TypedDict
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

# Initialize FastMCP server
mcp = FastMCP("Essbase")


class UserProfile(TypedDict):
    url: str
    user: str
    pwd: str


class Application(UserProfile):
    app: str


class Database(Application):
    db: str


def get_base_url(url: str) -> str:
    if url and url.startswith("http"):
        parsed_url = urlparse(url)
        if parsed_url.port:
            base_url = f"{parsed_url.scheme}://{parsed_url.hostname}:{parsed_url.port}/essbase/rest/v1"
        else:
            base_url = f"{parsed_url.scheme}://{parsed_url.hostname}/essbase/rest/v1"
        return base_url
    else:
        return 'Essbase URL'


@mcp.tool()
async def connect(profile: UserProfile) -> UserProfile | str:
    """Connect to Essbase server URL.

    Args:
        url: Essbase server URL
        user: Essbase user name
        pwd: Essbase user password
    """
    rest_url = f"{get_base_url(profile['url'])}/about"
    user = profile['user']
    pwd = profile['pwd']

    async with httpx.AsyncClient() as client:
        response = await client.get(
            rest_url,
            auth=(user, pwd)
        )
        content_type = response.headers.get("Content-Type", "")

        if content_type.startswith("application/json"):
            return UserProfile(url=rest_url, user=user, pwd=pwd)
        else:
            return f"HTTP GET {rest_url} Error: Unexpected Content-Type: {content_type}"


@mcp.tool()
async def list_applications(profile: UserProfile) -> List[str] | str:
    """Returns a list of applications to which the specified user is assigned.

    Args:
        profile: connected user profile
    """
    base_url = get_base_url(profile['url'])
    resource_url = f"{base_url}/applications/actions/name/ALL"
    user = profile['user']
    pwd = profile['pwd']

    async with httpx.AsyncClient() as client:
        response = await client.get(
            resource_url,
            auth=(user, pwd)
        )

        if response.status_code == 200:
            data = response.json()

            application_names = data
            return application_names
        else:
            return f'''Error: GET {resource_url}
            HTTP {response.status_code}
            {response.text}'''


@mcp.tool()
async def list_databases(app_profile: Application) -> List[str] | str:
    """List Essbase databases for the input application.

    Args:
        app_profile: Application dict with Essbase connection and application name.
    """
    base_url = get_base_url(app_profile['url'])
    app = app_profile['app']
    user = app_profile['user']
    pwd = app_profile['pwd']

    resource_url = f"{base_url}/applications/{app}/databases"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            resource_url,
            auth=(user, pwd)
        )
        if response.status_code == 200:
            data = response.json()

            database_names = [item['name'] for item in data['items']]
            return database_names
        else:
            return f'''Error: GET {resource_url}\nHTTP {response.status_code}\n{response.text}'''


@mcp.tool()
async def list_dimensions(db_profile: Database) -> List[str] | str:
    """List Essbase dimensions for the input database.

    Args:
        db_profile: Database dict with Essbase connection, application name, and database name.
    """
    base_url = get_base_url(db_profile['url'])
    app = db_profile['app']
    db = db_profile['db']
    user = db_profile['user']
    pwd = db_profile['pwd']

    resource_url = f"{base_url}/applications/{app}/databases/{db}/dimensions"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            resource_url,
            auth=(user, pwd)
        )
        if response.status_code == 200:
            data = response.json()

            dimension_names = [item['name'] for item in data.get('items', [])]
            return dimension_names
        else:
            return f'''Error: GET {resource_url}\nHTTP {response.status_code}\n{response.text}'''


class MemberRange(TypedDict):
    start_member_name: str
    end_member_name: str


class SetFunction(BaseModel):
    function_name: str


class Set(TypedDict):
    members: MemberRange | List[str] | SetFunction


@mcp.tool()
def member_range_MDX_expression(member_range: MemberRange) -> str:
    """
    Generate an MDX member range expression for Essbase.

    Args:
        member_range (MemberRange): A dictionary-like object with keys 'start_member_name' and 'end_member_name'.
            - 'start_member_name' (str): The name of the first member in the range.
            - 'end_member_name' (str): The name of the last member in the range.

    Returns:
        str: An MDX expression string representing the range between the start and end member, in the format:
            'MemberRange(start_member_name, end_member_name)'
    """
    return f"MemberRange({member_range['start_member_name']}, {member_range['end_member_name']})"


@mcp.tool()
def set_MDX_expression(set_: Set) -> str:
    """
    Generate an MDX set expression for Essbase.

    Args:
        set_ (Set): A dictionary-like object with a 'members' key.
            - 'members' can be a MemberRange, a list of member names, or a SetFunction.

    Returns:
        str: An MDX expression string representing the set.
    """
    if isinstance(set_['members'], MemberRange):
        return member_range_MDX_expression(set_['members'])
    elif isinstance(set_['members'], list):
        return "{" + ", ".join(set_['members']) + "}"
    elif isinstance(set_['members'], SetFunction):
        return f"{set_['members'].function_name}()"
    else:
        raise ValueError("Invalid members type in Set")


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
