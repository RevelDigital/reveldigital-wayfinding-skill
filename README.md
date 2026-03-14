# Revel Digital Wayfinding Skill

A Claude skill for generating wayfinding floorplan configurations for the [Revel Digital Wayfinding App](https://reveldigital.github.io/wayfinding-app/). Provide floor plan images (or describe your building layout) and this skill generates the complete JSON configuration including locations, waypoint navigation graphs, and a visual preview for verification.

## Features

- **Image-based generation** — Upload floor plan images and the skill visually analyzes them to identify rooms, corridors, entrances, and elevators, then generates waypoint coordinates in image-pixel space.
- **Text-based generation** — Describe your building layout in plain text and the skill generates SVG floor plan images along with the JSON configuration.
- **Visual preview** — Always generates an interactive overlay showing waypoints and connections on the floor plan so you can verify placement before deploying.
- **Multi-floor support** — Handles elevator and stairwell connections across floors with transport waypoints.
- **Validation** — Includes a validation script that checks bidirectional connections, graph connectivity, coordinate bounds, and cross-references.

## Installation

Download the latest `.skill` file from [Releases](../../releases) and install it in Claude.

Alternatively, copy the `revel-wayfinding/` directory to your Claude skills folder:

```
revel-wayfinding/
├── SKILL.md                         # Main skill instructions
├── scripts/
│   └── validate.py                  # Floorplan JSON validator
└── references/
    └── floorplan-schema.json        # JSON Schema definition
```

## Usage

### From a floor plan image

Upload one or more floor plan images and ask Claude to generate the wayfinding configuration:

> Here's the floor plan for our office building. Can you generate a wayfinding configuration for our Revel Digital kiosk?

The skill will:
1. Analyze the image to identify rooms, corridors, and entrances
2. Place waypoints at corridor intersections and room doorways
3. Build the navigation graph with bidirectional connections
4. Generate the complete JSON configuration
5. Validate the output
6. Render a visual preview of the waypoint graph

### From a text description

Describe your building and Claude will generate both SVG floor plans and the JSON configuration:

> We have a two-story medical clinic. Ground floor has a main lobby, reception, two exam rooms, and a waiting area. Second floor has four offices, a conference room, and a break room. There's an elevator connecting the floors.

### Output

The skill produces a `floorplan.json` file conforming to the [Wayfinding Floorplan Schema](https://reveldigital.github.io/wayfinding-app/floorplan-schema.json).

```json
{
  "locations": [
    {
      "id": "1",
      "name": "Main Lobby",
      "category": "Common",
      "floor": "1",
      "room": "100",
      "description": "Welcome desk and visitor check-in.",
      "icon": "🏥",
      "tags": ["entrance", "reception"],
      "waypointId": "f1-lobby"
    }
  ],
  "floors": [
    {
      "floor": "1",
      "label": "Floor 1 — Ground",
      "image": "https://example.com/floorplan-f1.svg",
      "imageSize": [1000, 500],
      "youAreHere": "f1-entrance",
      "waypoints": [
        { "id": "f1-entrance", "x": 100, "y": 480, "connections": ["f1-cor-bl"] },
        { "id": "f1-cor-bl", "x": 100, "y": 305, "connections": ["f1-entrance", "f1-lobby"] },
        { "id": "f1-lobby", "x": 100, "y": 195, "connections": ["f1-cor-bl"] }
      ]
    }
  ]
}
```

## Validation

The included validation script checks the generated JSON for common issues:

```bash
python revel-wayfinding/scripts/validate.py floorplan.json
```

Checks performed:
- No duplicate location or waypoint IDs
- All location `floor` references exist in the floors array
- All `waypointId` references exist in the correct floor's waypoints
- All `youAreHere` references are valid
- All waypoint connections are bidirectional
- Transport waypoints have `isTransport` and `transportName`
- Waypoint coordinates are within image bounds
- Navigation graph is fully connected (every room reachable from start)

## Schema

The full JSON Schema is available at:
- [floorplan-schema.json](https://reveldigital.github.io/wayfinding-app/floorplan-schema.json)
- [Configuration Guide](https://reveldigital.github.io/wayfinding-app/floorplan-schema.md)

## Development

### Packaging

To build the `.skill` file locally:

```bash
pip install pyyaml
python scripts/validate_skill.py revel-wayfinding
python scripts/package_skill.py revel-wayfinding dist
```

The packaged file will be at `dist/revel-wayfinding.skill`.

### CI/CD

A GitHub Actions workflow automatically packages and attaches the `.skill` file to each release. Create a release tag to trigger it, or run the workflow manually via `workflow_dispatch`.

## License

MIT — see [LICENSE](LICENSE).
