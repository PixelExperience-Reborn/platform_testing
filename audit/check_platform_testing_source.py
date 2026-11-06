#!/usr/bin/env python3
"""Fail-closed, source-only AOSP 17 platform_testing audit.

Arguments: legacy PE repository, shallow-fetched official AOSP tree, staged
manifest checkout. Does not build modules, run CTS/VTS or validate a device.
"""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

LEGACY = "0115e3c9e2c728dd19c9f9aedad3c6460aee4cb6"
LEGACY_FIRST_PARENT = "dba101fc217797b7277a5c080a11a6fe0a62eabe"
LEGACY_AOSP_PARENT = "2570e61eb12b5414260d3d28405b8aedb34283b3"
AOSP17_COMMIT = "6abefd291d50dee240ed2b22572d273175f070da"
AOSP17_TREE = "81eb3bcc0f6a94c2cd09dede894aa007ad713c93"
LEGACY_LIST = "build/tasks/tests/platform_test_list.mk"


def git(repo, *args):
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_legacy(root):
    # The caller fetches refs/heads/seventeen to depth >= 2, exposing both
    # real merge parents. Do not mistake a renamed branch for AOSP17 sources.
    require(git(root, "rev-parse", "refs/remotes/origin/seventeen") == LEGACY,
            "historic PE branch changed; redo the comparison before proceeding")
    parents = git(root, "rev-list", "--parents", "-n", "1", LEGACY).split()
    require(parents == [LEGACY, LEGACY_FIRST_PARENT, LEGACY_AOSP_PARENT],
            f"unexpected legacy merge ancestry: {parents}")
    expected_stat = "0\t2\t" + LEGACY_LIST
    stat = git(root, "diff", "--numstat", LEGACY_AOSP_PARENT, LEGACY)
    require(stat == expected_stat,
            f"additional PE changes need review: {stat!r}")
    patch = git(root, "diff", "--unified=0", LEGACY_AOSP_PARENT,
                LEGACY, "--", LEGACY_LIST)
    removed = [line[1:].strip().split()[0]
               for line in patch.splitlines()
               if line.startswith("-") and not line.startswith("---")]
    added = [line for line in patch.splitlines()
             if line.startswith("+") and not line.startswith("+++")]
    require(removed == ["CalendarTests", "ContactsTests"] and not added,
            f"unexpected historical PE delta: {removed!r}, {added!r}")
    print("PASS: legacy PE-only diff is exactly two old Make test deletions")


def check_aosp17(root):
    commit = git(root, "rev-parse", "FETCH_HEAD^{commit}")
    tree = git(root, "rev-parse", "FETCH_HEAD^{tree}")
    require(commit == AOSP17_COMMIT and tree == AOSP17_TREE,
            f"unexpected official tag commit/tree: {commit} / {tree}")
    roots = set(git(root, "ls-tree", "--name-only", "FETCH_HEAD").splitlines())
    require({"Android.bp", "host_runners", "libraries", "tests", "tools",
             "emu_test", "robolab", "scripts", "utils"}.issubset(roots),
            "modern Android 17 platform_testing entrypoints missing")
    require("build" not in roots, "old platform_testing build tasks reappeared")
    require(not git(root, "ls-tree", "-r", "--name-only",
                    "FETCH_HEAD", "--", LEGACY_LIST),
            "old platform test list reappeared upstream")
    print("PASS: AOSP17 r1 commit/tree and modern layout are exact")


def check_manifest(root):
    base = ET.parse(root / "aosp17_reference.xml").getroot()
    projects = [p for p in base.findall("project")
                if p.get("path") == "platform_testing"]
    require(len(projects) == 1 and
            projects[0].get("name") == "platform/platform_testing",
            "official platform_testing baseline owner absent or replaced")
    default = base.find("default")
    require(default is not None and
            default.get("revision") == "refs/tags/android-17.0.0_r1" and
            default.get("remote") == "aosp",
            "official baseline tag/remote no longer selected")
    entry = ET.parse(root / "default.xml").getroot()
    includes = list(entry)
    require(len(includes) == 1 and
            includes[0].tag == "include" and
            includes[0].get("name") == "aosp17_pe_p2_kernel_configs.xml",
            "active manifest entrypoint changed; review the new profile")
    subprocess.run(
        [sys.executable, str(root / "tools/validate_aosp17_base_profiles.py")],
        cwd=root, check=True)
    print("PASS: official AOSP17 platform_testing owner retained by staged manifest")


def main():
    require(len(sys.argv) == 4,
            "usage: check_platform_testing_source.py PE_ROOT AOSP17_GIT_ROOT MANIFEST_ROOT")
    pe, aosp, manifest = map(lambda v: Path(v).resolve(), sys.argv[1:])
    for repo in (pe, aosp, manifest):
        require(repo.is_dir(), f"missing checkout {repo}")
    check_legacy(pe)
    check_aosp17(aosp)
    check_manifest(manifest)
    print("PASS: platform_testing source-only gate; no build or hardware testing")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError, ValueError,
            ET.ParseError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
