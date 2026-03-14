#!/usr/bin/env python3
"""
Validate a Revel Digital wayfinding floorplan JSON configuration.

Checks:
  1. JSON structure matches schema requirements
  2. All location floor references exist in floors array
  3. All location waypointId references exist in their floor's waypoints
  4. All floor youAreHere references exist in that floor's waypoints
  5. All waypoint connections are bidirectional
  6. Transport waypoints have required fields and cross-floor pairing
  7. Waypoint coordinates are within image bounds
  8. Navigation graph is fully connected per floor (every room reachable from youAreHere)
  9. No duplicate IDs

Usage:
  python validate.py <path-to-floorplan.json>
"""

import json
import sys
from collections import deque


def validate(config):
    errors = []
    warnings = []

    locations = config.get("locations", [])
    floors = config.get("floors", [])

    if not locations:
        errors.append("No locations defined.")
    if not floors:
        errors.append("No floors defined.")

    floor_map = {}
    for f in floors:
        fid = f.get("floor", "")
        if fid in floor_map:
            errors.append(f"Duplicate floor ID: '{fid}'")
        floor_map[fid] = f

    # -- Location checks --
    location_ids = set()
    for loc in locations:
        lid = loc.get("id", "")
        if lid in location_ids:
            errors.append(f"Duplicate location ID: '{lid}'")
        location_ids.add(lid)

        floor_ref = loc.get("floor", "")
        if floor_ref not in floor_map:
            errors.append(
                f"Location '{loc.get('name', lid)}' references floor '{floor_ref}' which does not exist."
            )

        wp_ref = loc.get("waypointId")
        if wp_ref and floor_ref in floor_map:
            wp_ids = {wp["id"] for wp in floor_map[floor_ref].get("waypoints", [])}
            if wp_ref not in wp_ids:
                errors.append(
                    f"Location '{loc.get('name', lid)}' references waypointId '{wp_ref}' "
                    f"not found in floor '{floor_ref}' waypoints."
                )

        valid_categories = {"Common", "Office", "Conference", "Dining", "Amenity", "Restricted"}
        cat = loc.get("category", "")
        if cat not in valid_categories:
            errors.append(
                f"Location '{loc.get('name', lid)}' has invalid category '{cat}'. "
                f"Must be one of: {', '.join(sorted(valid_categories))}"
            )

    # -- Floor / waypoint checks --
    all_waypoint_ids = {}  # global map: wp_id -> floor_id

    for f in floors:
        fid = f.get("floor", "")
        waypoints = f.get("waypoints", [])
        wp_map = {}

        image_size = f.get("imageSize", [0, 0])
        img_w = image_size[0] if len(image_size) > 0 else 0
        img_h = image_size[1] if len(image_size) > 1 else 0

        if img_w <= 0 or img_h <= 0:
            errors.append(f"Floor '{fid}' has invalid imageSize: {image_size}")

        for wp in waypoints:
            wid = wp.get("id", "")
            if wid in wp_map:
                errors.append(f"Floor '{fid}' has duplicate waypoint ID: '{wid}'")
            wp_map[wid] = wp
            all_waypoint_ids[wid] = fid

            x, y = wp.get("x", 0), wp.get("y", 0)
            if img_w > 0 and (x < 0 or x >= img_w):
                warnings.append(
                    f"Waypoint '{wid}' x={x} is outside image width [0, {img_w}) on floor '{fid}'."
                )
            if img_h > 0 and (y < 0 or y >= img_h):
                warnings.append(
                    f"Waypoint '{wid}' y={y} is outside image height [0, {img_h}) on floor '{fid}'."
                )

        # youAreHere check
        yah = f.get("youAreHere", "")
        if yah and yah not in wp_map:
            errors.append(
                f"Floor '{fid}' youAreHere '{yah}' not found in its waypoints."
            )

        # Bidirectional connection check (within floor)
        for wp in waypoints:
            wid = wp["id"]
            for conn in wp.get("connections", []):
                if conn in wp_map:
                    peer_conns = wp_map[conn].get("connections", [])
                    if wid not in peer_conns:
                        errors.append(
                            f"Floor '{fid}': waypoint '{wid}' connects to '{conn}' "
                            f"but '{conn}' does not connect back to '{wid}'."
                        )

        # Transport waypoint checks
        for wp in waypoints:
            if wp.get("isTransport"):
                if not wp.get("transportName"):
                    errors.append(
                        f"Transport waypoint '{wp['id']}' on floor '{fid}' is missing 'transportName'."
                    )

        # Graph connectivity check from youAreHere
        if yah and yah in wp_map:
            visited = set()
            queue = deque([yah])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                if current in wp_map:
                    for conn in wp_map[current].get("connections", []):
                        if conn in wp_map and conn not in visited:
                            queue.append(conn)

            # Check that all room waypoints are reachable
            room_wps = set()
            for loc in locations:
                if loc.get("floor") == fid and loc.get("waypointId"):
                    room_wps.add(loc["waypointId"])

            unreachable = room_wps - visited
            if unreachable:
                errors.append(
                    f"Floor '{fid}': the following room waypoints are unreachable from "
                    f"youAreHere '{yah}': {', '.join(sorted(unreachable))}"
                )

    # Cross-floor transport pairing
    for f in floors:
        for wp in f.get("waypoints", []):
            if wp.get("isTransport"):
                for conn in wp.get("connections", []):
                    if conn not in all_waypoint_ids:
                        # Could be a cross-floor reference that's missing
                        if conn not in {w["id"] for w in f.get("waypoints", [])}:
                            errors.append(
                                f"Transport waypoint '{wp['id']}' connects to '{conn}' "
                                f"which does not exist in any floor."
                            )

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate.py <floorplan.json>")
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"INVALID JSON: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"File not found: {path}")
        sys.exit(1)

    errors, warnings = validate(config)

    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"\n❌ {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n✅ Validation passed. No errors found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
