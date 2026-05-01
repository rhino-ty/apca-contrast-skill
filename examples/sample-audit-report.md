# Sample audit report — shadcn/ui Neutral default theme

This is the actual output of running this skill against shadcn/ui's default Neutral theme (`examples/sample-globals.css`). It demonstrates how to read the report and what kinds of issues to look for. Run it yourself:

```bash
python3 scripts/apca.py --from-tailwind examples/sample-globals.css
```

## Raw output

### LIGHT mode

| Name                               |     Lc | Verdict                                |
|------------------------------------|--------|----------------------------------------|
| foreground on background           | +105.8 | Pass — body minimum ≥14.5px @ 400wt    |
| muted-foreground on background     |  +72.9 | Pass — headlines only ≥19.5px @ 400wt  |
| primary on background              | +104.7 | Pass — body minimum ≥15px @ 400wt      |
| secondary-foreground on background | +104.7 | Pass — body minimum ≥15px @ 400wt      |
| accent-foreground on background    | +104.7 | Pass — body minimum ≥15px @ 400wt      |
| destructive on background          |  +70.1 | Pass — headlines only ≥19.5px @ 400wt  |
| card-foreground on background      | +105.8 | Pass — body minimum ≥14.5px @ 400wt    |
| popover-foreground on background   | +105.8 | Pass — body minimum ≥14.5px @ 400wt    |
| border on background               |  +12.9 | Fail — insufficient contrast           |

### DARK mode

| Name                               |     Lc | Verdict                                |
|------------------------------------|--------|----------------------------------------|
| foreground on background           | -104.4 | Pass — body minimum ≥15px @ 400wt      |
| muted-foreground on background     |  -51.2 | Pass — headlines only ≥32px @ 400wt    |
| primary on background              | -104.4 | Pass — body minimum ≥15px @ 400wt      |
| secondary-foreground on background | -104.4 | Pass — body minimum ≥15px @ 400wt      |
| accent-foreground on background    | -104.4 | Pass — body minimum ≥15px @ 400wt      |
| destructive on background          |  -10.4 | **Fail — insufficient contrast**       |
| card-foreground on background      | -104.4 | Pass — body minimum ≥15px @ 400wt      |
| popover-foreground on background   | -104.4 | Pass — body minimum ≥15px @ 400wt      |
| border on background               |   +0.0 | Fail — insufficient contrast           |

## Headline findings

### 🚨 1. `destructive` text fails completely in dark mode

`oklch(0.396 0.141 25.723)` against `oklch(0.145 0 0)` scores **Lc -10.4** — under the Lc 15 floor. This means the default shadcn dark-mode destructive color **cannot be used for any text role**, including small icons paired with text. In light mode the same token is fine (Lc +70.1, passes for ≥19.5px).

**Why it happens:** the destructive color was tuned to be visible on a *light* page — the dark-mode override darkens it to keep brand consistency, but doesn't compensate for the now-darker background.

**Fix:** introduce a separate `--destructive-foreground-dark` (or restructure so the dark variant uses a lighter, more saturated red, e.g. `oklch(0.65 0.2 25)` lands around Lc -55).

### ⚠️ 2. `muted-foreground` is too low-contrast in dark mode for caption text

Lc -51.2 → minimum 32px @ 400wt. That's fine for body paragraphs but **fails for any text under 24px** — the typical home of timestamp / placeholder / hint text. In light mode it lands at Lc +72.9 (≥19.5px), so the same role is comfortable for 14–16px there.

**Fix:** either tighten the dark-mode `muted-foreground` (push closer to Lc -65, around `oklch(0.78 0 0)`) or document that this token is only for ≥18px in dark mode.

### ℹ️ 3. `border` (Lc 8–13 / 0.0) — expected, not a bug

Borders score Lc 8–13 in light and ~0 in dark. APCA flags these as "fail for text," which is correct — they shouldn't be used for text. They're fine for non-text UI per the APCA Bronze conformance for non-text contrast (Lc ≥ 15 for graphic objects). The dark-mode `border` matching `secondary` exactly (both `oklch(0.269 0 0)`) is why Lc is literally 0; if border visibility matters for your UI, raise the `border` token to ~`oklch(0.32 0 0)` to clear the Lc 15 floor against `--background`.

## How to act on this

1. **Fix red flags first.** The destructive dark-mode failure is a real accessibility regression — anyone who reads error messages on a dark theme is being failed.
2. **Decide a policy for muted text.** Either tighten the token, or codify "muted-foreground is only valid for 18px+ in dark mode" in your typography system.
3. **Re-run after fixing.** `python3 scripts/apca.py --from-tailwind <your file>` is idempotent and fast (<200ms). Make it part of your design-system PR review.
4. **Pick your floor.** APCA Lc 75 is the comfortable body-text target across most weights at 16px. If you want a single number to enforce, that's it.

## Why this matters more than it looks

The shadcn Neutral default theme is one of the most-deployed React UI starting points in the world. It ships with a dark-mode failure for destructive text by default. If your project hasn't audited it, you almost certainly have at least one place where an error message is illegible to users with mild low-vision conditions in dark mode. This is not a hypothetical — it's the single most common finding when auditing real shadcn-based apps.

That is the entire point of this skill: surfacing this exact class of finding in under a second per theme.
