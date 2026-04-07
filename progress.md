# Sail-Viz Brainstorming Progress

> Working session capturing the interrogation of `sail_vision_v1_scope.md`. The plan is to keep brainstorming until the design is concrete, then write a fresh design spec at `docs/superpowers/specs/2026-04-07-sail-vision-v1-design.md` that supersedes the original scope doc, then transition to implementation planning.

---

## Session 1 — 2026-04-07

### Decisions made

#### Original four open questions from §17 of the scope doc

| # | Question | Decision |
|---|---|---|
| 1 | Are the three draft stripes visible in most clips, or only a subset? | **Subset only, condition-dependent.** Frame ranker is load-bearing; upper stripe is weakest; visibility filter is a real pipeline stage. |
| 2 | Is V1 Snipe-only acceptable? | **Yes.** Class-specific priors (3 stripes, geometry, expected stripe spacing) are fair game. |
| 3 | One tack first, mirror later? | **No — both tacks native, no mirroring tricks.** Sail setups differ tack-to-tack, so the asymmetry is real signal. `tack` is a required field on every annotation; same-tack comparison is the default; nothing in the measurement pipeline gets to assume symmetry. |
| 4 | Is 1–2 manual corrections per frame acceptable? | **Option B: small fully-manual "gold set" + auto-attempt on the rest.** Two tracks: a frozen hand-labeled validation set + a pipeline that runs auto and is scored against it. Gives both regression-test stability and an honest per-point error number for the auto detector as it improves. |

#### Deeper interrogation decisions (in order they were asked)

**User intent / decision context**
- Use case: **cross-session library used in debrief mode**
- Specifically: multiple sailors take turns sailing the *same* boat (e.g., warm-up before a race), claim to have identical setups, but actually don't
- The tool's job: surface those trim differences so the coach can flag them
- Failure mode to avoid: producing **fake differences** (low credibility) — NOT missing subtle ones (low recall)

**Aggregation unit**
- **D leaning C: store full per-frame distribution per clip** — aggregation is render-time, not destructive
- **Primary visualization: curve heatmap over accepted frames in a clip**
  - Y axis = height up the sail
  - X axis = horizontal offset from mast (`d_i` values, normalized)
  - Each accepted frame contributes a 3-point curve through the stripe endpoints
  - Overlaid frames produce a density band
  - Two heatmaps side by side (sailor A vs sailor B): visible separation = real difference, overlap = noise
- Median ± IQR is a numeric sidecar, NOT the headline
- "Ideal for analysis" is broader than alignment alone — composite gate

**Conditions handling**
- Natural unit is **session**, not clip
- Per-session metadata (e.g., "8kt sea breeze, light chop") is written once and inherited by every clip in the session
- Within a session, conditions are assumed roughly constant — sailors are filmed minutes apart in the same conditions
- **No hard gating** on conditions; coach interprets
- **V1 only compares within a session.** Cross-session is V2.
- Data hierarchy: `session → clip → frame → signature` (sessions are first-class)

**Discrimination floor**
- **Designed for "drastic" deltas: ~10% of mast height or larger in stripe-endpoint offset**
- Tool noise budget: ~3% of mast height
- Tool is an "extension of the coach's eye", not a precision instrument
- Will be validated against the user's own eye iteratively (the user is a national champion sailor and is the validation oracle)
- Precision target may tighten later based on field feedback, but A is the starting bar

**Alignment criteria (from the example image the user provided)**
The user shared a frame with green-line annotations and described their visual decision process. Translated to operational signals:

| User's eye | Pixel-level signal |
|---|---|
| "clew lined up with mast" | `\|clew_x − mast_x_at_clew_y\| / mast_pixel_height` is small |
| "rudder straight up and down" | rudder long-axis tilt from vertical is small (this is really a *frame-stability* check, not a zero-heel check) |
| "both parts of the sail in frame" | sail bounding box fully inside frame, no edge clipping |
| "all 3 stripes visible" | each stripe endpoint is detectable AND not occluded |

Composite alignment score = product of soft 0–1 signals from each component. If any drops to ~0, frame is rejected. Exact thresholds are deferred — they should be tuned against the user's eye on real frames, not picked in the abstract.

**Camera roll / heel correction**
- **NOT a pipeline step.** Reject unstable/lurching frames via rudder-verticality check.
- Moderate steady heel is accepted as-is — Snipes upwind always have some heel.
- Revisit only if heatmaps show heel-driven noise.

**The green-line image is also a mockup of the desired output overlay**
- Single bright vertical reference line through the mast
- Small marker at the gooseneck
- Line extends through the boom area
- Minimal clutter
- This is the visual language for the overlay renderer

**Sprint 1 shape**
- **Option A: single-frame analyzer with manual point placement.** Load one image, click ~5–7 keypoints (mast head, mast base, gooseneck, clew, three stripe endpoints), tool draws the green-line overlay + leech opening curve, computes the twist signature, saves a JSON.
- *No* heatmap, *no* clip aggregation, *no* video, *no* automation in Sprint 1
- Sprint 1's purpose framed properly: **"the smallest credible demonstration that the 2D astern proxy can rank-order known-different sail trims correctly"** — NOT "the smallest viable single-frame analyzer"
- Validation test: take ~10 hand-picked frames where the user already knows the answer ("this one is more open, this one is more closed"); if the twist signature ranks them in the same order as the user's eye, the proxy is meaningful; if not, we found that out in days, not weeks

**Distribution model / strategic positioning**
- **Open source tool + hosted integration on the coach's domain (user manages)**
- Single permissive license (likely MIT or Apache 2.0)
- The coach owns a sailing technology business; the user runs the hosted integration on their domain
- Architecture: **library at the core** (`session → clips → frames → signatures → heatmap`), **thin frontends on top** (CLI / local web app for Sprint 1; hosted web app on coach's domain later)
- Library should NOT bake in "files on local disk" assumptions — treat I/O as parameters so the same core works locally and hosted
- Privacy: open-source local mode = "your video stays on your machine"; hosted version handles uploads (V2+)

**Differentiation framing**
- This tool intentionally does NOT compete with VSPARS, North 3DL, sailmaker proprietary tools, or other 3D sail shape reconstruction systems
- Those need calibrated cameras / known marker spacing / on-board hardware, and target "is my sail shape right" for one boat
- This tool's wedge is the *opposite* set of constraints: uncalibrated coach-boat archive video, 2D astern projection, statistical aggregation across frames, cross-sailor diagnostic for the debrief room
- The pitch: **"use the footage you already have to surface trim differences between sailors who think they have the same setup"**
- Never "VSPARS but cheaper"

---

### What now needs editing in the original scope doc

These items in `sail_vision_v1_scope.md` are now stale or contradicted by decisions above:

1. **§6 scope constraints** says *"ideally one tack only at first, with the other tack mirrored later"* — contradicts Q3. Should change to "both tacks handled natively; no mirroring".
2. **§4 V1B "user selects one or two frames"** — manual frame selection across sailors is a bias trap for cross-sailor diagnostic. Aggregation is a clip-level statistical operation across many accepted frames, not a manual single-frame pick.
3. **§5 measurement** is defined per-frame but the *output of interest* is now per-clip or per-sailor heatmap. Per-frame is an intermediate.
4. **§10 annotation schema** has `tack` as a regular field — should be marked required.
5. **§12 definition of done** and **§13 acceptance criteria** should reference the gold set explicitly, and include a user-acceptance test against the user's eye.
6. **§13 video acceptance "two selected frames produce a meaningful directional comparison"** — same bias problem as §4. Should be clip-level, not frame-level.
7. **§17 open questions** — Q1–Q4 are answered. Q5 (folder of low/med/high twist examples) is still open.
8. **No mention of "session" anywhere** — the data hierarchy needs to add a `session` level above `clip`.
9. **No mention of "heatmap visualization" anywhere** — currently the doc assumes overlay images and JSON; the heatmap is the new headline output.
10. **No mention of distribution model / open source / library architecture / hosted integration** — needs adding.

(These edits will go into the fresh design spec rather than back-editing the scope doc.)

---

### Memory files written

| File | Purpose |
|---|---|
| `~/.claude/projects/-Users-diegoescobar-Dev-sail-viz/memory/MEMORY.md` | Index |
| `.../memory/user_sailing_expertise.md` | User is a national champion sailor; serves as validation oracle |
| `.../memory/project_sail_viz_intent.md` | V1 use case, session model, discrimination floor, validation loop, distribution model, differentiation framing |

---

### Tasks completed in session 1

- [x] #1 — Pin down user intent and decision context
- [x] #2 — Pin down aggregation unit (frame/clip/sailor)
- [x] #3 — Pin down conditions handling (wind, heel, waves)
- [x] #4 — Define alignment score formula and threshold *(structure decided; thresholds deferred to empirical tuning)*
- [x] #8 — Decide camera roll / boat heel handling

---

### Tasks still pending — to address tomorrow

In rough priority order. The first two are loose ends from session 1; the rest are net-new interrogation topics.

#### Loose ends from session 1

1. **(Q6a) Specific tools to benchmark against**
   - Is VSPARS the main "serious incumbent" you're worried about?
   - Are there *Snipe-class-specific* video analysis tools that already exist that I should know about?
   - Does your coach's business already have any sail-analysis features it's offering today that this would extend or replace?
   - **Why this matters:** the differentiation pitch goes in the spec README, and it needs to name the right targets.

#### Sprint 1 mechanics

2. **(#7) Manual labeling tool choice** — what does the click-points-on-a-frame UX actually look like for Sprint 1?
   - **A)** Jupyter notebook with matplotlib clicks
   - **B)** Tiny tkinter / PyQt desktop app
   - **C)** Tiny local web page (Flask/FastAPI + HTML canvas) — *my recommendation, since it's the same shell that grows into the heatmap UI later*
   - **D)** Off-the-shelf tool (LabelMe, CVAT)
   - **E)** Smaller — render-with-guesses, edit JSON
   - This decision determines what Sprint 1 actually builds.

3. **(#5) Normalization baseline**
   - §5.3 lists three options: mast pixel height vs base-to-head distance vs class-consistent sail scale
   - **My recommendation:** mast pixel height in the *current frame* (self-corrects for camera distance and zoom). Lock in unless you push back.

4. **(#6) Gold set specifics**
   - How many frames? My estimate: 20–40 to start
   - Curation rules: should it include *paired* examples (same boat, two sailors, known-different trim) so the discrimination test is built into the gold set?
   - Storage: in-repo `sample_data/gold/` or out-of-repo? Privacy implications?
   - Versioning: how do we know which version of the gold set a regression test was run against?
   - Integration: should the test suite automatically run against the gold set on every commit?

5. **(#9) Comparison metric & confidence definition**
   - The scope doc mentions "twist signature and confidence" but never defines confidence
   - Per-point or per-frame? Derived from alignment score, detector confidence, distribution width, or something else?
   - Which derived metric (`upper_minus_lower`, slope of opening vs height, etc.) is the headline number under the heatmap?

6. **(#13) Cross-tack and cross-clip comparison rules**
   - Given Q3 (tacks are not symmetric), what comparisons does the UI even allow?
   - Same-tack only? Cross-tack with a warning? Cross-clip default behavior within a session?
   - What does the UI do when the user tries to compare a port-tack clip to a starboard-tack clip?

#### Pipeline mechanics

7. **(#10) Automation path from manual to auto**
   - Classical CV (Hough lines for mast, color masks for stripes, edge detection for boom) vs learned keypoint model vs segmentation
   - When does automation enter — Sprint 2? Sprint 3?
   - What does the gradient from manual → assisted → fully auto look like?

8. **(#11) Video frame sampling strategy**
   - Every frame? Every N? Scene-change detection?
   - Affects compute volume and how aggressive the alignment-score filter has to be downstream

9. **(#12) Input format & resolution assumptions**
   - Container formats (MP4, MOV, WebM…)
   - Codec assumptions (H.264 only, or anything ffmpeg can read?)
   - Minimum resolution
   - Minimum sail size in pixels for the geometry to be reliable

#### Architecture & wrap-up

10. **(#14) Propose 2–3 architectural approaches**
    - After all interrogation questions are answered, lay out alternative shapes for the V1 build with trade-offs and a recommendation

11. **(#15) Present design sections and get approval**
    - Walk through architecture, components, data flow, error handling, testing in scaled sections
    - Get user approval after each section before moving on

12. **(#16) Write fresh design spec**
    - Save to `docs/superpowers/specs/2026-04-07-sail-vision-v1-design.md` (or whatever date we land on)
    - Run spec self-review (placeholder scan, internal consistency, scope check, ambiguity check)
    - Ask user to review before invoking the writing-plans skill to create the implementation plan

---

### Note for tomorrow's session

> **Enable extended thinking before continuing.** Several of the remaining decisions (especially #10 automation path, #14 architectural approaches, and the spec self-review) benefit from deeper reasoning. Toggle with Option+T (macOS), or set `alwaysThinkingEnabled` in `~/.claude/settings.json`. Verbose thinking output is Ctrl+O.

When picking up tomorrow, the suggested re-entry is:

1. Read this `progress.md`
2. Read `sail_vision_v1_scope.md` for the original scope
3. Read the memory files at `~/.claude/projects/-Users-diegoescobar-Dev-sail-viz/memory/` — they have the persistent context
4. Re-load the brainstorming skill (`superpowers:brainstorming`)
5. Resume at loose end #1 (specific tools to benchmark against), then continue down the pending list in order
