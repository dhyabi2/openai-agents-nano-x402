import urllib.request, json, time, sys

from gh_cred import token as gh_token
tok = gh_token()

targets = [
    ('xpaysh', 'awesome-x402', 'add-openai-agents-nano-v2'),
    ('x402-foundation', 'x402', 'docs/list-openai-agents-nano-v10'),
    ('frankxai', 'awesome-payment-agent-skills', 'add-openai-agents-nano'),
    ('Haustorium12', 'gold-402', 'add-openai-agents-nano-v5'),
    ('assafbar2', 'agentswitchboard.dev', 'add-openai-agents-nano-v5'),
]

# Check 404-ed branches: did upstream move?
missing = [
    ('xpaysh', 'awesome-x402', 'add-openai-agents-nano'),
    ('Scottcjn', 'awesome-agents', 'add-openai-agents-nano'),
    ('michielpost', 'x402-dev', 'add-openai-agents-nano'),
    ('x402-foundation', 'x402', 'specs/nano-spec-v1'),
]

print("=== Clean branches ===")
for owner, repo, branch in targets:
    url = f'https://api.github.com/repos/{owner}/{repo}/compare/main...PANDeveloper001:{branch}'
    try:
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'User-Agent': 'rai-agent'})
        r = urllib.request.urlopen(req, timeout=15)
        d = json.loads(r.read().decode())
        print(f'{owner}/{repo} {branch}: {d["status"]} ahead {d["ahead_by"]} behind {d["behind_by"]}')
    except urllib.error.HTTPError as e:
        print(f'{owner}/{repo} {branch}: {e.code}')
    time.sleep(0.3)

print("\n=== 404-ed branches: checking fork ===")
for owner, repo, branch in missing:
    # Check if the fork branch exists
    for check_url in [
        f'https://github.com/PANDeveloper001/{repo}/blob/{branch}/README.md',
        f'https://github.com/{owner}/{repo}',
    ]:
        try:
            req = urllib.request.Request(check_url, headers={'User-Agent': 'curl/8.5.0'})
            r = urllib.request.urlopen(req, timeout=10)
            print(f'{check_url[:80]}: {r.status}')
        except Exception as e:
            print(f'{check_url[:80]}: FAILED ({e})')
    print('---')
    time.sleep(0.3)

# Check AgentMRR homepage
print("\n=== AgentMRR ===")
try:
    req = urllib.request.Request('https://agentmrr.ai/', headers={'User-Agent': 'Mozilla/5.0'})
    r = urllib.request.urlopen(req, timeout=15)
    body = r.read().decode('utf-8', errors='replace')
    mentions = body.lower().count('openai-agents-nano')
    print(f'Homepage mentions: {mentions}')
except Exception as e:
    print(f'FAILED: {e}')

# Check if nanodir still lists us
print("\n=== nanodirectory ===")
for url in ['https://nanodirectory.info', 'https://www.nanodirectory.info']:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.5.0'})
        r = urllib.request.urlopen(req, timeout=10)
        body = r.read().decode('utf-8', errors='replace')
        found = 'openai-agents-nano' in body.lower()
        print(f'{url}: {r.status} - {"FOUND" if found else "not found"}')
    except Exception as e:
        print(f'{url}: FAILED ({e})')

print("\n=== Directory re-checks ===")
dirs = [
    ('agents.net', 'https://agents.net/directory'),
    ('bestaiagents.org', 'https://bestaiagents.org/agents'),
    ('theagentrank.com', 'https://theagentrank.com'),
    ('x402info.com/ecosystem', 'https://x402info.com/ecosystem'),
    ('4agent.dev', 'https://4agent.dev/agents'),
    ('aiagentcensus.com', 'https://aiagentcensus.com'),
    ('aiagents.directory', 'https://aiagents.directory'),
]
for name, url in dirs:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=10)
        body = r.read().decode('utf-8', errors='replace')
        found = 'openai-agents-nano' in body.lower()
        print(f'{name}: {r.status} - {"FOUND" if found else "not found"}')
    except Exception as e:
        print(f'{name}: FAILED ({e})')

# GitHub release downloads
print("\n=== Release downloads ===")
try:
    req = urllib.request.Request('https://api.github.com/repos/PANDeveloper001/openai-agents-nano-x402/releases', 
                                 headers={'Authorization': f'Bearer {tok}', 'User-Agent': 'rai-agent'})
    r = urllib.request.urlopen(req, timeout=10)
    releases = json.loads(r.read().decode())
    for rel in releases:
        print(f'{rel["tag_name"]}: {rel.get("assets", [])}')
        for asset in rel.get('assets', []):
            print(f'  {asset["name"]}: {asset["download_count"]} downloads')
except Exception as e:
    print(f'FAILED: {e}')