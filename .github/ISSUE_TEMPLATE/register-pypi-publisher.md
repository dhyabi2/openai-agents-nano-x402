---
name: "\U0001F4E6 Register PyPI trusted publisher"
about: "One-click action for the repo owner: register the pending trusted publisher on PyPI so the release workflow can publish."
title: "[Action] Register PyPI pending trusted publisher"
labels: ["customer-action", "req1"]
assignees: ""
---

**What to do (one human step, ~2 minutes):**

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in exactly:

   | Field | Value |
   |---|---|
   | PyPI Project Name | `openai-agents-nano` |
   | Owner | `dhyabi2` |
   | Repository name | `openai-agents-nano-x402` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

4. Click "Add"

**After you do this:**

- The publish.yml workflow (triggered on any release) will push the built wheel & sdist to PyPI automatically via OIDC — no token to store, no token to rotate.
- `pip install openai-agents-nano` will work for every user.
- Close this issue and the nightly watcher will detect the package and log the adoption milestone.

**Verified preconditions (already true):**

- PyPI project name check: `/pypi/openai-agents-nano/json` → 404 (name is free)
- Workflow build test: `gh workflow run publish.yml` produced sdist+wheel successfully, only failed on `invalid-publisher` (expected — the registration is the missing step)
- GitHub Actions OIDC identity: confirmed by error message claims matching every field above