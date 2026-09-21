#!/usr/bin/env python3
"""Check upstream issue replies and directory status."""
import json
import os
import urllib.request

from gh_cred import token

def api(url, tok):
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("User-Agent", "rai-agent/1.0")
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

def main():
    tok = token()
    
    # Check x402-foundation/x402 issues
    issues = api("https://api.github.com/repos/x402-foundation/x402/issues?per_page=10&state=all&sort=updated", tok)
    print("=== x402-foundation/x402 recent issues ===")
    for i in issues[:5]:
        print("  #%d [%s] %s" % (i["number"], i["state"], i["title"][:90]))
        print("    by %s, comments: %d" % (i["user"]["login"], i["comments"]))
    
    # Check e2b-dev/awesome-ai-sdks issues (one of our targets)
    print("\n=== e2b-dev/awesome-ai-sdks recent issues ===")
    issues = api("https://api.github.com/repos/e2b-dev/awesome-ai-sdks/issues?per_page=10&state=all&sort=updated", tok)
    for i in issues[:5]:
        print("  #%d [%s] %s" % (i["number"], i["state"], i["title"][:90]))
        print("    by %s, comments: %d" % (i["user"]["login"], i["comments"]))

    # Check facundofarias/awesome-agent-first-tools issues
    print("\n=== facundofarias/awesome-agent-first-tools issues ===")
    issues = api("https://api.github.com/repos/facundofarias/awesome-agent-first-tools/issues?per_page=10&state=all", tok)
    for i in issues[:5]:
        print("  #%d [%s] %s" % (i["number"], i["state"], i["title"][:90]))
        print("    by %s, comments: %d" % (i["user"]["login"], i["comments"]))
        # Check if anyone else already submitted a Nano/x402 PR
        if "nano" in i.get("title","").lower() or "x402" in i.get("title","").lower():
            print("    *** RELEVANT! ***")

    # Check the state of the awesome-agent-first-tools - does it already have open PRs for payments
    print("\n=== facundofarias/awesome-agent-first-tools PRs ===")
    prs = api("https://api.github.com/repos/facundofarias/awesome-agent-first-tools/pulls?state=open", tok)
    for p in prs[:10]:
        print("  #%d %s (by %s)" % (p["number"], p["title"][:80], p["user"]["login"]))

if __name__ == "__main__":
    main()
