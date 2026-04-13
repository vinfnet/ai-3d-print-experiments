# AI 3D Print Experiments

A collection of 3D-printable models generated entirely by AI. Each model is created programmatically using Python scripts that output STL files ready for slicing and printing.

## Models

| Model | Script | STL | Description |
|-------|--------|-----|-------------|
| Screwdriver in Banana | `generate_screwdriver_banana.py` | `screwdriver_in_banana.stl` | A screwdriver stuck in a curved banana (~150mm) |
| Coffee Cup | `generate_coffee_cup.py` | `coffee_cup.stl` | A tapered mug with a C-shaped handle (80mm tall) |
| Azure Cloud | `generate_cloud_ms_logo.py` | `cloud_microsoft_logo.stl` | A puffy cloud with Microsoft logo, padlock, and "Azure Confidential Computing" nameplate (130mm wide) |
| iPhone MacBook Mount | `generate_iphone_macbook_mount.py` | `iphone_macbook_mount.stl` | Clips iPhone 16 Pro (in Apple Silicone Case, landscape) onto MacBook Pro 14" screen top edge with webcam clearance (151mm wide) |
| Egg Beater Pedal Adapter | `generate_eggbeater_adapter.py` | `eggbeater_adapter.stl` | Platform adapter for Crank Brothers Egg Beater pedals — clips in like a cleat, provides a flat 95×75mm pedal surface for normal shoes. Print twice (one per pedal). (95mm wide, 19mm tall) |

## How It Works

Each Python script uses `numpy` and `numpy-stl` to procedurally generate triangle meshes from geometric primitives (spheres, cylinders, swept profiles, extruded text, etc.) and exports them as binary STL files. No manual CAD modelling involved — just AI-written code.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy numpy-stl

# Generate a model
python generate_coffee_cup.py
```

Load the resulting `.stl` file into your slicer (PrusaSlicer, Cura, Bambu Studio, etc.) and print.

## License

Experimental / personal use.
