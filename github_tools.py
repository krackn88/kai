import requests
from typing import List, Dict, Any, Optional
from anthropic_agent.tools import Tool, ToolParameter

class GitHubAPI:
    """GitHub API wrapper with authentication."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None):
        """Make a GET request to the GitHub API."""
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

def get_github_tools() -> List[Tool]:
    """Get tools for GitHub API integration."""
    github_api = GitHubAPI()
    
    async def get_repo_info(owner: str, repo: str) -> Dict[str, Any]:
        """Get information about a GitHub repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        return github_api.get(url)
    
    async def get_file_contents(owner: str, repo: str, path: str, ref: Optional[str] = None) -> Dict[str, Any]:
        """Get the contents of a file in a GitHub repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else None
        return github_api.get(url, params)
    
    async def search_code(query: str) -> Dict[str, Any]:
        """Search code in GitHub repositories."""
        url = "https://api.github.com/search/code"
        params = {"q": query}
        return github_api.get(url, params)
    
    async def list_issues(owner: str, repo: str, state: Optional[str] = "open") -> Dict[str, Any]:
        """List issues in a GitHub repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        params = {"state": state}
        return github_api.get(url, params)
    
    async def list_pull_requests(owner: str, repo: str, state: Optional[str] = "open") -> Dict[str, Any]:
        """List pull requests in a GitHub repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        params = {"state": state}
        return github_api.get(url, params)
    
    # Define tools
    return [
        Tool(
            name="get_repo_info",
            description="Get information about a GitHub repository",
            parameters=[
                ToolParameter(name="owner", type="string", description="Repository owner"),
                ToolParameter(name="repo", type="string", description="Repository name")
            ],
            function=get_repo_info,
            category="github"
        ),
        
        Tool(
            name="get_file_contents",
            description="Get the contents of a file in a GitHub repository",
            parameters=[
                ToolParameter(name="owner", type="string", description="Repository owner"),
                ToolParameter(name="repo", type="string", description="Repository name"),
                ToolParameter(name="path", type="string", description="File path"),
                ToolParameter(name="ref", type="string", description="Branch or tag name", required=False)
            ],
            function=get_file_contents,
            category="github"
        ),
        
        Tool(
            name="search_code",
            description="Search code in GitHub repositories",
            parameters=[
                ToolParameter(name="query", type="string", description="Search query")
            ],
            function=search_code,
            category="github"
        ),
        
        Tool(
            name="list_issues",
            description="List issues in a GitHub repository",
            parameters=[
                ToolParameter(name="owner", type="string", description="Repository owner"),
                ToolParameter(name="repo", type="string", description="Repository name"),
                ToolParameter(name="state", type="string", description="Issue state (open, closed, all)", required=False, default="open")
            ],
            function=list_issues,
            category="github"
        ),
        
        Tool(
            name="list_pull_requests",
            description="List pull requests in a GitHub repository",
            parameters=[
                ToolParameter(name="owner", type="string", description="Repository owner"),
                ToolParameter(name="repo", type="string", description="Repository name"),
                ToolParameter(name="state", type="string", description="Pull request state (open, closed, all)", required=False, default="open")
            ],
            function=list_pull_requests,
            category="github"
        )
    ]