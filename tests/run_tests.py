#!/usr/bin/env python3
"""Link the checked-in objects and check the result.

    python3 tests/run_tests.py [path/to/jwlink]

The .obj files are jwasm output of the .asm beside them.
"""
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
JWLINK = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                         else os.path.join(HERE, '..', 'GccUnixR', 'jwlink'))


def link(obj, tmp):
    exe = os.path.join(tmp, 'OUT.EXE')
    r = subprocess.run([JWLINK, 'option', 'quiet', 'format', 'dos', 'name', exe,
                        'file', os.path.join(HERE, obj)], capture_output=True)
    assert r.returncode == 0, f'jwlink exited {r.returncode}: {r.stdout + r.stderr}'
    with open(exe, 'rb') as f:
        return f.read()


def test_explicit_frame_fixup_links(tmp):
    """A fixup with an explicit frame crashed a 64-bit jwlink (SIGSEGV/SIGBUS):
    the frame pointer was saved in 32 bits and read back as 64. BC 4.5's
    BCOM45.LIB hit it."""
    link('frame_fixup.obj', tmp)


def test_dosseg_keeps_dgroup_classes_in_first_seen_order(tmp):
    """DOSSEG put data-bearing DGROUP classes before BC_DATA, so the BASIC
    range BC_DATA..BC_FT came out negative and the runtime wiped DGROUP:
    PDS 7.1 programs died in B$RTCLR calling CS:0000."""
    exe = link('dosseg_order.obj', tmp)
    i = exe.index(b'RANGE:') + 6
    start, end = struct.unpack('<HH', exe[i:i + 4])
    assert start < end, f'BC_DATA at {start:#x} is past BC_FT at {end:#x}'


def main():
    failed = 0
    for name, fn in list(globals().items()):
        if not name.startswith('test_'):
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                fn(tmp)
                print(f'PASS {name}')
            except AssertionError as e:
                failed += 1
                print(f'FAIL {name}: {e}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
