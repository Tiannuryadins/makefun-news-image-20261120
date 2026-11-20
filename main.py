#!/usr/bin/env python3
"""The World in One Image — Friday, 20 November 2026.

Entry for make.fun competition news-image-20261120, "Sum up 20
November's world news in one image" ($250 shared by the top 50; entries
close Sunday 22 November 2026, 00:00 UTC = 07:00 WIB; bounty page
https://make.fun/bounty/news-image-20261120).

Running this file writes the newspaper poster that ships in this repo
(world_news_20_nov_2026.png) to /output/entry.png. The poster itself
was drawn at build time by render_poster.py with Pillow; this file does
nothing but copy its bytes, using the standard library alone. That
matters because the grader runs `python3 -P -s`, where no third-party
package exists, and because the program runs twice and must write the
same bytes both times — fixed bytes in, fixed bytes out.

The gate, checked here on every run with a small stdlib PNG reader: a
whole PNG of at most 1 MiB and 1024x1024 px. This poster is 1024x1024
and well under the byte cap.

    python3 main.py                  -> /output/entry.png
    python3 main.py out.png          -> the given path
    MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py

When /output cannot be created or written, ./output/entry.png is used.

The thirteen stories on the poster are the news of Friday, 20 November
2026 — Cyclone Akvan's landfall, Anthropic's Nasdaq debut, the PIF Tower
strike and ten more — each cross-checked against at least two sources
dated 20 November 2026; the full source table is in BUILD-TRANSCRIPT.md.
"""

import hashlib
import os
import struct
import sys
from pathlib import Path

POSTER = "world_news_20_nov_2026.png"
ENTRY = "entry.png"
MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024
SIGNATURE = b"\x89PNG\r\n\x1a\n"


class GateFailure(Exception):
    """The poster file is missing, broken, or over the gate."""


def read_poster_bytes():
    """Load the poster PNG that ships next to this file."""
    path = Path(__file__).resolve().parent / POSTER
    try:
        return path.read_bytes()
    except OSError as exc:
        raise GateFailure(f"cannot read {POSTER}: {exc}") from exc


def png_dimensions(blob):
    """Pull (width, height) out of the IHDR chunk, or raise GateFailure."""
    if blob[:8] != SIGNATURE or len(blob) < 33:
        raise GateFailure("not a valid PNG file")
    chunk_len, chunk_kind = struct.unpack(">I4s", blob[8:16])
    if chunk_kind != b"IHDR" or chunk_len != 13:
        raise GateFailure("PNG has no IHDR chunk first")
    return struct.unpack(">II", blob[16:24])


def check_gate(blob):
    """Return (width, height) or raise GateFailure when over the gate."""
    width, height = png_dimensions(blob)
    if len(blob) > MAX_BYTES:
        raise GateFailure(f"poster is {len(blob)} bytes, over the 1 MiB cap")
    if width > MAX_SIDE or height > MAX_SIDE:
        raise GateFailure(
            f"poster is {width}x{height}, over the 1024x1024 cap")
    return width, height


def pick_output(argv):
    """Decide where entry.png goes: argv, env dir, /output, ./output."""
    if len(argv) > 1:
        return Path(argv[1])
    for candidate in (os.environ.get("MAKEFUN_OUTPUT_DIR"), "/output"):
        if not candidate:
            continue
        try:
            os.makedirs(candidate, exist_ok=True)
            probe = Path(candidate) / ".makefun_write_test"
            probe.touch()
            probe.unlink()
            return Path(candidate) / ENTRY
        except OSError:
            continue
    fallback = Path.cwd() / "output"
    os.makedirs(fallback, exist_ok=True)
    return fallback / ENTRY


def run(argv):
    """Copy the poster to the output path and report what was written."""
    blob = read_poster_bytes()
    width, height = check_gate(blob)
    target = pick_output(argv)
    target.write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()[:16]
    print(f"wrote {target} — PNG {width}x{height}, {len(blob):,} bytes, "
          f"sha256={digest}...")
    return 0


def main(argv):
    try:
        return run(argv)
    except GateFailure as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
