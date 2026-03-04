# Brand DNA — MediaAuditOrganizer Landing

**Version:** 1.0  
**Created:** 2026-03-03  
**Status:** Launch-Ready

---

## Brand Identity

**Working Name:** `AXIOMATIC` (placeholder — swappable in one variable)  
**Tagline:** "Local-First Media Organization for Professionals"  
**Positioning:** Industrial-grade tool for photographers/videographers with chaotic media libraries

**Core Message:** We never see your data. Everything runs locally on your machine.

---

## Design System

### Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--obsidian` | `#1a1a1a` | Primary background, deep surfaces |
| `--slate` | `#4a5568` | Secondary surfaces, borders, muted text |
| `--cyber-lime` | `#a3e635` | Primary accent, CTAs, success states |
| `--slate-light` | `#64748b` | Secondary text, icons |
| `--white` | `#ffffff` | Primary text |
| `--white-dim` | `#e2e8f0` | Secondary text, captions |

### CSS Variables (Tailwind Config)

```css
:root {
  --obsidian: #1a1a1a;
  --slate: #4a5568;
  --slate-light: #64748b;
  --cyber-lime: #a3e635;
  --cyber-lime-hover: #84cc16;
  --cyber-lime-active: #65a30d;
  --white: #ffffff;
  --white-dim: #e2e8f0;
  
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
}
```

### Tailwind Extension

```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      obsidian: '#1a1a1a',
      slate: {
        DEFAULT: '#4a5568',
        light: '#64748b',
      },
      'cyber-lime': {
        DEFAULT: '#a3e635',
        hover: '#84cc16',
        active: '#65a30d',
      },
    },
    fontFamily: {
      mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      sans: ['Inter', 'system-ui', 'sans-serif'],
    },
  },
}
```

---

## Button States

### Primary CTA (Cyber-Lime)

```css
.btn-primary {
  background: var(--cyber-lime);
  color: var(--obsidian);
  font-weight: 600;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary:hover {
  background: var(--cyber-lime-hover);
  transform: translateY(-1px);
}

.btn-primary:active {
  background: var(--cyber-lime-active);
  transform: translateY(0);
}

.btn-primary:disabled {
  background: var(--slate);
  color: var(--slate-light);
  cursor: not-allowed;
  transform: none;
}
```

### Secondary (Outline)

```css
.btn-secondary {
  background: transparent;
  color: var(--white);
  font-weight: 500;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  border: 1px solid var(--slate);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-secondary:hover {
  border-color: var(--cyber-lime);
  color: var(--cyber-lime);
}

.btn-secondary:disabled {
  border-color: var(--slate);
  color: var(--slate-light);
  cursor: not-allowed;
}
```

---

## Pro-Density Layout Rules

**Philosophy:** Information-dense, no fluff. Professionals scan, don't read.

### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` | Tight inline spacing |
| `--space-sm` | `8px` | Component internal spacing |
| `--space-md` | `16px` | Standard gap |
| `--space-lg` | `24px` | Section spacing |
| `--space-xl` | `48px` | Major section breaks |
| `--space-2xl` | `96px` | Page-level spacing |

### Layout Principles

1. **No hero images without purpose** — Every visual must communicate function
2. **Monospace for technical data** — File counts, paths, hashes, timestamps
3. **Dense but breathable** — Tight line-height (1.4), generous section breaks
4. **Left-aligned content** — Professionals scan left-to-right
5. **Visible structure** — Borders, dividers, clear hierarchy

### Component Density

```css
.pro-density {
  line-height: 1.4;
  letter-spacing: -0.01em;
}

.pro-density h1 {
  font-size: 2.5rem;
  line-height: 1.1;
  margin-bottom: var(--space-md);
}

.pro-density h2 {
  font-size: 1.5rem;
  line-height: 1.2;
  margin-bottom: var(--space-sm);
}

.pro-density p {
  font-size: 1rem;
  line-height: 1.5;
  margin-bottom: var(--space-md);
}

.pro-density .mono {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  background: rgba(74, 85, 104, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
}
```

---

## Typography Scale

### Headings

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| `h1` | `2.5rem` (40px) | 700 | 1.1 | Hero headline |
| `h2` | `1.5rem` (24px) | 600 | 1.2 | Section headers |
| `h3` | `1.125rem` (18px) | 600 | 1.3 | Subsections |
| `h4` | `1rem` (16px) | 600 | 1.4 | Card titles |

### Body

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| `body-lg` | `1.125rem` (18px) | 400 | 1.5 | Lead paragraphs |
| `body` | `1rem` (16px) | 400 | 1.5 | Standard text |
| `body-sm` | `0.875rem` (14px) | 400 | 1.4 | Captions, labels |
| `mono` | `0.875rem` (14px) | 400 | 1.4 | Technical data |

### Font Stack

```css
font-family: 'Inter', system-ui, -apple-system, sans-serif; /* Body */
font-family: 'JetBrains Mono', 'Fira Code', monospace; /* Technical data */
```

---

## Visual Language

### Aesthetic: "Industrial-Grade Professional Tool"

**NOT:** Consumer app, playful, rounded, gradient-heavy  
**IS:** Precise, functional, high-contrast, monospace accents

### Design Tokens

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);

--border-subtle: 1px solid rgba(74, 85, 104, 0.3);
--border-default: 1px solid rgba(74, 85, 104, 0.5);
--border-accent: 1px solid rgba(163, 230, 53, 0.5);
```

### Animation Principles

1. **Fast and purposeful** — 150-250ms transitions
2. **No bouncy easing** — Linear or ease-out only
3. **Hover states are subtle** — Color shift + 1px transform
4. **Loading states are honest** — Progress bars, spinners, no fake speed

```css
.transition-fast {
  transition: all 0.15s ease;
}

.transition-medium {
  transition: all 0.25s ease;
}

.ease-out {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## Messaging Framework

### Headline Formula

```
[Pain of Chaos] → [Axiomatic Proof of Order]
```

**Examples:**
- "Your Drive is Chaos. We Build Order."
- "10,000 Files. 0 Duplicates. 1 Source of Truth."
- "Stop Managing Media. Start Creating."

### Subhead Formula

```
[Local-First Emphasis] + [Professional Credibility]
```

**Examples:**
- "Everything runs on your machine. We never see your data."
- "Built for photographers who shoot 100GB/week."
- "GPU-accelerated. Local-first. Professional-grade."

### CTA Formula

```
[Action] + [Exclusivity] + [Low Commitment]
```

**Examples:**
- "Join Alpha Waitlist"
- "Get Early Access"
- "Reserve Your Spot"

---

## Component Library

### Waitlist Form

```tsx
// Props
interface WaitlistFormProps {
  apiEndpoint: string; // Mock: /api/waitlist
  onSuccess: () => void;
  onError: (error: string) => void;
}

// States
- idle: Email input + CTA button
- loading: Disabled input + spinner
- success: Checkmark + "You're on the list"
- error: Red border + error message

// Validation
- Email format check
- Duplicate submission prevention
- Privacy reassurance copy
```

### Engine Preview (12 Subagents)

```tsx
// Visual: Grid of 12 cards
// Each card shows:
- SA-XX ID
- Subagent name
- Status indicator (idle/processing/complete)
- One-line purpose

// Animation: Staggered fade-in, left-to-right
// Data source: SUBAGENT_ORCHESTRATION_PLAN.md
```

### Roadmap Timeline

```tsx
// 3-phase horizontal timeline
// Phases:
1. Local Alpha (Now) — Core audit, dedupe, organize
2. GPU Acceleration (Q2 2026) — 10x faster processing
3. Team/Studio Sync (Q4 2026) — Multi-user workflows

// Visual: Connected nodes with progress indicators
```

---

## Name Swap System

**Current:** `AXIOMATIC` (placeholder)  
**Swap Location:** Single variable in config

```ts
// config/brand.ts
export const BRAND_NAME = 'AXIOMATIC'; // CHANGE THIS ONE VARIABLE
export const BRAND_TAGLINE = 'Local-First Media Organization';
```

**All occurrences reference this variable:**
- Page titles
- Hero headlines
- Footer
- Meta tags
- Email templates

---

## Competitive Positioning

| Feature | MediaAuditOrganizer | Lightroom | Google Photos |
|---------|---------------------|-----------|---------------|
| Local-first | ✅ Yes | ⚠️ Partial | ❌ Cloud-only |
| No upload | ✅ Yes | ❌ Syncs | ❌ Uploads all |
| GPU-accelerated | ✅ Yes | ✅ Yes | ❌ N/A |
| Duplicate detection | ✅ Hash + perceptual | ⚠️ Basic | ⚠️ Basic |
| Professional workflow | ✅ 12 subagents | ✅ Yes | ❌ Consumer |
| Price | One-time | Subscription | Subscription |

**Key Differentiator:** LOCAL-FIRST (we never see your data)

---

## Accessibility

- **Contrast:** WCAG AA minimum (4.5:1 for text)
- **Focus states:** Visible outlines on all interactive elements
- **Keyboard navigation:** Full tab support
- **Screen readers:** ARIA labels on all components
- **Motion:** Respect `prefers-reduced-motion`

---

## File Structure

```
gui/landing/
├── BRAND_DNA.md (this file)
├── index.html (or page.tsx for Next.js)
├── components/
│   ├── Hero.tsx
│   ├── EnginePreview.tsx
│   ├── Roadmap.tsx
│   ├── WaitlistForm.tsx
│   └── Footer.tsx
├── styles/
│   └── landing.css
└── api/
    └── waitlist.ts (mock endpoint)
```

---

## Next Actions

1. ✅ Brand DNA documented
2. ⏳ Build Hero component
3. ⏳ Build EnginePreview component
4. ⏳ Build Roadmap component
5. ⏳ Build WaitlistForm component
6. ⏳ Assemble landing page
7. ⏳ Write deployment instructions

---

*This document is the single source of truth for landing page design. All components must follow these specifications.*
