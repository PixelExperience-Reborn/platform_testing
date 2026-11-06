# PixelExperience-Reborn: Android 17 platform_testing source audit

## Scope and decision

- Matrix entry: P2, `platform_testing` (row 157; matrix file line 157).
- Legacy branch: `seventeen` at `0115e3c9e2c728dd19c9f9aedad3c6460aee4cb6`, with identical `fourteen` head when audited.
- Legacy branch's tip is a merge of the AOSP `android-14.0.0_r21` source, **not** Android 17; its first parent is `dba101fc217797b7277a5c080a11a6fe0a62eabe` and second parent is `2570e61eb12b5414260d3d28405b8aedb34283b3`.
- Official, immutable target: `platform/platform_testing`, tag `android-17.0.0_r1`, **peeled commit** `6abefd291d50dee240ed2b22572d273175f070da`, **root tree** `81eb3bcc0f6a94c2cd09dede894aa007ad713c93`.
- **Decision: keep the official AOSP Android 17 project in the active manifest. Do not create an unnecessary PE source override or try to compile an obsolete Android 14 tree.**

## Exact PixelExperience delta

GitHub's comparison of the imported AOSP parent `2570e61e` against the legacy merge tip `0115e3c9` reports **one altered file only**, `build/tasks/tests/platform_test_list.mk`, with **zero insertions and two deletions**:

- `CalendarTests`
- `ContactsTests`

This is the historic PixelExperience change `dba101fc` (`Remove ContactsTests and CalendarTests`). These two entries were removed from the older Make-based platform test list. This change does not add a device feature, fix an Android 17 test bug or justify overriding modern test modules.

## Android 17 source compatibility

The official Android 17 r1 root contains `Android.bp`, `host_runners/`, `tests/`, `libraries/`, `emu_test/`, `robolab/`, `scripts/`, `tools/` and `utils/`. The legacy `build/tasks/tests/platform_test_list.mk` is **absent** from the Android 17 root tree. Therefore, cherry-picking the PE-only deletion would target a nonexistent file. Recreating an old Make test list in the new source would be an unreviewed build-system regression.

The staged Android 17 manifest currently selects the official entry:

```xml
<project path="platform_testing" name="platform/platform_testing"
         groups="pdk-fs,pdk-cw-fs,cts,sysui-studio" />
```

The Android 17 baseline uses the official `aosp` remote and `refs/tags/android-17.0.0_r1`. No PE `platform_testing` project override, second path owner, extra product package or test suite installation is required.

## Source-only CI and guardrails

`audit/check_platform_testing_source.py` and `.github/workflows/a17-platform-testing-source-check.yml` check:

1. The historical PE head and its **exact** two-line test-list delta relative to its AOSP parent.
2. Official Android 17 tag's peeled commit and root tree **without checkout/build**, plus presence of the modern entrypoints and absence of the legacy test list.
3. The manifest baseline/default source ownership and existing 25-stage offline manifest validator; all stages must preserve the official `platform_testing` owner.

The manifest validator separately treats `platform_testing` as a protected official-source path, with a negative regression test against an unreviewed fork import.

## Explicitly NOT verified

This is a test-infrastructure **source/manifest audit**, not a system build or successful device testing claim. Still open: full `repo sync`, Soong bootstrap and module-name graph, host/device test suite execution, CTS/VTS/Tradefed, recovery/AVB/SELinux, and actual POCO F5 Pro / Redmi K60 (mondrian) boot. CI workflow execution and result must be checked on GitHub after publication; writing a workflow does not imply it passed.

## Grounded references

- Original PE repo: https://github.com/PixelExperience-Reborn/platform_testing/tree/seventeen
- PE-only historical change: https://github.com/PixelExperience-Reborn/platform_testing/commit/dba101fc217797b7277a5c080a11a6fe0a62eabe
- Legacy merge: https://github.com/PixelExperience-Reborn/platform_testing/commit/0115e3c9e2c728dd19c9f9aedad3c6460aee4cb6
- Official Android 17 r1: https://android.googlesource.com/platform/platform_testing/+/refs/tags/android-17.0.0_r1
- Port manifest: https://github.com/PixelExperience-Reborn/manifest/tree/port/a17-aosp17-manifest-20261102

No change to `seventeen` or existing AOSP17 staged profiles was performed by the source audit.
