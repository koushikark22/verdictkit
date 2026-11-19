"""Print true test counts from JUnit XML files (no filtering, no rounding)."""
import sys
import xml.etree.ElementTree as ET

total = {"tests": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
for path in sys.argv[1:]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as e:
        print(f"{path}: MISSING OR UNREADABLE ({e})")
        continue
    c = {"tests": 0, "failed": 0, "errors": 0, "skipped": 0}
    for tc in root.iter("testcase"):
        c["tests"] += 1
        if tc.find("failure") is not None:
            c["failed"] += 1
        elif tc.find("error") is not None:
            c["errors"] += 1
        elif tc.find("skipped") is not None:
            c["skipped"] += 1
    c["passed"] = c["tests"] - c["failed"] - c["errors"] - c["skipped"]
    print(f"{path}: {c['tests']} tests, {c['passed']} passed, {c['failed']} failed, {c['errors']} errors, {c['skipped']} skipped")
    for k in total:
        total[k] += c[k]
print(f"TOTAL: {total['tests']} tests, {total['passed']} passed, {total['failed']} failed, {total['errors']} errors, {total['skipped']} skipped")
