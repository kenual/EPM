from typing import List, TypedDict
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Essbase")


class UserProfile(TypedDict):
    url: str
    user: str = "admin"
    pwd: str = "welcome1"


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
async def get_applications(profile: UserProfile) -> List[str] | str:
    """Returns a list of applications to which the specified user is assigned.

    Args:
        profile: connected user profile
    """
    resource_url = f"{get_base_url(profile['url'])}/applications/actions/name/ALL"
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

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
