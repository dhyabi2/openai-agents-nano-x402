#!/usr/bin/env python3
"""Prepare the openai-agents-nano branch on the awesome-agent-first-tools fork.

Clones the fork, adds the openai-agents-nano entry to the Payments & Commerce
section of README.md, commits, and pushes the branch.
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

FORK_OWNER = "PANDeveloper001"
REPO = "awesome-agent-first-tools"
UPSTREAM = "facundofarias/awesome-agent-first-tools"
BRANCH = "add-openai-agents-nano"
WORK = "/tmp/agentfirst"

from gh_cred import token


def run(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.stdout:
        print(r.stdout[-500:])
    if r.returncode != 0:
        print("ERR:", r.stderr[-500:])
    return r


def api(url, tok, method="GET", data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("User-Agent", "rai-agent/1.0")
    req.add_header("Accept", "application/vnd.github+json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    tok = token()

    # Wait for the fork to be ready (created async)
    import time
    fork_ready = False
    for _ in range(10):
        status, data = api(
            "https://api.github.com/repos/%s/%s" % (FORK_OWNER, REPO), tok)
        if status == 200 and data.get("fork"):
            print("fork ready:", data["full_name"], "default:", data["default_branch"])
            fork_ready = True
            break
        time.sleep(3)
    if not fork_ready:
        print("fork not ready yet")
        sys.exit(1)

    clone_url = "https://github.com/%s/%s.git" % (FORK_OWNER, REPO)
    if os.path.exists(WORK):
        run(["rm", "-rf", WORK])
    run(["git", "clone", clone_url, WORK])
    os.chdir(WORK)
    run(["git", "config", "user.email", "rai@ai-agents.invalid"])

    # Create branch from current main
    run(["git", "checkout", "-b", BRANCH])

    # Read the README and add the entry in Payments & Commerce
    readme = open("README.md").read()
    anchor = "## Payments & Commerce"
    add = (
        "- [openai-agents-nano](https://github.com/PANDeveloper001/openai-agents-nano-x402) "
        "- Lets an OpenAI Agents SDK agent pay x402-priced HTTP APIs instantly and feeless in "
        "self-custodied Nano (XNO).\n"
    )
    # Insert after the section header: find first bullet after the header
    idx = readme.find(anchor)
    if idx == -1:
        print("Payments & Commerce section not found")
        sys.exit(1)
    sec_end = readme.find("\n## ", idx + len(anchor))
    if sec_end == -1:
        sec_end = len(readme)
    section = readme[idx:sec_end]
    # insert right after the section header line
    header_end = section.find("\n") + 1
    new_section = section[:header_end] + add + section[header_end:]
    new_readme = readme[:idx] + new_section + readme[sec_end:]
    open("README.md", "w").write(new_readme)

    # Show the diff
    run(["git", "diff", "--stat"])
    run(["git", "add", "README.md"])
    run(["git", "commit", "-m", "Add openai-agents-nano (Nano x402 payments for the OpenAI Agents SDK)"])

    # Push - git credentials come from .git-credentials (configured for PANDeveloper001)
    # Push URL already has the correct origin from clone
    result = run(["git", "push", "-u", "origin", BRANCH])
    print("PUSH EXIT:", result.returncode)


if __name__ == "__main__":
    main()
