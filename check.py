"""Alert via ntfy when any HOM chalet is free for the target nights."""
import json
import os
import sys
import urllib.request

URL = "https://homminichalets.com/apps/hostfully-integration/hostfully/properties"
NIGHTS = (os.environ.get("NIGHTS") or "2026-11-06,2026-11-07").split(",")
TOPIC = os.environ.get("NTFY_TOPIC", "")


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (chalet-watch)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["data"]


def free_chalets(data):
    names = {p["uid"]: p["name"] for p in data["properties"]["properties"]}
    found = []
    for cal in data["propertiesCalendar"]["calendars"]:
        days = {e["date"]: e for e in cal["entries"]}
        if all(n in days and not days[n]["availability"]["unavailable"] for n in NIGHTS):
            found.append((names.get(cal["propertyUid"], cal["propertyUid"]), cal["propertyUid"]))
    return sorted(found)


def notify(found):
    lines = [f"{name}: https://homminichalets.com/pages/chalets?uid={uid}" for name, uid in found]
    body = f"Free {NIGHTS[0]} to {NIGHTS[-1]}:\n" + "\n".join(lines)
    req = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}",
        data=body.encode(),
        headers={"Title": "Chalet available!", "Priority": "urgent", "Tags": "house,tada"},
    )
    urllib.request.urlopen(req, timeout=30).read()


def main():
    found = free_chalets(fetch())
    if not found:
        print(f"None free for {NIGHTS}")
        return
    print("AVAILABLE:", [n for n, _ in found])
    if TOPIC:
        notify(found)
    else:
        print("NTFY_TOPIC not set; skipping notification", file=sys.stderr)


if __name__ == "__main__":
    main()
