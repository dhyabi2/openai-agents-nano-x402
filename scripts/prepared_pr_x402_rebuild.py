#!/usr/bin/env python3
"""Rebuild x402-foundation/x402 prepared branches against latest upstream HEAD.

Cherry-picks our commits from old -vN branches onto upstream HEAD and pushes as -vN+1.
"""
import json, subprocess, sys, os

X402_DIR = "/root/work/x402"
OUR_REPO = "PANDeveloper001/x402"

from gh_cred import token as gh_token
TOKEN = gh_token()

def gh_api(url):
    r = subprocess.run(["curl", "-sL", "-H", f"Authorization: Bearer {TOKEN}",
                        "-H", "Accept: application/vnd.github+json", url],
                       capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def git(cmd, cwd=X402_DIR):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        print(f"  GIT ERROR: {' '.join(cmd)}: {r.stderr.strip()[:200]}")
    return r.stdout.strip()

# Branches to rebuild
branches = [
    ("docs/list-openai-agents-nano-v8", "docs/list-openai-agents-nano-v9",
     "docs/list-openai-agents-nano.mdx"),
    ("specs/exact-nano-mainnet-v2", "specs/exact-nano-mainnet-v3",
     "specs/schemes/exact-nano-mainnet.md"),
]

for old_branch, new_branch, our_file in branches:
    print(f"\n=== {old_branch} -> {new_branch} ===")

    # Get old branch info from our fork
    info = gh_api(f"https://api.github.com/repos/{OUR_REPO}/branches/{old_branch}")
    if "commit" not in info:
        print(f"  ERROR: branch {old_branch} not found: {info.get('message','')}")
        continue
    old_sha = info["commit"]["sha"]
    print(f"  Old SHA: {old_sha[:12]}")

    # Get the old branch's commits (just ours, not upstream's)
    cmp = gh_api(f"https://api.github.com/repos/{OUR_REPO}/compare/HEAD...{old_branch}?per_page=10")
    if "_http_error" in cmp:
        # Try comparing to the fork's default branch
        cmp = gh_api(f"https://api.github.com/repos/x402-foundation/x402/compare/main...{OUR_REPO}:{old_branch}?per_page=10")
    if "_http_error" in cmp:
        print(f"  Compare API error: {cmp['_http_error']} {cmp.get('_body','')[:100]}")
        continue

    commits = cmp.get("commits", [])
    our_commits = [c for c in commits if c.get("author",{}).get("login","") != "web-flow"
                   and c.get("commit",{}).get("author",{}).get("email","") != "41898282+github-actions[bot]@users.noreply.github.com"]
    # Actually all commits in the compare are what we added — just cherry-pick them all
    print(f"  Commits to cherry-pick: {len(commits)}")
    for c in commits:
        print(f"    {c['sha'][:8]} {c['commit']['message'][:70]}")

    # Create new branch from upstream HEAD
    git(["git", "branch", "-D", new_branch], cwd=X402_DIR)
    r = git(["git", "checkout", "-b", new_branch, "origin/main"])
    print(f"  Created {new_branch} from origin/main")

    # Cherry-pick our commits
    for c in commits:
        sha = c["sha"]
        out = git(["git", "cherry-pick", sha])
        if "Cherry-pick failed" in out or "conflict" in out.lower():
            # Try with --keep-empty and skip
            git(["git", "cherry-pick", "--abort"])
            # Manual approach: save the file from old branch
            print(f"  Cherry-pick conflict on {sha[:8]}, trying manual file copy...")
            # Fetch our file from our fork
            file_r = subprocess.run(
                ["curl", "-sL", "-H", f"Authorization: Bearer {TOKEN}",
                 f"https://raw.githubusercontent.com/{OUR_REPO}/{old_branch}/{our_file}"],
                capture_output=True, text=True, timeout=15)
            if file_r.returncode == 0 and len(file_r.stdout) > 10:
                os.makedirs(os.path.dirname(os.path.join(X402_DIR, our_file)), exist_ok=True)
                with open(os.path.join(X402_DIR, our_file), "w") as f:
                    f.write(file_r.stdout)
                # Need the parent dir for specs
                msg = c["commit"]["message"]
                git(["git", "add", our_file])
                env = os.environ.copy()
                env["GIT_AUTHOR_NAME"] = c["commit"]["author"]["name"]
                env["GIT_AUTHOR_EMAIL"] = c["commit"]["author"]["email"]
                env["GIT_COMMITTER_DATE"] = c["commit"]["committer"]["date"]
                git(["git", "commit", "-m", msg, "--author",
                     f'{c["commit"]["author"]["name"]} <{c["commit"]["author"]["email"]}>'])
                print(f"  Manually applied {sha[:8]}: {msg[:50]}")
            else:
                print(f"  Could not fetch file: {file_r.stderr[:100]}")
                continue
        else:
            print(f"  Cherry-picked {sha[:8]}")

    # Push new branch
    push_r = subprocess.run(["git", "push", "origin", new_branch], capture_output=True, text=True, cwd=X402_DIR)
    if push_r.returncode == 0:
        print(f"  Pushed {new_branch}")
    else:
        print(f"  Push error: {push_r.stderr[:200]}")

    # Verify
    info2 = gh_api(f"https://api.github.com/repos/{OUR_REPO}/branches/{new_branch}")
    if "commit" in info2:
        print(f"  Verified: {new_branch} @ {info2['commit']['sha'][:12]}")

# Cleanup: go back to main
git(["git", "checkout", "main"])
print("\nDone rebuilding x402 branches.")