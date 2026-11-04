---
name: Reacher GitHub profile
description: A bold public portfolio built around products and accepted upstream work.
colors:
  midnight: "#080e18"
  ice: "#edf4fc"
  slate: "#a4b6cb"
  mint: "#79ffe1"
  night-line: "#26364c"
  paper: "#f5f8fc"
  ink: "#102238"
  steel: "#50647d"
  forest: "#086b57"
  day-line: "#d5dfeb"
typography:
  wordmark:
    fontFamily: Space Grotesk
    fontWeight: 700
  statement:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 27px
    fontWeight: 500
  description:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 18px
    fontWeight: 400
rounded:
  panel: 12px
spacing:
  panel-inset: 32px
components:
  brand-panel:
    backgroundColor: "{colors.midnight}"
    textColor: "{colors.ice}"
    rounded: "{rounded.panel}"
  statistics-dark:
    backgroundColor: "{colors.midnight}"
    textColor: "{colors.ice}"
    rounded: "{rounded.panel}"
  statistics-light:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
---

# Design System: Reacher GitHub profile

## Overview

**Creative North Star: "Built and accepted"**

A confident contributor portfolio. Large custom lettering establishes Reacher's identity; real products and accepted upstream fixes supply its substance. The surrounding GitHub interface stays native.

The visual character comes from clear typography, a midnight canvas, and mint contribution paths. All public copy is English. Product descriptions use the approved facts, and metrics state their time window and privacy scope.

**Key Characteristics:**

- Outlined Space Grotesk lettering.
- Branch drawings tied to verified public merges.
- A consistent midnight finish for responsive brand artwork.
- Native links, tables, and expandable methodology.

## Colors

Mint marks contribution paths and the largest activity bar. Ice and slate provide the primary and secondary text hierarchy on midnight. Statistics cards use forest, ink, steel, and paper in GitHub's light theme; borders use the corresponding night or day line.

**The Evidence Rule.** Accent color emphasizes real contribution data and accepted fixes.

## Typography

Space Grotesk at weight 700 is converted to SVG paths for the REACHER and product wordmarks. Its original SIL Open Font License is retained in `assets/brand/OFL.txt`; no font download is required at runtime.

SVG statements and descriptions use the platform sans stack. The token sizes describe their SVG coordinate space; the artwork scales within GitHub's README container. Readable native Markdown repeats the key totals and explains the charts.

## Layout

Brand panels use a shared inset. The desktop hero is an asymmetric wordmark and three-branch composition (900 by 288). At widths of 600px or less, it changes to a compact composition (440 by 312). Product panels change from three columns to three stacked rows. The activity chart also has a dedicated narrow composition.

GitHub rewrites media queries containing `prefers-color-scheme`, dropping combined width conditions. Brand artwork therefore uses width-only picture sources and a stable midnight finish. Stats Extended cards use separate theme-only sources. Do not combine these conditions or put a picture inside a link: both patterns failed on the actual GitHub renderer.

Stats cards share aligned canvases and display at up to 400px each, wrapping on narrow screens. Image URLs include content hashes so freshly updated copy and chart values stay consistent through caching.

## Elevation & Depth

The custom artwork has no shadows. Quiet borders and the difference between the native GitHub frame and the artwork establish depth. All custom charts and contribution paths are static.

## Shapes

Panels use gently curved corners. Fine dividers separate products; circular nodes connect accepted fixes to their originating contribution path. The geometry describes contribution relationships.

## Components

The signature hero draws only verified public upstream merges. The product panel contains the three approved summaries and no private repository links. The monthly chart groups anonymous calendar counts, with partial boundary months disclosed in its accessible description and methodology.

The official Stats Extended cards retain their generated numbers. A local preparation step clarifies public PR labels and aligns the outer canvases without changing data. Native Markdown links, tables, headings, and details retain GitHub's focus, hover, and disclosure behavior.

## Do's and Don'ts

### Do

- Do keep product descriptions faithful to the approved summaries.
- Do pair anonymous private counts with explicit privacy and time-window labels.
- Do keep merged PRs in the full history after they leave the homepage's latest entries.
- Do verify the actual GitHub page at desktop and narrow widths after changing picture markup.

### Don't

- Don't publish private repository identifiers, commit messages, paths, or code.
- Don't present contribution events as authored lines of code or language bytes as proficiency.
- Don't add fabricated ranks or achievements.
- Don't replace the last valid published charts with an error response.
