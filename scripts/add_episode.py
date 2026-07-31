#!/usr/bin/env python3
"""Add a new episode to podcast.xml and update latest.mp3.

Usage (run from the repo root):
  python3 scripts/add_episode.py <mp3_path> <YYYY-MM-DD> "<title>" "<description>"

- Copies the mp3 to episodes/briefing-<date>.mp3 and to latest.mp3
- Inserts a new <item> right after the <!-- EPISODES --> marker
- Computes enclosure length (bytes) and itunes:duration (seconds, via ffprobe)
- Skips insertion if a guid for that date already exists (idempotent)
"""
import shutil, subprocess, sys, html
from datetime import datetime, timezone, timedelta
from pathlib import Path

def main():
    mp3_path, date_str, title, description = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    root = Path(__file__).resolve().parent.parent
    dest = root / "episodes" / f"briefing-{date_str}.mp3"
    dest.parent.mkdir(exist_ok=True)
    shutil.copy(mp3_path, dest)
    shutil.copy(mp3_path, root / "latest.mp3")

    feed = root / "podcast.xml"
    xml = feed.read_text(encoding="utf-8")
    guid = f"synpod-{date_str}"
    if guid in xml:
        print(f"guid {guid} already present; episode files updated, feed unchanged")
        return

    size = dest.stat().st_size
    try:
        dur = int(float(subprocess.check_output(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(dest)]).decode().strip()))
    except Exception:
        dur = 0

    d = datetime.strptime(date_str, "%Y-%m-%d").replace(
        hour=7, minute=30, tzinfo=timezone(timedelta(hours=-4)))
    pub = d.strftime("%a, %d %b %Y %H:%M:%S %z")

    item = f"""    <item>
      <title>{html.escape(title)}</title>
      <description>{html.escape(description)}</description>
      <pubDate>{pub}</pubDate>
      <enclosure url="https://renetec.github.io/synpod/episodes/briefing-{date_str}.mp3" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{guid}</guid>
      <itunes:duration>{dur}</itunes:duration>
    </item>"""

    marker = "<!-- EPISODES -->"
    xml = xml.replace(marker, marker + "\n" + item, 1)
    feed.write_text(xml, encoding="utf-8")
    print(f"added episode {guid} ({size} bytes, {dur}s)")

if __name__ == "__main__":
    main()
