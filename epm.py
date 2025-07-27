from typing import List, TypedDict
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("EPM")


class UserProfile(TypedDict):
    url: str
    user: str
    pwd: str


def get_base_url(url: str) -> str:
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.hostname}:{parsed_url.port}/HyperionPlanning/rest/v3"
    return base_url


@mcp.tool()
async def connect(epm_server_url: str, user: str, pwd: str) -> UserProfile | str:
    """Connect to EPM server URL.

    Args:
        epm_server_url: EPM server URL
        user: EPM user name
        pwd: EPM user password
    """
    rest_url = get_base_url(epm_server_url)

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
    epm_server_url = profile.get('url', 'epm_server_url')
    resource_url = f"{get_base_url(epm_server_url)}/applications"
    user = profile.get('user', 'user')
    pwd = profile.get('pwd', 'pwd')

    async with httpx.AsyncClient() as client:
        response = await client.get(
            resource_url,
            auth=(user, pwd)
        )

        if response.status_code == 200:
            data = response.json()

            # Extract names from the items
            application_names = [item['name'] for item in data['items']]
            return application_names
        else:
            return f'''Error: GET {resource_url}
            HTTP {response.status_code}
            {response.text}'''

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
