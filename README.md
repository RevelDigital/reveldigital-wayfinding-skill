# Revel Digital Wayfinding Skill for Claude

A [Claude AI Skill](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) that generates wayfinding floorplan configurations for the [Revel Digital Wayfinding App](https://reveldigital.github.io/wayfinding-app/). Provide floor plan images (or describe your building layout) and get a complete JSON configuration with locations, waypoint navigation graphs, and a visual preview for verification.

## Features

- **Image-based generation** — Upload floor plan images and the skill visually analyzes them to identify rooms, corridors, entrances, and elevators, then generates waypoint coordinates in image-pixel space.
- **Text-based generation** — Describe your building layout in plain text and the skill generates SVG floor plan images along with the JSON configuration.
- **Visual preview** — Always generates an interactive overlay showing waypoints and connections on the floor plan so you can verify placement before deploying.
- **Multi-floor support** — Handles elevator and stairwell connections across floors with transport waypoints.
- **Validation** — Includes a validation script that checks bidirectional connections, graph connectivity, coordinate bounds, and cross-references.

## Installation

### Claude.ai (Web / Desktop / Mobile)

1. Download the latest release ZIP from the [Releases](https://github.com/RevelDigital/reveldigital-wayfinding-skill/releases) page, or [download the skill directly](https://github.com/RevelDigital/reveldigital-wayfinding-skill/raw/main/revel-wayfinding-skill.zip)
2. In Claude, go to **Settings → Features → Skills**
3. Click **Add Custom Skill** and upload the ZIP
4. Toggle the skill **ON**

> Requires **Code Execution** to be enabled in Settings → Capabilities.

### Claude Code (CLI)

Copy the skill folder into your personal or project skills directory:

```
# Personal skills (available in all projects)
cp -r revel-wayfinding-skill ~/.claude/skills/revel-wayfinding

# Or project-level skills (available only in this repo)
cp -r revel-wayfinding-skill .claude/skills/revel-wayfinding
```

### Team / Enterprise Provisioning

Organization Owners can provision this skill for all users:

1. Go to **Organization Settings → Skills**
2. Upload the ZIP to make it available org-wide

## Usage

Once installed, just ask Claude to generate a wayfinding configuration:

> *"Here's the floor plan for our office building. Can you generate a wayfinding configuration for our Revel Digital kiosk?"*

> *"We have a two-story medical clinic. Ground floor has a main lobby, reception, two exam rooms, and a waiting area. Second floor has four offices, a conference room, and a break room. There's an elevator connecting the floors."*

> *"Create a wayfinding floorplan JSON for this hospital floor plan image"*

Claude will analyze the floor plan, place waypoints, build the navigation graph, validate the output, and render a visual preview.

## Skill Contents

```
revel-wayfinding-skill/
├── SKILL.md                         # Main skill instructions
├── scripts/
│   └── validate.py                  # Floorplan JSON validator
└── references/
    └── floorplan-schema.json        # JSON Schema definition
```

## Output

The skill produces a `floorplan.json` file conforming to the [Wayfinding Floorplan Schema](https://reveldigital.github.io/wayfinding-app/floorplan-schema.json). See the [Configuration Guide](https://reveldigital.github.io/wayfinding-app/floorplan-schema.md) for full documentation.

## Validation

The included validation script checks the generated JSON for common issues:

```bash
python revel-wayfinding-skill/scripts/validate.py floorplan.json
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

## Related Resources

- [Revel Digital Wayfinding App](https://reveldigital.github.io/wayfinding-app/) — The wayfinding app that consumes the generated configuration
- [Floorplan Schema](https://reveldigital.github.io/wayfinding-app/floorplan-schema.json) — JSON Schema definition
- [Configuration Guide](https://reveldigital.github.io/wayfinding-app/floorplan-schema.md) — Full schema documentation
- [Revel Digital Gadget Skill](https://github.com/RevelDigital/reveldigital-gadget-skill) — Companion skill for scaffolding Revel Digital gadgets

## Building the .skill ZIP

To rebuild the distributable ZIP from source:

```
cd revel-wayfinding-skill
zip -r ../revel-wayfinding-skill.zip .
```

Or use the included build script:

```
./build.sh
```

## License

MIT — see [LICENSE](LICENSE) for details.
