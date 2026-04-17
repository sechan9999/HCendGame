# Decision: Vercel rootDirectory Fix

**Tags**: vercel, deployment, python, rootdirectory, ci

## Problem

GitHub auto-deploy to Vercel failed with exit code 254. Vercel detected Python files at repo root (`streamlit_app.py`, `requirements.txt`) and auto-installed Python dependencies including `sagemaker`, `torch` (~2 GB). Build timed out.

Error: `tcgyver-2267. There was an error deploying hcendgame-fwa to the production environment.`

## Root Cause

Vercel's auto-detection scanned the repo root, found Python files, and ran pip install on `requirements.txt`. The repo root contained mixed Python/JS files because early development used a Python Streamlit prototype before pivoting to React.

## Fix

Set `rootDirectory=rxhcc-app` via Vercel API PATCH:

```bash
curl -X PATCH "https://api.vercel.com/v9/projects/PROJECT_ID" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rootDirectory": "rxhcc-app"}'
```

Then deploy from the **parent** directory (`fwa_deploy_repo/`), not from inside `rxhcc-app/`:
```bash
cd fwa_deploy_repo
vercel --prod
```

## Path Doubling Trap

If you set `rootDirectory=rxhcc-app` AND deploy from inside `rxhcc-app/`, Vercel sees `rxhcc-app/rxhcc-app` — double nesting. Always deploy from the parent.

## Result

Build time: ~8 min (with Python) → ~2 min (React only).

## Long-term Fix

The repo cleanup (`_archive/` folder) moved all Python files out of root, so this issue won't recur even if `rootDirectory` is ever unset.

**Related**: [[rxhcc-app]]
