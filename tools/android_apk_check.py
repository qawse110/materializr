#!/usr/bin/env python3
"""Verify a built Materializr Android APK really carries the Simplified Chinese UI.

A green Gradle run only proves the compiler was happy. The failure modes that
actually reach a tester are all inside the package: a CJK face that never made
it into assets/fonts (the UI then draws tofu boxes), an OCCT shared library
dropped by the packaging rules (the app dies on the first shape), a shared
object whose LOAD segments are not 16 KB aligned (Android 15+ refuses to load
it), or a src/i18n_catalogue.h that was not regenerated so the menus stay half
English.

This script checks the artifact, not the log. It needs nothing but the Python
standard library, so it runs on a bare CI runner and locally against any APK.

Usage:
    python3 tools/android_apk_check.py android/app/build/outputs/apk/debug/app-debug.apk
    python3 tools/android_apk_check.py app.apk --abi arm64-v8a --expect-zh 1615
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FAILURES = []
CHECKS = [0]


def check(ok, label, detail=""):
    """Record one named check. Prints a single line either way."""
    CHECKS[0] += 1
    mark = "ok  " if ok else "FAIL"
    print("[" + mark + "] " + label + (" - " + detail if detail else ""))
    if not ok:
        FAILURES.append(label + (" - " + detail if detail else ""))
    return ok


# --- src/i18n_catalogue.h ---------------------------------------------------

def _literal_bytes(src):
    r"""Turn the inside of one C string literal into the bytes it denotes.

    The generated header is pure ASCII and spells every non-ASCII byte as \xNN
    (see cstr() in tools/i18n_catalogue.py), so unicode_escape followed by
    latin-1 recovers the exact UTF-8 byte sequence.
    """
    return src.encode("ascii").decode("unicode_escape").encode("latin-1")


def parse_catalogue(header_text, symbol):
    """Parse one 'inline const TrEntry kXxCatalogue[] = { {"en", "tr"}, ... };' block.

    Adjacent string literals are concatenated by the compiler, and the generator
    emits long translations that way, so a regex on a single literal would
    silently truncate. Scan instead: read string literals back to back, then the
    second field, repeating until the block's closing brace.
    """
    start = header_text.index(symbol)
    block = header_text[start:header_text.index("};", start)]

    rows = []
    i, n = 0, len(block)
    while True:
        i = block.find("{", i)
        if i < 0:
            break
        i += 1
        fields = []
        while len(fields) < 2:
            while i < n and block[i] in " \t\r\n,":
                i += 1
            if i >= n or block[i] != '"':
                break
            buf = bytearray()
            while i < n and block[i] == '"':
                i += 1
                raw_start = i
                while block[i] != '"':
                    i += 2 if block[i] == "\\" else 1
                buf += _literal_bytes(block[raw_start:i])
                i += 1
                while i < n and block[i] in " \t\r\n":
                    i += 1
            fields.append(buf.decode("utf-8", "replace"))
        if len(fields) == 2:
            rows.append((fields[0], fields[1]))
    return rows


# --- ELF / APK helpers ------------------------------------------------------

def elf_load_alignments(data):
    """p_align of every PT_LOAD segment, or [] when the file is not ELF64."""
    if data[:4] != b"\x7fELF" or data[4] != 2:
        return []
    order = "<" if data[5] == 1 else ">"
    phoff = struct.unpack_from(order + "Q", data, 0x20)[0]
    phentsize, phnum = struct.unpack_from(order + "HH", data, 0x36)
    out = []
    for index in range(phnum):
        off = phoff + index * phentsize
        p_type = struct.unpack_from(order + "I", data, off)[0]
        if p_type == 1:  # PT_LOAD
            out.append(struct.unpack_from(order + "Q", data, off + 0x30)[0])
    return out


def tool_path(*names):
    """Find an Android SDK build-tool, or fall back to PATH."""
    home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if home:
        root = Path(home) / "build-tools"
        if root.is_dir():
            for version in sorted(root.iterdir(), key=lambda p: p.name, reverse=True):
                for name in names:
                    candidate = version / name
                    if candidate.is_file():
                        return str(candidate)
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


# --- main -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--abi", default="arm64-v8a")
    parser.add_argument("--expect-zh", type=int, default=1615,
                        help="number of Simplified Chinese catalogue entries")
    parser.add_argument("--min-occt", type=int, default=50,
                        help="minimum libTK*.so count in the APK")
    parser.add_argument("--min-page-align", type=int, default=16384)
    parser.add_argument("--skip-signature", action="store_true")
    args = parser.parse_args()

    if not check(args.apk.is_file(), "APK exists", str(args.apk)):
        return 1
    size_mb = args.apk.stat().st_size / (1024 * 1024)
    print("       %s = %.1f MiB, abi %s" % (args.apk, size_mb, args.abi))

    header = (REPO / "src" / "i18n_catalogue.h").read_text(encoding="ascii")
    rows = parse_catalogue(header, "kZhCatalogue")
    check(len(rows) == args.expect_zh, "zh catalogue parsed",
          "%d entries (expected %d)" % (len(rows), args.expect_zh))
    empty = [en for en, zh in rows if not zh.strip()]
    check(not empty, "every zh row has a translation",
          "%d empty" % len(empty) if empty else "")

    with zipfile.ZipFile(args.apk) as apk:
        names = set(apk.namelist())

        # 1. The CJK face must travel inside the package, byte for byte.
        font = "assets/fonts/NotoSansSC-Regular.ttf"
        if check(font in names, "NotoSansSC-Regular.ttf packaged", font):
            packaged = apk.read(font)
            source = REPO / "android/app/src/main/assets/fonts/NotoSansSC-Regular.ttf"
            check(source.is_file() and packaged == source.read_bytes(),
                  "packaged font matches the repo copy",
                  "%d bytes" % len(packaged))

        # 2. Native payload: libmain.so plus the r28 STL plus cross-built OCCT.
        libmain = "lib/%s/libmain.so" % args.abi
        has_main = check(libmain in names, "libmain.so packaged", libmain)
        has_stl = check("lib/%s/libc++_shared.so" % args.abi in names,
                        "libc++_shared.so packaged", args.abi)
        occt = sorted(n for n in names
                      if n.startswith("lib/%s/libTK" % args.abi) and n.endswith(".so"))
        check(len(occt) >= args.min_occt, "OCCT shared libraries packaged",
              "%d libTK*.so (minimum %d)" % (len(occt), args.min_occt))

        # 3. 16 KB page alignment: Android 15+ will not load a 4 KB-aligned .so.
        if has_main and has_stl:
            bad = []
            for entry in [libmain, "lib/%s/libc++_shared.so" % args.abi] + occt:
                aligns = elf_load_alignments(apk.read(entry))
                if not aligns:
                    bad.append("%s (not ELF64)" % entry)
                elif min(aligns) < args.min_page_align:
                    bad.append("%s (p_align %d)" % (entry, min(aligns)))
            check(not bad, "every .so is %d-byte aligned" % args.min_page_align,
                  "%d offenders: %s" % (len(bad), bad[:3]) if bad else "")

        # 4. The catalogue must be compiled into the shipped binary: a stale
        #    header or a file excluded from the CMake glob ships half-English
        #    menus and nothing else would notice.
        if has_main:
            blob = apk.read(libmain)
            absent = [zh for _, zh in rows if zh.encode("utf-8") not in blob]
            check(not absent, "zh catalogue strings compiled into libmain.so",
                  "%d/%d present" % (len(rows) - len(absent), len(rows))
                  + ("; missing e.g. %r" % (absent[:3],) if absent else ""))
            native_name = "\u7b80\u4f53\u4e2d\u6587".encode("utf-8")
            check(native_name in blob, "language picker shows the native name",
                  "\u7b80\u4f53\u4e2d\u6587")
            check(b"Chinese" in blob, "language picker English name compiled in")

    # 5. Signature: a debug build must be signed with the debug key, otherwise
    #    the APK cannot be installed at all (release builds stay unsigned).
    if args.skip_signature:
        print("[skip] signature check (--skip-signature)")
    else:
        apksigner = tool_path("apksigner", "apksigner.bat")
        if check(apksigner is not None, "apksigner available"):
            proc = subprocess.run([apksigner, "verify", "--print-certs", str(args.apk)],
                                  capture_output=True, text=True)
            check(proc.returncode == 0, "APK signature verifies",
                  (proc.stderr or proc.stdout).strip().splitlines()[0]
                  if proc.returncode else "")
            check("CN=Android Debug" in proc.stdout, "signed with the debug key")
            for line in proc.stdout.splitlines()[:3]:
                print("       " + line.strip())

    aapt2 = tool_path("aapt2", "aapt")
    if aapt2:
        proc = subprocess.run([aapt2, "dump", "badging", str(args.apk)],
                              capture_output=True, text=True)
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if line.split(":")[0] in ("package", "sdkVersion", "targetSdkVersion",
                                          "native-code", "application-label"):
                    print("       " + line.strip())
            badging = proc.stdout
            check("native-code: '%s'" % args.abi in badging,
                  "APK declares exactly the requested ABI", args.abi)
            check("application-debuggable" in badging, "APK is debuggable")
            for line in badging.splitlines():
                if line.startswith("sdkVersion:"):
                    check("24" in line, "minSdk is 24", line.strip())
                    break

    print()
    if FAILURES:
        for failure in FAILURES:
            print("::error title=APK verification::" + failure)
        print("%d of %d checks failed" % (len(FAILURES), CHECKS[0]))
        return 1
    print("all %d checks passed" % CHECKS[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
