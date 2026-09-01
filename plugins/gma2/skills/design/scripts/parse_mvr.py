#!/usr/bin/env python3
"""Read an MVR (My Virtual Rig) file into a flat, inspectable rig map.

An `.mvr` is a zip whose `GeneralSceneDescription.xml` describes every fixture
in the rig: its Fixture ID, GDTF profile, DMX address, and — the part no other
source gives you — its position in 3D space. That geometry is what turns "the
back truss" from a guess into a fact, so a lighting design can talk about
symmetry, depth layers and sweep direction instead of hand-waving.

It NEVER touches the console — it only reads a file and prints. Every console
write goes through the gma2 MCP, same as the other gma2 skills.

Usage
-----
    # Human-readable rig table + zone proposal + sanity warnings
    python3 parse_mvr.py rig.mvr --dump

    # Proposed fixture groups (type x depth band), as MA2-ready ID ranges
    python3 parse_mvr.py rig.mvr --groups

    # Structured output
    python3 parse_mvr.py rig.mvr --json

Coordinates
-----------
Positions come from each fixture's `<Matrix>`; the 4th bracket is the
translation, **in millimetres**, which this script converts to metres.

The axis convention is ASSUMED to be the common MVR one:

    X = lateral   (positive = one side of centre; which side is rig-dependent)
    Y = depth     (positive = upstage / away from audience)
    Z = height    (positive = up)

**Verify this before trusting the zone labels.** `--dump` prints the raw range
of each axis precisely so it can be checked against the real rig: if the front
truss reports a *larger* Y than the back truss, the depth sign is flipped —
pass `--flip-depth`. If the rig was modelled with Y up and Z depth (some CAD
exports), pass `--swap-yz`.

Known limitation: a fixture nested inside a `<GroupObject>` that carries its own
non-identity transform would need the parent matrices composed onto it. This
script uses each fixture's own matrix and WARNS when a parent group carries a
non-identity translation, rather than silently reporting a wrong position.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict, field

# Matrix text looks like {a,b,c}{d,e,f}{g,h,i}{x,y,z} — 3 basis rows then the
# translation. Whitespace varies between exporters, so parse the brackets.
_BRACKET = re.compile(r"\{([^}]*)\}")

# A gap in a sorted axis wider than this (metres) starts a new band; the range
# fraction keeps it sane on both tiny club rigs and stadium rigs.
_MIN_GAP_M = 0.75
_GAP_RANGE_FRACTION = 0.22


@dataclass
class Fixture:
    fid: int | None          # console Fixture ID (the number the desk selects by)
    name: str
    layer: str               # MVR layer — usually the truss / position name
    gdtf: str                # GDTF profile filename (fixture type)
    mode: str
    universe: int | None
    channel: int | None
    x: float | None          # metres, see Coordinates above
    y: float | None
    z: float | None

    @property
    def type_key(self) -> str:
        """Fixture type identity for grouping — profile plus mode."""
        return f"{self.gdtf}|{self.mode}" if self.mode else self.gdtf


@dataclass
class RigMap:
    fixtures: list[Fixture] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _parse_matrix(text: str | None) -> tuple[float, float, float] | None:
    """Return the translation (x, y, z) in metres, or None if unparseable."""
    if not text:
        return None
    groups = _BRACKET.findall(text)
    if len(groups) < 4:
        return None
    try:
        vals = [float(v) for v in groups[3].split(",")]
    except ValueError:
        return None
    if len(vals) != 3:
        return None
    return tuple(round(v / 1000.0, 3) for v in vals)  # mm -> m


def _parse_address(fixture_el: ET.Element) -> tuple[int | None, int | None]:
    """MVR stores an absolute DMX address; split it into universe + channel."""
    addr_el = fixture_el.find("./Addresses/Address")
    if addr_el is None or not (addr_el.text or "").strip():
        return None, None
    try:
        absolute = int(float(addr_el.text.strip()))
    except ValueError:
        return None, None
    return absolute // 512 + 1, absolute % 512 + 1


def _int_or_none(text: str | None) -> int | None:
    if text is None or not text.strip():
        return None
    try:
        return int(float(text.strip()))
    except ValueError:
        return None


def _walk(el: ET.Element, layer: str, rig: RigMap, group_path: str = "") -> None:
    """Recurse a ChildList, collecting Fixtures and flagging nested transforms."""
    for child in el:
        if child.tag == "Fixture":
            pos = _parse_matrix(child.findtext("Matrix"))
            universe, channel = _parse_address(child)
            rig.fixtures.append(Fixture(
                fid=_int_or_none(child.findtext("FixtureID")),
                name=(child.get("name") or child.findtext("Name") or "").strip(),
                layer=group_path or layer,
                gdtf=(child.findtext("GDTFSpec") or "").strip(),
                mode=(child.findtext("GDTFMode") or "").strip(),
                universe=universe,
                channel=channel,
                x=pos[0] if pos else None,
                y=pos[1] if pos else None,
                z=pos[2] if pos else None,
            ))
        elif child.tag in ("GroupObject", "SceneObject"):
            gname = (child.get("name") or "").strip()
            offset = _parse_matrix(child.findtext("Matrix"))
            if offset and any(abs(v) > 0.001 for v in offset):
                rig.warnings.append(
                    f"group '{gname or child.tag}' carries a non-identity offset "
                    f"{offset} — its fixtures' positions may be relative to it, "
                    f"not to the world. Verify those fixtures against the plot."
                )
            sub = child.find("ChildList")
            if sub is not None:
                _walk(sub, layer, rig, f"{layer}/{gname}" if gname else layer)


def read_mvr(path: str) -> RigMap:
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist()
                 if n.lower().endswith("generalscenedescription.xml")]
        if not names:
            raise SystemExit(f"{path}: no GeneralSceneDescription.xml inside "
                             f"(is this really an MVR?)")
        xml = zf.read(names[0])
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise SystemExit(f"{path}: {names[0]} is not well-formed XML ({e}). The "
                         f"MVR is likely corrupt or was written by a broken "
                         f"exporter — re-export it before relying on it.")
    rig = RigMap()
    for layer in root.iter("Layer"):
        lname = (layer.get("name") or layer.findtext("Name") or "").strip()
        children = layer.find("ChildList")
        if children is not None:
            _walk(children, lname or "(unnamed layer)", rig)
    if not rig.fixtures:
        rig.warnings.append("no <Fixture> elements found — the MVR may be empty "
                            "or use a structure this parser doesn't cover.")
    return rig


def apply_axes(rig: RigMap, flip_depth: bool, swap_yz: bool) -> None:
    """Normalise to X=lateral, Y=depth(+upstage), Z=height per the flags."""
    for f in rig.fixtures:
        if f.y is None or f.z is None:
            continue
        if swap_yz:
            f.y, f.z = f.z, f.y
        if flip_depth:
            f.y = -f.y


def band(values: list[float]) -> list[tuple[float, float]]:
    """Split sorted values into bands wherever a gap is 'large'.

    Transparent on purpose: a band break is just a gap wider than the threshold,
    so the result can be explained to (and overruled by) a human, unlike an
    opaque clustering fit.
    """
    vals = sorted(values)
    if not vals:
        return []
    span = vals[-1] - vals[0]
    threshold = max(_MIN_GAP_M, span * _GAP_RANGE_FRACTION)
    bands, start, prev = [], vals[0], vals[0]
    for v in vals[1:]:
        if v - prev > threshold:
            bands.append((start, prev))
            start = v
        prev = v
    bands.append((start, prev))
    return bands


def band_of(value: float, bands: list[tuple[float, float]]) -> int:
    for i, (lo, hi) in enumerate(bands):
        if lo - 1e-6 <= value <= hi + 1e-6:
            return i
    return len(bands) - 1


def depth_labels(n: int) -> list[str]:
    """Names for depth bands, front (audience side) to back."""
    if n <= 1:
        return ["stage"]
    if n == 2:
        return ["front", "back"]
    if n == 3:
        return ["front", "mid", "back"]
    return ["front"] + [f"mid{i}" for i in range(1, n - 1)] + ["back"]


def side_of(x: float, span: float) -> str:
    """Lateral third: L / C / R relative to the rig's own centre."""
    if span < 1e-6:
        return "C"
    if x < -span * 0.18:
        return "L"
    if x > span * 0.18:
        return "R"
    return "C"


def zones(rig: RigMap) -> dict:
    placed = [f for f in rig.fixtures if f.y is not None]
    if not placed:
        return {}
    ys = [f.y for f in placed]
    xs = [f.x for f in placed if f.x is not None]
    y_bands = band(ys)
    labels = depth_labels(len(y_bands))
    x_span = (max(xs) - min(xs)) if xs else 0.0
    x_mid = (max(xs) + min(xs)) / 2 if xs else 0.0
    out = {}
    for f in placed:
        depth = labels[band_of(f.y, y_bands)]
        side = side_of((f.x - x_mid) if f.x is not None else 0.0, x_span)
        out[id(f)] = {"depth": depth, "side": side}
    return out


def ranges(rig: RigMap) -> dict:
    out = {}
    for axis in ("x", "y", "z"):
        vals = [getattr(f, axis) for f in rig.fixtures if getattr(f, axis) is not None]
        out[axis] = {"min": min(vals), "max": max(vals)} if vals else None
    return out


def fmt_range(r: dict | None) -> str:
    return f"{r['min']:+.2f} .. {r['max']:+.2f} m" if r else "—"


def id_ranges(fids: list[int]) -> str:
    """Collapse [101,102,103,107] into '101 Thru 103 + 107' for MA2 selection."""
    if not fids:
        return "—"
    fids = sorted(set(fids))
    parts, start, prev = [], fids[0], fids[0]
    for v in fids[1:]:
        if v != prev + 1:
            parts.append((start, prev))
            start = v
        prev = v
    parts.append((start, prev))
    return " + ".join(f"{a} Thru {b}" if a != b else f"{a}" for a, b in parts)


def dump(rig: RigMap, z: dict) -> None:
    print(f"{len(rig.fixtures)} fixtures\n")
    print("axis ranges (VERIFY these against the real rig before trusting zones)")
    r = ranges(rig)
    print(f"  X lateral : {fmt_range(r['x'])}")
    print(f"  Y depth   : {fmt_range(r['y'])}   (+ should be UPSTAGE / away from audience)")
    print(f"  Z height  : {fmt_range(r['z'])}   (+ should be UP)")
    print()
    hdr = f"{'FID':>5}  {'type':<34} {'layer':<18} {'zone':<12} {'x':>7} {'y':>7} {'z':>7}  addr"
    print(hdr)
    print("-" * len(hdr))
    for f in sorted(rig.fixtures, key=lambda f: (f.fid is None, f.fid or 0)):
        zn = z.get(id(f))
        zone = f"{zn['depth']}/{zn['side']}" if zn else "—"
        addr = f"{f.universe}.{f.channel}" if f.universe else "—"
        gd = f.gdtf.replace(".gdtf", "")[:34]
        print(f"{(f.fid if f.fid is not None else '?'):>5}  {gd:<34} {f.layer[:18]:<18} "
              f"{zone:<12} {_n(f.x):>7} {_n(f.y):>7} {_n(f.z):>7}  {addr}")
    if rig.warnings:
        print("\nwarnings")
        for w in rig.warnings:
            print(f"  ! {w}")


def _n(v: float | None) -> str:
    return f"{v:+.2f}" if v is not None else "—"


def groups(rig: RigMap, z: dict) -> None:
    """Propose fixture groups: one per (type, depth band), split L/C/R too."""
    buckets: dict[tuple, list[int]] = {}
    for f in rig.fixtures:
        if f.fid is None:
            continue
        zn = z.get(id(f))
        depth = zn["depth"] if zn else "unplaced"
        buckets.setdefault((f.gdtf.replace(".gdtf", ""), depth), []).append(f.fid)

    print("proposed groups — type x depth band\n")
    for (gd, depth), fids in sorted(buckets.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print(f"  {depth:<8} {gd:<32} {len(fids):>3} fx   {id_ranges(fids)}")

    print("\nproposed groups — lateral split (for symmetric sweeps / L-R chases)\n")
    side_buckets: dict[tuple, list[int]] = {}
    for f in rig.fixtures:
        if f.fid is None:
            continue
        zn = z.get(id(f))
        if not zn:
            continue
        side_buckets.setdefault((zn["depth"], zn["side"]), []).append(f.fid)
    for (depth, side), fids in sorted(side_buckets.items()):
        print(f"  {depth:<8} {side:<3} {len(fids):>3} fx   {id_ranges(fids)}")

    print("\nThese are geometry-derived proposals, not lighting roles. Naming them "
          "(face / side / back / beam) is a design decision — confirm with the user "
          "against the plot before creating any group on the console.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mvr")
    ap.add_argument("--dump", action="store_true", help="human-readable rig table")
    ap.add_argument("--groups", action="store_true", help="propose fixture groups")
    ap.add_argument("--json", action="store_true", help="structured output")
    ap.add_argument("--flip-depth", action="store_true",
                    help="negate Y (use when the front truss reports a larger Y)")
    ap.add_argument("--swap-yz", action="store_true",
                    help="swap Y and Z (use when the model was built Y-up)")
    args = ap.parse_args()

    rig = read_mvr(args.mvr)
    apply_axes(rig, args.flip_depth, args.swap_yz)
    z = zones(rig)

    if args.json:
        out = []
        for f in rig.fixtures:
            d = asdict(f)
            zn = z.get(id(f))
            d["depth"] = zn["depth"] if zn else None
            d["side"] = zn["side"] if zn else None
            out.append(d)
        json.dump({"fixtures": out, "ranges": ranges(rig), "warnings": rig.warnings},
                  sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    if args.groups:
        groups(rig, z)
        return

    dump(rig, z)


if __name__ == "__main__":
    main()
