#!/usr/bin/env python3
"""Resolve named grandMA2 fixture functions to per-type (attribute, At%) values.

grandMA2's Telnet interface cannot read a fixture profile's channel-function
ranges, so values like "Strobe Fast" / "Iris Closed" / "wide" / "gobo 1.3" are
fixture-type specific. That information IS in the MA2 fixture-type XML: every
channel's functions, percent ranges, and named DMX channel-sets.

This script parses those XMLs (no third-party deps — stdlib `xml` only) and:
  * `--dump`     : prints each fixture's channels grouped by preset type, with
                   every named ChannelSet and its DMX mid-percent (the value to
                   send via `At`). Use this to design a palette by eye.
  * `--queries`  : resolves a JSON list of named functions across all fixtures,
                   returning {label: {fixture_key: [attribute, at_percent]}} —
                   exactly what you merge into one Global preset across types.

Percent values are 0..100 (grandMA2 `At` maps 0-100% across the channel's DMX
range), so a named slot resolves to its DMX midpoint as a percentage.

Usage:
  python profile_palette.py FIXTURE1.xml [FIXTURE2.xml ...] --dump
  python profile_palette.py *.xml --queries '[{"query":"max Strobe","feature":"SHUTTER"},
                                               {"query":"wide","feature":"FOCUS"},
                                               {"query":"4 facet prism"}]'
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _descendants(elem, local):
    return [e for e in elem.iter() if _local(e.tag) == local]


def _children(elem, local):
    return [e for e in list(elem) if _local(e.tag) == local]


def _to_int(v):
    return int(round(float(v))) if v is not None else 0


# Query -> case-insensitive substrings that satisfy it.
_ALIASES = {
    "closed": ["closed", "close"],
    "open": ["open"],
    "random": ["random", "rnd"],
    "strobe": ["strobe"],
    "prism": ["prism", "prisma"],
}
_BAND_QUERIES = {"strobe"}            # resolved as a position within a range
_SHUTTER_SCOPED = {"open", "closed", "strobe", "random"}  # auto-scope to SHUTTER


def _is_random(hay: str) -> bool:
    return "random" in hay or "rnd" in hay


class Profile:
    def __init__(self, name, mode, functions, features):
        self.name = name          # e.g. "Fine 600L BSWF"
        self.mode = mode
        self.functions = functions  # {attribute: [func, ...]}
        self.features = features    # {attribute: feature}

    def _attrs(self, feature):
        for attr, funcs in self.functions.items():
            if feature is None or self.features.get(attr, "").upper() == feature:
                yield attr, funcs

    def resolve(self, query, position=0.5, feature=None):
        """Return (attribute, at_percent) or None."""
        q = query.strip().lower()
        needles = _ALIASES.get(q, [q])
        if feature is None and q in _SHUTTER_SCOPED:
            feature = "SHUTTER"

        # 1. Band query (e.g. strobe): position within the matching function.
        if q in _BAND_QUERIES:
            for attr, funcs in self._attrs(feature):
                for f in funcs:
                    hay = f"{f['name']} {f['sub']}".lower()
                    if any(n in hay for n in needles) and not _is_random(hay):
                        val = f["from"] + position * (f["to"] - f["from"])
                        return attr, round(val, 3)
            return None

        # 2. Named slot: a ChannelSet whose name matches (precise DMX midpoint).
        for attr, funcs in self._attrs(feature):
            for f in funcs:
                for cs in f["sets"]:
                    if any(n in cs["name"].lower() for n in needles):
                        mid = (cs["from"] + cs["to"]) / 2 / 255 * 100
                        return attr, round(mid, 3)

        # 3. Fallback: attribute or function name match -> positioned in range.
        for attr, funcs in self._attrs(feature):
            if any(n in attr.lower() for n in needles) and funcs:
                f = funcs[0]
                return attr, round(f["from"] + position * (f["to"] - f["from"]), 3)
            for f in funcs:
                hay = f"{f['name']} {f['sub']}".lower()
                if any(n in hay for n in needles):
                    return attr, round(f["from"] + position * (f["to"] - f["from"]), 3)
        return None


def parse(path: str) -> Profile:
    root = ET.parse(path).getroot()
    ft = next(iter(_descendants(root, "FixtureType")), None)
    if ft is None:
        raise ValueError(f"No <FixtureType> in {path}")
    functions, features = {}, {}
    for ct in _descendants(ft, "ChannelType"):
        attr = ct.get("attribute")
        if not attr:
            continue
        if ct.get("feature"):
            features.setdefault(attr, ct.get("feature"))
        for cf in _children(ct, "ChannelFunction"):
            if cf.get("from") is None or cf.get("to") is None:
                continue
            sets = [
                {"name": cs.get("name") or "", "from": _to_int(cs.get("from_dmx")),
                 "to": _to_int(cs.get("to_dmx"))}
                for cs in _children(cf, "ChannelSet")
            ]
            functions.setdefault(attr, []).append({
                "name": cf.get("name") or "", "sub": cf.get("subattribute") or "",
                "from": float(cf.get("from")), "to": float(cf.get("to")), "sets": sets,
            })
    return Profile(ft.get("name") or "", ft.get("mode") or "", functions, features)


def dump(profiles):
    out = {}
    for p in profiles:
        chans = []
        for attr, funcs in p.functions.items():
            sets = []
            for f in funcs:
                for cs in f["sets"]:
                    if cs["name"]:
                        mid = round((cs["from"] + cs["to"]) / 2 / 255 * 100, 2)
                        sets.append({"name": cs["name"], "at_percent": mid})
            chans.append({"attribute": attr, "feature": p.features.get(attr, ""), "sets": sets})
        out[p.name] = {"mode": p.mode, "channels": chans}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xml", nargs="+", help="fixture-type XML path(s)")
    ap.add_argument("--dump", action="store_true", help="print full capability map")
    ap.add_argument("--queries", help="JSON list of {query, position?, feature?}")
    args = ap.parse_args()

    profiles = [parse(x) for x in args.xml]

    if args.queries:
        specs = json.loads(args.queries)
        result = {}
        for spec in specs:
            label = spec.get("label", spec["query"])
            per = {}
            for p in profiles:
                r = p.resolve(spec["query"], spec.get("position", 0.5), spec.get("feature"))
                if r is not None:
                    per[p.name] = [r[0], r[1]]
            result[label] = per
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    else:  # default to dump
        json.dump(dump(profiles), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
