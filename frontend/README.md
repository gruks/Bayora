# CENTINELA — Frontend Implementation Prompt

## Project Overview

Build a professional, dark-themed security audit dashboard for CENTINELA, an AI safety validation platform. The product runs adversarial red-team attacks against AI deployments and produces signed, tamper-proof PDF safety certificates for regulated industries (Healthcare, Finance, Legal).

The UI must feel like enterprise security tooling — think Datadog meets a penetration testing platform. Dark, dense, precise, credible. Not a startup landing page.

---

## Tech Stack

- **Framework**: React (functional components + hooks)
- **Styling**: Tailwind CSS only (no external component libraries)
- **Charts**: Recharts
- **Icons**: Lucide React
- **Fonts**: JetBrains Mono (monospace, for prompts/hashes/IDs) + Inter (UI text)
- **State**: `useState` + `useReducer` + `useContext` (no Redux)
- **Websocket**: Native browser WebSocket API (mock with `setInterval` for now)
- **PDF Preview**: iframe embed of a generated PDF blob (mock a sample cert)

---

## Getting Started

### Install

```bash
cd frontend
npm install
```

### Run locally

```bash
npm run dev
```

- Open the local Vite URL shown in the terminal.
- The app should start in dark mode by default.

### Build for production

```bash
npm run build
```

### Repo conventions

- Keep UI logic in `src/`, with `components/`, `contexts/`, and `hooks/` as needed.
- Use Tailwind CSS utility classes only; no external UI component libraries.
- Keep mock data in a shared `src/mock/` or `src/data/` folder.
- Use monospace styling for IDs, hashes, and prompt blocks.
- Keep the app desktop-first; support widths from `1280px` and above.

---

## Color System

- Background: `#0A0B0D` (near-black)
- Surface: `#111318` (cards, panels)
- Surface Elevated: `#1A1D24` (modals, dropdowns)
- Border: `#2A2D35` (subtle dividers)
- Border Active: `#3D4250` (focused/hover borders)
- Accent Blue: `#3B82F6` (primary actions)
- Accent Blue Dim: `#1D4ED8` (hover states)
- Severity CRITICAL: `#EF4444`
- Severity HIGH: `#F97316`
- Severity MEDIUM: `#EAB308`
- Severity LOW: `#22C55E`
- Severity PASS: `#10B981`
- Text Primary: `#F1F5F9`
- Text Secondary: `#94A3B8`
- Text Muted: `#475569`
- Hash/Mono text: `#A78BFA` (purple — makes cryptographic strings visually distinct)

---

## Application Structure

```
App
├── Sidebar (navigation + audit status)
├── Main Content Area
│   ├── Page: Configure          ← step 1
│   ├── Page: Live Audit         ← step 2 (auto-navigates here on start)
│   └── Page: Results            ← step 3 (auto-navigates here on complete)
└── Header Bar (audit ID + timer + status chip)
```

Navigation is linear. Steps are also shown as a progress indicator in the sidebar:
`[1] Configure → [2] Running → [3] Results`

Steps 2 and 3 are locked until the prior step is complete.

---

## Page 1: Configure

### Layout

- Two-column layout.
- Left column: Target Configuration.
- Right column: Audit Configuration.
- Full-width "Start Audit" CTA at the bottom.

### Left Column — Target Configuration

#### Target Model

1. **Provider** — segmented button selector:
   - Options: `OpenAI` | `Anthropic` | `Ollama` | `Custom`
   - Active: filled blue background, white text.
   - Inactive: dark surface, muted text.
   - `Ollama` hides the API Key field.
   - `Custom` shows an extra Base URL text input.

2. **Model Name** — text input with placeholder by provider:
   - OpenAI: `gpt-4o`
   - Anthropic: `claude-sonnet-4-6`
   - Ollama: `llama3`
   - Custom: `your-model-name`

3. **API Key** — password input (masked).
   - Right-side inline button: eye icon toggle visibility.
   - Label: "API Key" with a small lock icon.
   - Hidden entirely when `Ollama` is selected.

4. **Base URL** — text input.
   - Only visible when `Custom` is selected.
   - Placeholder: `https://your-endpoint.com/v1`

5. **System Prompt** — textarea (6 rows).
   - Label: "Deployment System Prompt"
   - Sublabel: "Paste the exact system prompt of the AI deployment you are auditing"
   - Monospace font.
   - Below the textarea, a static analysis chip appears as user types (after 50 chars):
     - Gray chip: "Analyzing..." (1 second delay)
     - Then 1–3 colored chips such as:
       - 🟡 `2 potential injection surfaces detected`
       - 🔵 `Role definition found`
       - 🟠 `Output constraints present`
     - These are heuristic/fake for now — trigger on keywords like `you are`, `never`, `always`, `do not`, `json`, `format`.

### Right Column — Audit Configuration

#### Audit Parameters

1. **Domain Profile** — card selector (2×2 grid of cards):
   - Healthcare | Finance | Legal | General
   - Each card: icon, domain name, one-line description:
     - Healthcare: stethoscope icon — "PHI exposure, clinical advice, drug interactions"
     - Finance: trending-up icon — "PII leakage, fraud facilitation, insider trading prompts"
     - Legal: scale icon — "Privilege breach, unauthorized legal advice, bias detection"
     - General: shield icon — "Jailbreaks, prompt injection, harmful content"
   - Selected: blue border + faint blue background tint.
   - Unselected: dark surface, subtle border.

2. **Attack Budget** — slider + numeric display.
   - Range: 10 – 500 attacks.
   - Default: 50.
   - Below slider: live stats update as slider moves:
     - `~3 min estimated` (based on 50 attacks ≈ 3 min, linear)
     - `~$0.08 estimated cost` (based on 50 attacks × $0.0016/call)

3. **Severity Threshold** — segmented selector.
   - Options: `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`
   - Sublabel: "Attacks at or above this level will count as failures"
   - Each selected option uses its severity color.

4. **Audit Metadata** — two side-by-side text inputs.
   - Organization Name (placeholder: `Acme Health Systems`).
   - Auditor Name (placeholder: `Jane Smith, CISO`).

5. **Audit ID** — read-only field, auto-generated.
   - Format: `AUDIT-2025-HC-0047`.
   - Small regenerate icon button on the right.
   - Monospace font, purple color `#A78BFA`.

### Bottom Bar — Full Width

- Left: summary of selections in muted text: `OpenAI · gpt-4o · Healthcare · 50 attacks · threshold: HIGH`
- Right: large `Start Audit →` button (blue, full rounded).
- Validation: button disabled + tooltip if required fields are empty.

---

## Page 2: Live Audit

This page is the hero experience. Maximum visual density. Split into three zones.

### Top Bar (full width)

- Left: Audit ID in monospace purple.
- Center: Status chip with animated dot.
   - `● INITIALIZING` (blue pulse)
   - `● ATTACKING` (orange pulse)
   - `● SIGNING` (purple pulse)
   - `● COMPLETE` (green, no pulse)
- Right: elapsed timer in monospace.

Status transitions (mock with `setTimeout`):
- 0s: INITIALIZING
- 3s: ATTACKING
- after attacks complete: SIGNING
- 2s later: COMPLETE → auto-navigate to Results

### Left Panel (60%) — Attack Feed

- Header: "Attack Feed" + live counter `47 / 50`
- Each attack row: `[SEVERITY BADGE] [CATEGORY TAG] [truncated prompt...] [timestamp]`
- Row hover: slightly lighter background.
- Click expands full prompt + response and verdict.
- New rows animate in from the bottom.
- Auto-scroll to latest, with a pause button if user scrolls up.

Below feed: Merkle Hash Display:
- Label: "Live Audit Chain Hash" with tooltip.
- Monospace purple hash value updates every ~3 seconds.
- Brief highlight animation on update.

### Right Panel (40%) — Live Stats

#### Score Gauge

- Large circular SVG gauge.
- Color based on score range.
- Center text: score + "SAFETY SCORE".
- Below: `12 FAILURES` and `35 PASSED` stats.

#### Category Breakdown

- Header: "Attack Categories"
- Horizontal bar chart with Recharts.
- Bars show attacks sent vs failures.
- Red for failures, emerald for passes.

---

## Page 3: Results

### Section 1: Summary Header

- Full-width card with colored left border.
- Large label: `AUDIT COMPLETE`
- Audit ID in monospace purple.
- Organization, model, domain, date.
- Overall verdict chip: `✓ CERTIFIED` or `✗ FAILED CERTIFICATION`.
- Safety score prominently displayed.

### Section 2: Three-Column Stats Row

- Attacks Executed
- Failures Detected
- Certificate Status

### Section 3: Two-Column Layout

#### Left: Attack Log

- Expandable rows like Live Audit.
- Filter bar for severity and search.
- Export CSV button.

#### Right: Certificate Panel

- Header: "Safety Certificate"
- PDF preview using iframe or styled HTML mock.
- Certificate content includes audit details, signature block, and Merkle root.
- Buttons: `↓ Download PDF`, `⎘ Copy Audit ID`.
- Verification panel with input + verify button.

---

## Global Components

### Sidebar

- Width: 240px, dark surface.
- Steps navigation with numbers and lock states.
- Bottom text: `v0.1.0 · Bayora Hackathon 2025`.
- Demo Mode toggle.

### Header Bar

- Left: page title.
- Center: Audit ID.
- Right: status chip + timer.

### Empty State

- Muted banner on Configure page.
- Sample certificate thumbnail and modal.

### Toast Notifications

- Bottom-right corner.
- Appear for audit started, complete, CSV exported, ID copied.
- Auto-dismiss after 3 seconds.

---

## Mock Data Specification

- Domain-specific categories for Healthcare, Finance, Legal, General.
- Sample attacks and prompts are realistic but non-harmful.
- Attack timing: 800ms–1200ms random interval.
- Score calculation: CRITICAL -8, HIGH -4, MEDIUM -1.
- Merkle hash is fake SHA256-style hex updated every 3 attacks.

---

## Responsive Behavior

- Minimum supported width: 1280px.
- Sidebar collapses to icon-only at 1280px.
- Full sidebar visible at 1440px+.

---

## Demo Mode

When Demo Mode is ON:

1. Auto-fill realistic values.
2. "Start Audit" becomes "Run Demo Audit →".
3. Audit runs with seeded mock data.
4. Certificate output is reproducible.

---

## Animations & Micro-interactions

- Attack row fade-up animation.
- Score gauge arc transition.
- Status chip pulse.
- Hash update flash.
- Button hover subtle brightness.

---

## What NOT to Build

- No authentication / login screens.
- No multi-user / team features.
- No real backend calls.
- No mobile layout.
- No theme toggle.
- No settings page.
- No onboarding flow.
