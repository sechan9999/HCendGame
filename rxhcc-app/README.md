# RxHCC FWA Detection System

**Live:** [hcendgame-fwa.vercel.app](https://hcendgame-fwa.vercel.app/)  
**Repo:** [github.com/sechan9999/HCendGame](https://github.com/sechan9999/HCendGame)

AI-powered **Healthcare Fraud, Waste & Abuse (FWA)** detection combining a clinical rule engine with **Amazon Nova Pro** and an autonomous **AutoResearch loop** modeled after [@karpathy/autoresearch](https://github.com/karpathy/autoresearch).

---

## What It Does

Healthcare fraud costs the US **$100–300 billion annually**. This system detects three categories in real time:

- **Fraud** — intentional deception (e.g., Keytruda billed without cancer diagnosis)
- **Waste** — overutilization (e.g., Ozempic prescribed for hypertension-only patients)
- **Abuse** — inconsistent practices (e.g., HCC upcoding to inflate risk scores)

---

## 6 Modules

| Tab | Description |
|-----|-------------|
| 🔍 Single Claim | Real-time validation across 5 fraud scenarios |
| 📊 Batch Analysis | 500 synthetic claims, 15% planted anomaly rate |
| 🕸️ Network Graph | Kickback rings, hub providers, doctor-shopping detection |
| 📅 Temporal Analysis | Monthly billing spike detection (SVG chart, no dependencies) |
| 🤖 AI Investigator | Natural-language queries → structured evidence briefs |
| 🧪 AutoResearch | Autonomous rule improvement loop — best F1: **0.878** |

---

## AutoResearch Loop

> *"One day, insurance fraud used to be caught by meat computers reviewing stacks of claims between coffee breaks and department meetings. That era is long gone."*  
> — adapted from @karpathy, March 2026

The **AutoResearch** tab runs Karpathy's `LOOP FOREVER` methodology on the FWA rule engine:

1. Agent proposes a new detection rule
2. Validates on 500 synthetic claims
3. If F1 improves → **keep** the commit
4. If equal or worse → `git reset --hard HEAD~1` (**discard**)
5. Repeat indefinitely

Click **Loop All** to watch it run autonomously. Click **Stop Loop** to halt.

---

## Tech Stack

React 19 · Vite 7 · Tailwind CSS 3 · Amazon Nova Pro (Bedrock) · Inline SVG · Zero test-script dependencies

---

## Quick Start

```bash
git clone https://github.com/sechan9999/HCendGame.git
cd HCendGame
npm install
npm run dev
```

Open [localhost:5173](http://localhost:5173). No API key required — runs in Rule-Based Mode by default.

---

*AWS Healthcare FWA Hackathon · Amazon Nova Integration*
