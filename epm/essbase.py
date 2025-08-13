from epm.mdx import (
    MemberRange, SetFunction, Set,
    member_range_MDX_expression as _member_range_MDX_expression,
    set_MDX_expression as _set_MDX_expression,
)
from typing import Dict, List, TypedDict
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


class Member(TypedDict):
    dimension: str
    name: str
    unique_name: str


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


@mcp.tool()
async def search_members(db_profile: Database, entity_names: List[str]) -> Dict[str, List[Member]] | str:
    """Search for members in the specified database.

    Args:
        db_profile: Database dict with Essbase connection, application name, and database name.
        entity_names: List of member names to search for.
    """
    base_url = get_base_url(db_profile['url'])
    app = db_profile['app']
    db = db_profile['db']
    user = db_profile['user']
    pwd = db_profile['pwd']

    resource_url = f"{base_url}/outline/{app}/{db}?links=none&fields=MEMBERSANDALIASES&limit=5&matchWholeWord=true"
    result_dict = {}
    for entity_name in entity_names:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{resource_url}&keyword={entity_name}",
                auth=(user, pwd),
                headers={"Accept": "application/json"}
            )
            if response.status_code != 200:
                result_dict[entity_name] = None
                continue
            data = response.json()
            items = data.get('items', [])
            if len(items) == 0:
                result_dict[entity_name] = None
                continue

            if len(items) == 1:
                # Only one item found, use it directly
                item = items[0]
            else:
                # Multiple items found, apply selection logic
                # 1. Match uniqueName == entity_name
                item = next((itm for itm in items if itm.get('uniqueName') == entity_name), None)
                if not item:
                    # 2. Match name == entity_name
                    item = next((itm for itm in items if itm.get('name') == entity_name), None)
                if not item:
                    # 3. Fallback to first item
                    item = items[0]

            member_name = item.get('name', '')
            member = Member(
                dimension=item.get('dimensionName', member_name),
                name=member_name,
                unique_name=item['uniqueName']
            )
            result_dict[entity_name] = member

    return result_dict

member_range_MDX_expression = mcp.tool()(_member_range_MDX_expression)
set_MDX_expression = mcp.tool()(_set_MDX_expression)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
