import os
import sys
import httpx
import dulwich.porcelain
from pathlib import Path

REPO_PATH = Path(__file__).resolve().parent

def push_repository(token: str, repo_name: str = "khoj-campus-ai", private: bool = False):
    token = token.strip()
    if not token:
        print("Error: GitHub token cannot be empty.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    print("1. Verifying GitHub credentials...")
    try:
        user_res = httpx.get("https://api.github.com/user", headers=headers, timeout=15)
        if user_res.status_code != 200:
            print(f"Authentication failed: {user_res.status_code} - {user_res.text}")
            print("\nPlease make sure your GitHub Personal Access Token (PAT) has the 'repo' scope.")
            sys.exit(1)
        user_data = user_res.json()
        username = user_data["login"]
        print(f"   Authenticated as GitHub user: @{username}")
    except Exception as e:
        print(f"Network error connecting to GitHub: {e}")
        sys.exit(1)

    print(f"\n2. Checking repository 'https://github.com/{username}/{repo_name}'...")
    repo_res = httpx.get(f"https://api.github.com/repos/{username}/{repo_name}", headers=headers, timeout=15)
    
    if repo_res.status_code == 404:
        print(f"   Creating new repository '{repo_name}' on your GitHub account...")
        create_res = httpx.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json={
                "name": repo_name,
                "description": "KHOJ (खोज) — Multilingual AI Lost & Found Platform for IIT Kanpur powered by Sarvam AI",
                "private": private,
                "auto_init": False
            },
            timeout=15
        )
        if create_res.status_code not in (200, 201):
            print(f"Failed to create repository: {create_res.status_code} - {create_res.text}")
            sys.exit(1)
        print("   Repository created successfully!")
    elif repo_res.status_code == 200:
        print("   Existing repository found. Pushing latest commits...")
    else:
        print(f"Unexpected status from GitHub API: {repo_res.status_code}")

    print("\n3. Pushing code to GitHub...")
    remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    
    try:
        # Push to main branch
        dulwich.porcelain.push(str(REPO_PATH), remote_url, "refs/heads/main:refs/heads/main")
        print("\nSUCCESS! Your project has been pushed to GitHub:")
        print(f"https://github.com/{username}/{repo_name}")
    except Exception as e:
        print(f"Push error: {e}")
        # Try pushing HEAD
        try:
            dulwich.porcelain.push(str(REPO_PATH), remote_url, "HEAD:refs/heads/main")
            print(f"\nSUCCESS! Your project has been pushed to GitHub: https://github.com/{username}/{repo_name}")
        except Exception as e2:
            print(f"Fallback push also failed: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    token = os.environ.get("GITHUB_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]
    
    if not token:
        print("Enter your GitHub Personal Access Token (classic token with 'repo' scope or fine-grained token):")
        token = input("GitHub Token: ").strip()

    repo_name = sys.argv[2] if len(sys.argv) > 2 else "khoj-campus-ai"
    push_repository(token, repo_name)
