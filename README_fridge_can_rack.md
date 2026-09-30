# Fridge Can Rack — hanging 330ml can holder

A modular frame that clips onto the front edge of a glass fridge shelf and
hangs underneath it, holding a single row of 330ml cans lying on their side.
The row runs **front to back** into the fridge, so the rack only uses the
width of one can and leaves the rest of the shelf free.

![Assembled rack under a glass shelf, loaded with five cans](fridge_can_rack.png)

> Blue = printed rack · red = 330ml cans · translucent = the glass shelf.
> **Interactive 3D:** open [`fridge_can_rack_assembly.stl`](fridge_can_rack_assembly.stl)
> — GitHub renders STL files in a built-in 3D viewer you can spin and zoom.

## How many cans?

A 330ml can is Ø66mm. With a 72mm bay pitch (can + anti-roll ridge) the rack
uses `5 × 72 + 4 = 364mm` of a **380mm deep** shelf, leaving 16mm of clearance
at the back — so **five cans** is the maximum that fits. A sixth bay would
need 436mm.

## Dimensions

| | |
|---|---|
| Assembled size | 129mm wide × 373mm long × 83mm tall |
| Shelf depth used | 364mm (of 380mm available) |
| Clearance needed **under** the shelf | 74mm |
| Clearance needed **above** the shelf | 3mm (the clip flanges lie flat on the glass) |
| Glass thickness it clamps | 6mm (adjustable — see *Customising*) |
| Capacity | 5 × 330ml cans (Ø66 × 115mm), ≈1.8kg |

## How it works

* Two **shelf clips** wrap around the front edge of the glass. Each has a
  140mm flange that lies flat on *top* of the glass, so the load is taken by
  the shelf itself rather than by a fragile hook.
* Five **can bays** chain backwards under the glass on lap joints with a
  snap bump, forming an open-topped channel. The glass itself is the ceiling.
* A ramp at the front of each bay lets you push cans in from the front and
  stops them rolling back out.
* An **end stop** closes the back of the rack.
* Cans are loaded and taken from the front: push the row back, take the
  front can out.

![The three printable parts](fridge_can_rack_parts.png)

## Print it

| Part | STL | Qty | Size |
|------|-----|-----|------|
| Can bay | [`fridge_can_rack_bay.stl`](fridge_can_rack_bay.stl) | **5** | 127 × 90 × 74mm |
| Shelf clip | [`fridge_can_rack_shelf_clip.stl`](fridge_can_rack_shelf_clip.stl) | **2** | 80 × 149 × 25mm |
| End stop | [`fridge_can_rack_end_stop.stl`](fridge_can_rack_end_stop.stl) | **1** | 127 × 74 × 22mm |

Every part fits a 220 × 220mm bed and is already saved in its recommended
print orientation — drop the STL into your slicer and print it as-is.

Suggested settings:

* **Material:** PETG or PLA (PETG preferred — it is tougher and does not mind
  fridge temperatures or condensation).
* **Layer height:** 0.2mm · **Walls:** 4 perimeters · **Infill:** 25–30%.
* **Supports:** none needed.
* **Note:** `fridge_can_rack_assembly.stl` is a visualisation of the finished
  rack — it is *not* a printable part.

## Assemble it

1. Slide the front of one bay into the rear lap of another until the snap
   bump clicks into the window. Repeat until all five bays are joined.
2. Push the **end stop** onto the rear lap of the last bay.
3. Push a **shelf clip** onto each side of the front bay the same way.
4. Slide the whole rack onto the front edge of the glass shelf: the flanges
   go on top of the glass, the channel hangs underneath.
5. Load cans in from the front, pushing each one over the ramp.

If your prints are on the tight side, ease the lap joints with a file; if
they are loose, a drop of superglue or a cable tie through the snap window
will lock them permanently.

## Customising

Edit the constants at the top of
[`generate_fridge_can_rack.py`](generate_fridge_can_rack.py) and re-run it:

| Constant | Default | What it does |
|----------|---------|--------------|
| `GLASS_T` | `6.0` | **Measure your shelf** and set this — it is the clamp gap |
| `SHELF_DEPTH` | `380.0` | Your shelf depth (informational / capacity check) |
| `N_BAYS` | `5` | Bays in the assembly preview; print as many bays as you need |
| `BAY` | `72.0` | Bay pitch — increase for fatter cans |
| `W_IN` | `121.0` | Clear width — increase for longer cans (500ml is 168mm tall) |
| `WALL_H` | `71.0` | Height of the channel under the shelf |
| `CLIP_FLANGE_LEN` | `140.0` | How far the clip reaches back over the glass |

## Regenerate

```bash
python -m venv .venv && source .venv/bin/activate
pip install numpy numpy-stl

python generate_fridge_can_rack.py   # writes the four STL files
python render_fridge_can_rack.py     # writes the two PNG visualisations
```
