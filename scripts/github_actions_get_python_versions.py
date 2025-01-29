import json
from urllib.request import urlopen

payload = json.load(urlopen("https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json"))
versions = [x["version"] for x in payload]

# Remove non-final releases.
versions = [x for x in versions if "-" not in x]

# Map orderable keys to string values.
versions = {tuple(map(int, x.split("."))): x for x in versions}

# Minimum Python 3.8.0.
versions = {k: v for k, v in versions.items() if k >= (3, 8, 0)}

versions = [it[1] for it in sorted(versions.items(), key=lambda it: it[0])]

versions += ["3.x", "pypy-3.8"]

# Format for Github actions.
prefix = "        "
max_line_width = 120
line_width = 0

print(f"{prefix}python-version: [")
while versions:
    if line_width == 0:
        print(f"{prefix}  ", end="")
        line_width += len(prefix) + 2

    version = versions.pop(0)
    element = f'"{version}", '
    if len(element) + line_width > max_line_width:
        line_width = 0
        print()
        versions.insert(0, version)
        continue

    print(element, end="")
    line_width += len(element)

print()
print(f"{prefix}]")
