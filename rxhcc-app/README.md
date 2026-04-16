# HCendGame — AI-Powered Healthcare FWA Detection

**Live App:** [hcendgame-fwa.vercel.app](https://hcendgame-fwa.vercel.app/)  
**Repo:** [github.com/sechan9999/HCendGame](https://github.com/sechan9999/HCendGame)  
**Hackathon:** Zerve AI Hackathon · Amazon Nova Integration · April 2026

---

## The Question

> *Can an AI system not only detect healthcare fraud in real time — but autonomously improve its own detection rules without human intervention?*

Healthcare fraud costs the US **$100–300 billion annually**. Most detection is static, rule-based, and lags months behind evolving schemes. This project asks: what if the rule engine could rewrite itself?

---

## What We Found

A clinical rule engine + Amazon Nova Pro detects three FWA categories:

| Category | Example |
|----------|---------|
| **Fraud** | Keytruda billed without a cancer diagnosis |
| **Waste** | Ozempic prescribed for hypertension-only patients |
| **Abuse** | HCC upcoding to inflate CMS risk scores |

The **AutoResearch loop** (Karpathy's LOOP FOREVER methodology) ran 10 autonomous experiments:

```
F1: 0.821 → 0.829 → 0.837 → 0.843 → [discard] → 0.851 → 0.858 → 0.862 → [discard] → 0.878
```

**Best F1: 0.878** — achieved without a single human rule change after initialization.

---

## 6 Modules

| Tab | Description |
|-----|-------------|
| Single Claim | Real-time validation across 5 fraud scenarios |
| Batch Analysis | 500 synthetic claims, 15% planted anomaly rate |
| Network Graph | Kickback rings, hub providers, doctor-shopping detection |
| Temporal Analysis | Monthly billing spike detection (SVG, zero dependencies) |
| AI Investigator | Natural-language queries → structured evidence briefs |
| AutoResearch | Autonomous rule improvement loop — best F1: **0.878** |

---

## AutoResearch Loop

> *"One day, insurance fraud used to be caught by meat computers reviewing stacks of claims between coffee breaks and department meetings. That era is long gone."*  
> — adapted from @karpathy, March 2026

Each iteration:
1. Agent proposes a new detection rule via Amazon Nova Pro
2. Validates on 500 synthetic claims
3. F1 improves → **keep** the commit
4. Equal or worse → `git reset --hard HEAD~1` (**discard**)
5. Repeat

Click **Loop All** to watch it run. Click **Stop Loop** to halt.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Frontend | React 19, Vite 7, Tailwind CSS 3 |
| AI | Amazon Nova Pro (Bedrock Converse API) |
| Detection | ICD-10 / NDC / HCC clinical rule engine (inline) |
| Viz | Inline SVG — zero chart library dependencies |
| Deploy | Vercel |

---

## Why It Matters

Static fraud rules are written once and exploited immediately. An autonomous improvement loop means the system gets harder to game over time — without a data science team retooling it each quarter. The AutoResearch approach is generalizable to any claim type, payer system, or country.

---

## Quick Start

```bash
git clone https://github.com/sechan9999/HCendGame.git
cd HCendGame/rxhcc-app
npm install
npm run dev
```

Open [localhost:5173](http://localhost:5173). No API key required — runs in Rule-Based Mode by default.

Add your Bedrock credentials to `.env` to enable Nova Pro:
```
VITE_AWS_ACCESS_KEY_ID=...
VITE_AWS_SECRET_ACCESS_KEY=...
VITE_AWS_REGION=us-east-1
```

---

*Zerve AI Hackathon · Amazon Nova Integration · April 2026*
