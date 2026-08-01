#!/usr/bin/env python3
"""Generate app/src/main/assets/permissions/known_permissions.json.

Source data: `pm list permissions -f -u` dump from a real device (requires
root/adb shell). The bundled JSON is a *fallback* for permissions whose
defining package is not installed on the device running LibChecker; live
system resolution via PackageManager.getPermissionInfo() always takes
precedence at runtime.

Usage:
  adb shell pm list permissions -f -u > dump.txt
  python3 tools/generate_known_permissions.py dump.txt \
      app/src/main/assets/permissions/known_permissions.json
"""

import json
import re
import sys


# Hand-curated entries merged into the generated output. Only add permissions
# whose name and defining package are verified from public sources.
MANUAL_ENTRIES = {
    # ASUS MSA SupplementaryDID service (OAID / 移动安全联盟匿名设备标识),
    # service action com.asus.msa.action.ACCESS_DID.
    "com.asus.msa.SupplementaryDID.ACCESS": {
        "label": "访问 ASUS 补充设备标识 (OAID)",
        "source": "com.asus.msa.SupplementaryDID",
    },
}


def parse_dump(text: str) -> dict:
    entries: dict[str, dict] = {}
    current: str | None = None
    for line in text.splitlines():
        m = re.match(r"\+ permission:(\S+)", line)
        if m:
            current = m.group(1)
            entries[current] = {}
            continue
        if current is None:
            continue
        m = re.match(r"\s+(package|label|description|protectionLevel):(.*)", line)
        if m:
            entries[current][m.group(1)] = m.group(2).strip()
    return entries


def main() -> None:
    dump_path, out_path = sys.argv[1], sys.argv[2]
    with open(dump_path, encoding="utf-8") as f:
        entries = parse_dump(f.read())

    perms = {}
    for name, entry in entries.items():
        label = entry.get("label")
        desc = entry.get("description")
        if label in (None, "null", "") and desc in (None, "null", ""):
            continue
        item = {}
        if label not in (None, "null", ""):
            item["label"] = label
        if desc not in (None, "null", ""):
            item["description"] = desc
        if entry.get("package"):
            item["source"] = entry["package"]
        if entry.get("protectionLevel"):
            item["protectionLevel"] = entry["protectionLevel"]
        perms[name] = item

    # Hand-curated entries for well-known permissions whose defining packages
    # are OEM-specific and rarely installed; not present in the device dump.
    for name, item in MANUAL_ENTRIES.items():
        perms.setdefault(name, item)

    out = {
        "version": 1,
        "provenance": (
            "Generated from `pm list permissions -f -u` device dumps. "
            "System resolution takes precedence at runtime; this is a "
            "fallback for permissions whose defining package is not installed."
        ),
        "permissions": dict(sorted(perms.items())),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {len(perms)} permissions to {out_path}")


if __name__ == "__main__":
    main()
