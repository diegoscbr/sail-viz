# Sail Vision V1 — Problem Statement and Tight Scope

## 1) Project goal
Build a narrow prototype that takes **astern-view Snipe sailing images/video** and produces a **repeatable relative mainsail twist measurement** from frames where the **boom is projected near the mast / centerline**.

The first usable output is **not full 3D sail shape**. It is a **2D astern-view twist proxy** based on the visible aft ends of the three draft stripes, rendered as:
- an annotated image overlay
- a compact numeric twist signature
- a side-by-side comparison between two accepted frames

---

## 2) Problem statement
The user has a large archive of coach-boat footage shot from behind the boat. Human sailors and coaches can often see meaningful changes in leech opening and twist from these videos, but there is no simple tool that lets a user upload a clip and immediately compare sail shape without manually dragging curves and points across the whole sail.

For V1, the target use case is:

> From a behind-the-boat image or video frame of a **Snipe mainsail**, detect frames where the **boom is effectively aligned with the mast / centerline in image projection**, identify the **three visible draft-stripe endpoints**, and compute a **relative twist signature** that can be compared across frames.

This prototype should help answer questions like:
- Which frame shows a more open upper leech?
- Which frame shows more relative twist from bottom to top?
- How does the “opening curve” change when trim changes?

---

## 3) What the sketch implies
The sketch suggests a very good narrow first scope:
- Use the **mast line** as the main vertical reference.
- Only use frames where the **boom is visually aligned with the mast / centerline** closely enough to make comparison meaningful.
- Detect the **aft ends of the three draft stripes**.
- Draw a **comparison curve** through those stripe endpoints.
- Compare that curve and its offsets across frames.

This is a tighter and more realistic first build than trying to recover full camber or true 3D sail shape from arbitrary coach video.

---

## 4) V1 definition

### V1A — single-image prototype
Input: one astern-view image.

Output:
- mast reference line
- boom-alignment score
- three detected draft-stripe endpoints
- twist signature
- annotated overlay image

Human-in-the-loop correction is allowed in V1A.

### V1B — video candidate-frame mining
Input: one short astern-view clip.

Output:
- ranked candidate frames where boom alignment is best
- top accepted frames rendered with overlay
- ability to compare any two accepted frames

---

## 5) Exact measurement to build first

### 5.1 Reference geometry
For each accepted frame, detect or estimate:
- **mast_head** = top of visible mast
- **mast_base** = mast base / gooseneck region used to define mast reference line
- **clew** = optional, if visible and useful
- **stripe_lower_end** = aft visible endpoint of lower draft stripe
- **stripe_mid_end** = aft visible endpoint of middle draft stripe
- **stripe_upper_end** = aft visible endpoint of upper draft stripe

Define the mast reference line as the line through `mast_head` and `mast_base`.

### 5.2 Frame acceptance rule
Only analyze frames where boom alignment is good enough.

Operationally, a frame may be accepted when one or more of the following are true:
- the **clew lateral offset** from the mast line is below a threshold
- the visible boom segment has **minimal lateral projection**
- the **projected boom position lies near the mast x-coordinate** in the gooseneck/clew region

Store an `alignment_score` in `[0, 1]`.

### 5.3 Twist signature
For each stripe endpoint `P_i = (x_i, y_i)`:
1. project the corresponding x-position of the mast line at height `y_i`
2. compute the lateral opening offset

`d_i = x_i - x_mast(y_i)`

Normalize by a stable image scale, such as:
- mast pixel height, or
- distance from mast base to mast head, or
- another class-consistent sail scale

Result:

`twist_signature = [d_lower_norm, d_mid_norm, d_upper_norm]`

### 5.4 Derived comparison metrics
From that signature, compute:
- `upper_minus_lower = d_upper_norm - d_lower_norm`
- `mid_minus_lower = d_mid_norm - d_lower_norm`
- slope of opening versus height
- optional smooth curve through the three stripe endpoints

### 5.5 Interpretation
- Larger upper offset relative to lower offset = **more open upper leech / more twist**
- Smaller spread from lower to upper = **less twist / more closed leech**

Important language for engineering and UI:
- In code and docs, call this a **“2D astern-view twist proxy”**.
- Do **not** claim that it is a true 3D twist angle in V1.

---

## 6) Tight scope constraints
To keep this build realistic, V1 should be constrained to:
- **Snipe class only**
- **mainsail only**
- **astern / chase-boat perspective only**
- **daylight footage only**
- **upwind / close-hauled style trim only**
- **frames where all 3 draft stripes are visible**
- **frames with acceptable mast / sail visibility**
- ideally **one tack only** at first, with the other tack mirrored later

---

## 7) Non-goals for V1
Do **not** try to solve these yet:
- full 3D flying-shape reconstruction
- true camber percentage
- true draft-position percentage
- automatic multi-class support
- offwind sails / spinnakers
- automatic simultaneous two-boat comparison in one frame
- aerodynamic force estimation
- perfect full-video autonomy with zero user correction

---

## 8) Recommended user workflow
1. User uploads one image or one short video.
2. System extracts or receives candidate astern frames.
3. System scores frames for boom alignment and image usability.
4. User selects one or two frames.
5. System shows:
   - mast line
   - stripe endpoints
   - optional comparison curve
   - twist signature and confidence
6. User compares two frames side by side.

---

## 9) Recommended engineering build order

### Phase 1 — labeled still-image analyzer
Goal: prove that the geometry can be detected reliably on single frames.

Deliverables:
- image loader
- annotation schema
- overlay renderer
- manual correction option
- twist signature calculation

### Phase 2 — video frame extraction and ranking
Goal: find the best boom-aligned frames from clips.

Deliverables:
- frame extractor
- alignment scoring pipeline
- blur / visibility rejection
- top-N frame ranking

### Phase 3 — frame-to-frame comparison
Goal: compare two accepted frames and visualize the difference.

Deliverables:
- side-by-side comparison image
- delta twist signature
- difference curve or small plot

---

## 10) Annotation schema
Each labeled frame should store something like:

```json
{
  "image_id": "string",
  "boat_class": "Snipe",
  "tack": "starboard",
  "mast_head": [x, y],
  "mast_base": [x, y],
  "gooseneck": [x, y],
  "clew": [x, y],
  "stripe_lower_end": [x, y],
  "stripe_mid_end": [x, y],
  "stripe_upper_end": [x, y],
  "all_three_stripes_visible": true,
  "boom_aligned": true,
  "alignment_score_manual": 0.92,
  "image_quality_manual": 0.85,
  "notes": "good astern frame, slight sky glare"
}
```

Fields like `gooseneck` and `clew` can be optional at first if they are too hard to label reliably.

---

## 11) Minimum viable deliverables for the coding agent
A first repo does not need to be fancy. It should include:

- `extract_frames.py` — extract frames from video
- `label_schema.md` — explain required annotations
- `analyze_frame.py` — compute overlay + twist signature on one image
- `compare_frames.py` — compare two accepted frames
- `render_overlay.py` — draw mast line, stripe endpoints, and curve
- `notebooks/eda.ipynb` — inspect labeled data and debug geometry

Optional but useful:
- `configs/default.yaml`
- `tests/` for measurement logic
- `sample_data/` with a handful of manually labeled frames

---

## 12) Definition of done for the first sprint
A successful first sprint should do the following on a small set of handpicked Snipe images:
- load a single image
- detect or accept manual entry for mast line
- detect or accept manual entry for the 3 stripe endpoints
- compute a twist signature
- output an annotated image
- output a simple JSON result file

If that works reliably on clean still images, move to video.

---

## 13) Acceptance criteria

### Single-image acceptance
On a small labeled validation set of clean images:
- mast line is correct or quickly correctable
- stripe endpoints are visually acceptable on most usable frames
- twist signature follows expert intuition for low / medium / high twist examples

### Video acceptance
On a small set of short clips:
- top-ranked candidate frames are usually usable
- rejected frames are mostly blurry, occluded, or misaligned
- two selected frames produce a meaningful directional comparison

---

## 14) Risks and mitigation

### Risk: stripe visibility is weak
Mitigation:
- restrict dataset to frames where stripes are clearly visible
- allow manual point correction in V1

### Risk: boom is not clearly visible
Mitigation:
- use clew-to-mast alignment as the primary proxy if needed
- treat boom detection as helpful, not mandatory, in the first pass

### Risk: camera roll / wave motion changes geometry
Mitigation:
- normalize by mast line
- optionally rotate frame so mast is vertical before measuring

### Risk: camera is too far off centerline
Mitigation:
- reject low-confidence frames
- store `alignment_score`

### Risk: astern view can confuse true twist with viewpoint effects
Mitigation:
- keep claims limited to a 2D astern-view twist proxy
- only compare frames under similar viewpoint conditions

---

## 15) Suggested baseline implementation strategy
The coding agent should start with the **simplest thing that works**.

Recommended order:
1. Build a manual-label pipeline first.
2. Get measurement and overlay logic correct.
3. Then automate mast and stripe detection.
4. Then add video frame ranking.

Possible technical baseline:
- OpenCV for image loading, frame extraction, line utilities, and overlay rendering
- manual labels or lightweight GUI clicks for early debugging
- optional segmentation/keypoint model later, once labels exist

The critical thing to prove first is **measurement stability**, not model sophistication.

---

## 16) What to call the output in the UI
Recommended UI labels:
- **Mast reference line**
- **Stripe endpoints**
- **Leech opening curve**
- **Twist signature**
- **Upper leech opening**
- **Frame alignment score**

Avoid in V1:
- “True twist angle”
- “Camber percentage”
- “3D sail shape”

---

## 17) Open questions for the user
These should be answered before the second sprint:
- Are the three draft stripes present and visible in most of the archive?
- Is it acceptable for V1 to be **Snipe-only**?
- Should V1 start with **one tack only** and mirror later?
- Is **one or two manual corrections per frame** acceptable in the first prototype?
- Do you already have a small folder of obvious **low-twist / medium-twist / high-twist** examples?

---

## 18) Recommended next sprint
**Sprint 1 target:**

Build a **single-image Snipe analyzer** that:
- accepts one astern image
- detects or allows manual correction for mast line and 3 stripe endpoints
- computes a 3-value twist signature
- renders an annotated output image

That will validate whether the sketch can become a real measurement pipeline before spending time on full video automation.

---

## 19) Ready-to-paste coding-agent handoff prompt
Use this as the seed prompt for Codex or another coding agent:

```text
Build a narrow Python prototype for astern-view Snipe mainsail analysis.

Goal:
Given a single astern-view image of a Snipe under sail, detect or allow manual correction for:
- mast head
- mast base
- three aft draft-stripe endpoints

Then compute a normalized 3-value twist signature using the horizontal offset of each stripe endpoint from the mast line at the same height.

Constraints:
- Start with still images only.
- Use clean daytime astern images with visible draft stripes.
- Do not attempt true 3D reconstruction.
- Treat the result as a 2D astern-view twist proxy.
- Keep the code simple and debuggable.
- Human-in-the-loop correction is acceptable.

Deliverables:
- a script to analyze one image
- a rendered overlay image
- a JSON result file with keypoints, alignment score, and twist signature
- a simple comparison script for two analyzed frames

Prefer the simplest working baseline over a complex model. Start by getting the measurement geometry and overlays right.
```
