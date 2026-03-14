---
name: revel-wayfinding
description: Generate Revel Digital wayfinding floorplan configurations from floor plan images or text descriptions. Use this skill whenever the user mentions wayfinding, floorplan configuration, indoor navigation, building directory, kiosk navigation, waypoint graphs, or needs to create a JSON configuration for the Revel Digital wayfinding app. Also trigger when the user uploads a floor plan image and wants to extract rooms/locations from it, or asks about building navigation paths, room-finding kiosks, or digital signage wayfinding. This skill handles both image-based analysis (user provides floor plan images) and text-based generation (user describes the building layout and the skill generates SVG floor plans). Always use this skill even if the user just says "wayfinding" or "floorplan" in the context of Revel Digital.
---

# Revel Digital Wayfinding Floorplan Generator

This skill generates complete JSON configurations for the [Revel Digital Wayfinding App](https://reveldigital.github.io/wayfinding-app/). The configuration defines building locations (rooms, offices, amenities) and a waypoint navigation graph overlaid on floor plan images so the app can render 3D wayfinding routes.

## Quick reference

- **JSON Schema**: Read `references/floorplan-schema.json` in this skill's directory for the full schema definition.
- **Validation**: Run `scripts/validate.py <output.json>` to check the generated configuration.
- **Live app**: https://reveldigital.github.io/wayfinding-app/

## Two input modes

### Mode 1: Image-based (user provides floor plan images)

The user uploads one or more floor plan images (PNG, JPG, SVG). You visually inspect each image to identify rooms, corridors, entrances, and elevators, then generate the JSON configuration with waypoints placed at estimated pixel coordinates.

### Mode 2: Text-based (user describes the building)

The user describes their building layout in text (e.g., "two floors, main lobby on ground floor, 6 offices on second floor"). You generate simple SVG floor plan images first, then use those as the basis for the JSON configuration.

---

## Workflow

### Step 1: Gather inputs

Determine which mode applies:

- **If images are provided**: View each uploaded image. Note the pixel dimensions using image inspection tools or metadata. Confirm the number of floors with the user.
- **If no images**: Ask the user to describe the building layout — number of floors, rooms per floor, room names/purposes, entrance location, elevator/stairwell locations. Then proceed to generate SVG floor plans (see "Generating SVG floor plans" below).

Ask the user for any additional context not visible on the floor plan:
- Room names, departments, or functions
- Hours of operation or descriptions
- Which entrance visitors use (for "You Are Here" placement)
- Elevator and stairwell locations (for multi-floor buildings)

### Step 2: Analyze the floor plan

For each floor, systematically work through the image:

1. **Determine image dimensions.** Use bash to check the pixel dimensions:
   ```bash
   # For PNG/JPG
   python3 -c "from PIL import Image; img = Image.open('/path/to/image'); print(img.size)"
   # For SVG, check the viewBox or width/height attributes
   ```
   These become the `imageSize` field `[width, height]`.

2. **Identify all labeled rooms.** Scan the image for room labels, numbers, and names. For each room, note:
   - Its name and room number
   - Its approximate position on the floor plan
   - Its category (Common, Office, Conference, Dining, Amenity, or Restricted)
   - An appropriate emoji icon

3. **Trace the corridor structure.** Identify the main corridors, hallways, and walkable paths. Note intersections, turns, and junctions — these are where corridor waypoints will go.

4. **Locate entrances and transport points.** Find the main building entrance (ground floor) and any elevators or stairwells that connect floors.

### Step 3: Place waypoints

This is the most critical step. Waypoints form the navigation graph that the app uses to compute walking routes. Coordinates are in **image-pixel space** where `(0, 0)` is the top-left corner, x increases rightward, y increases downward.

**Waypoint placement methodology:**

Use the image dimensions as your coordinate space. Estimate positions by dividing the image into a proportional grid.

For example, on a 1000×500 image:
- A room at the far left, vertically centered → approximately `(50, 250)`
- A room at the center-top → approximately `(500, 50)`
- The bottom-right corner → approximately `(950, 450)`

**Place waypoints in this order:**

1. **Entrance waypoint** — At the building entrance (door or lobby). This becomes `youAreHere` for the ground floor.

2. **Corridor waypoints** — At every corridor intersection, bend, or junction. Use naming convention: `f{floor}-cor-{position}` (e.g., `f1-cor-left`, `f1-cor-center`, `f1-cor-right`). Space these along the corridors to create smooth routing paths.

3. **Room waypoints** — At each room's entrance/doorway, where a person steps from the corridor into the room. Use naming convention: `f{floor}-{room-slug}` (e.g., `f1-lobby`, `f1-cafe`). Set each location's `waypointId` to match.

4. **Transport waypoints** — At elevators and stairwells. These must have `isTransport: true` and a `transportName`. Their `connections` array must include the paired waypoint ID on the other floor.

**Connection rules:**
- All connections are **bidirectional**. If waypoint A lists B in connections, then B must also list A.
- Room waypoints connect to their nearest corridor waypoint (usually just one connection).
- Corridor waypoints connect to adjacent corridor waypoints and any room waypoints along that corridor segment.
- Transport waypoints connect to both their local corridor waypoint AND their cross-floor counterpart.

**Coordinate estimation tips:**
- Divide the floor plan visually into quadrants or a grid to anchor your estimates.
- Corridors in architectural plans are typically narrow — place corridor waypoints along the centerline.
- Room waypoints go at the doorway, not the center of the room.
- For long straight corridors, place waypoints every ~20% of the corridor length to create smooth paths.
- Keep at least a small margin from image edges (10-20px).

### Step 4: Build the JSON

Assemble the complete configuration with two top-level arrays:

```json
{
  "locations": [ ... ],
  "floors": [ ... ]
}
```

**Location entry format:**
```json
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
```

Categories: `Common`, `Office`, `Conference`, `Dining`, `Amenity`, `Restricted`

**Floor entry format:**
```json
{
  "floor": "1",
  "label": "Floor 1 — Ground",
  "image": "https://example.com/floorplan-f1.svg",
  "imageSize": [1000, 500],
  "youAreHere": "f1-entrance",
  "waypoints": [ ... ]
}
```

**Waypoint format:**
```json
{ "id": "f1-lobby", "x": 100, "y": 195, "connections": ["f1-cor-left"] }
```

**Transport waypoint format:**
```json
{ "id": "f1-elev", "x": 240, "y": 250, "connections": ["f1-cor-left", "f2-elev"], "isTransport": true, "transportName": "Main Elevator" }
```

**Image URL note:** The `image` field requires a publicly accessible URL. If the user hasn't hosted their images yet, use a placeholder URL like `https://example.com/floorplan-f1.png` and remind them to replace it with the actual hosted URL before deploying.

### Step 5: Validate

Run the validation script against the generated JSON:

```bash
python3 /path/to/skill/scripts/validate.py /path/to/output.json
```

The script checks:
- No duplicate location or waypoint IDs
- All location floor references exist
- All waypointId references exist in the correct floor
- All youAreHere references exist
- Bidirectional connections
- Transport waypoint completeness
- Coordinate bounds
- Graph connectivity (every room reachable from youAreHere)

Fix any errors before proceeding.

### Step 6: Generate the visual preview

**Always generate a visual preview** so the user can verify waypoint placement. Create a React artifact (`.jsx`) that renders each floor plan with the waypoint graph overlaid.

The preview should show:
- The floor plan image as a background (or a placeholder rectangle if no image URL is available yet)
- Waypoints as labeled circles at their `(x, y)` positions
- Connection lines between connected waypoints
- Room waypoints in one color (e.g. blue), corridor waypoints in another (e.g. gray), transport waypoints in a third (e.g. orange)
- The "You Are Here" waypoint highlighted (e.g. green with a star)
- Waypoint IDs as small labels
- Floor selector tabs for multi-floor buildings

The preview helps the user spot misplaced waypoints, missing connections, or unreachable areas before deploying.

**Preview implementation pattern:**

```jsx
// Use React with useState for floor selection
// Parse the generated JSON configuration
// For each floor, render an SVG overlay on top of the floor plan image
// Draw connection lines first (so they appear behind waypoint circles)
// Draw waypoint circles with color coding by type
// Add ID labels near each waypoint
// Include a floor selector if multiple floors exist
```

Use the Visualizer tool if available for inline previews, or create a React artifact for a richer interactive experience. Either way, the preview is mandatory — never skip it.

### Step 7: Deliver outputs

1. Save the JSON configuration to `/mnt/user-data/outputs/floorplan.json`
2. Present the file to the user
3. Show the visual preview artifact
4. Summarize what was generated: number of floors, locations, and waypoints
5. Remind the user about image hosting if placeholder URLs were used
6. Note that waypoint coordinates are best-effort estimates from visual analysis and may need fine-tuning

---

## Generating SVG floor plans (text-based mode)

When the user describes a building layout without providing images, generate clean SVG floor plan images:

1. **Determine layout.** Based on the user's description, decide on room arrangement, corridor paths, and overall building shape.

2. **Choose dimensions.** Use a standard aspect ratio like 1000×500 or 1200×600 pixels. Keep it simple.

3. **Draw the SVG.** Create a clean architectural-style floor plan with:
   - Outer building walls (thick lines)
   - Room boundaries (thinner lines)
   - Room labels (room number and/or name)
   - Corridor space (unlabeled open areas between rooms)
   - Door openings (small gaps in room walls)
   - Elevator/stairwell indicators if multi-floor

4. **Style guidelines:**
   - White background, dark gray or black walls
   - Room fills in a very light color (e.g. `#f8f9fa`) or white
   - Text labels in a readable sans-serif font, sized appropriately
   - Minimum room size roughly 80×60 pixels to fit labels

5. **Save the SVG** to `/mnt/user-data/outputs/` (one per floor, e.g. `floorplan-f1.svg`, `floorplan-f2.svg`).

6. **Use the SVG dimensions** as the `imageSize` in the JSON configuration.

After generating the SVGs, proceed with the normal waypoint placement workflow (Step 3 onward), using the SVG you just created as the reference image.

---

## Multi-floor buildings

For buildings with multiple floors:

- Each floor gets its own entry in `floors` with its own image and waypoint graph.
- Floors connect via transport waypoints (elevators, stairwells).
- A transport waypoint on floor 1 includes the ID of its counterpart on floor 2 in `connections`, and vice versa.
- Both paired transport waypoints must have `isTransport: true` and matching `transportName`.
- On the ground floor, `youAreHere` is typically the main entrance.
- On upper floors, `youAreHere` is typically the elevator or stairwell landing.

---

## Validation checklist

Before delivering the configuration, verify:

- [ ] Every location's `floor` matches a floor entry
- [ ] Every location's `waypointId` matches a waypoint in the correct floor
- [ ] Every floor's `youAreHere` matches a waypoint in that floor
- [ ] All connections are bidirectional
- [ ] Transport waypoints have `isTransport: true` and `transportName`
- [ ] Transport pairs reference each other across floors
- [ ] `imageSize` matches actual image dimensions
- [ ] Waypoint coordinates are within image bounds
- [ ] The graph is fully connected (every room reachable from youAreHere)
- [ ] No duplicate IDs anywhere

---

## Common mistakes to avoid

- **Forgetting bidirectional connections.** If A→B exists, B→A must also exist. This is the most common error.
- **Transport waypoints without cross-floor connections.** An elevator waypoint on floor 1 must list the floor 2 elevator waypoint in its connections.
- **Waypoints outside image bounds.** Coordinates must be within `[0, imageSize[0])` × `[0, imageSize[1])`.
- **Disconnected subgraphs.** Every room waypoint must be reachable from the `youAreHere` starting point. Use the validation script to catch this.
- **Mismatched floor references.** The `floor` value in a location must exactly match the `floor` value of a floor entry (string comparison).
- **Missing waypointId.** Every location should have a `waypointId` so the app can route to it. Without this, the location appears in search but can't be navigated to.
