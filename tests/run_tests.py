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


def _dictionary_hash(name):
    """The OMF library dictionary hash: block, block step, bucket, bucket step."""
    rol = lambda x, n: ((x << n) | (x >> (16 - n))) & 0xFFFF
    ror = lambda x, n: ((x >> n) | (x << (16 - n))) & 0xFFFF
    text = name.encode()
    left, right, count = 0, len(text), len(text)
    block, block_step, bucket, bucket_step = count | 0x20, 0, 0, count | 0x20
    while True:
        right -= 1
        back = text[right] | 0x20
        block_step, bucket = back ^ rol(block_step, 2), back ^ ror(bucket, 2)
        count -= 1
        if count == 0:
            break
        front = text[left] | 0x20
        left += 1
        block, bucket_step = front ^ rol(block, 2), front ^ ror(bucket_step, 2)
    return block, block_step, bucket % 37, (bucket_step % 37) or 1


def _library(member, name, overflowed):
    """A library of `member`, `name` in its dictionary as a librarian puts it
    after its own block overflowed: the next block, at the name's bucket.
    Its own block is full, the name's bucket there holds another name and
    the bucket after it is empty."""
    page = 16
    pad = lambda data, to: data + bytes(-len(data) % to)
    modules = pad(member, page)
    body = pad(bytes(page) + modules + bytes([0xF1, 1, 0, 0]), 512)
    block, _, bucket, step = _dictionary_hash(name)
    blocks = 2
    home, next_block = block % blocks, (block % blocks + 1) % blocks
    def entry(text, module_page):
        raw = text.encode()
        return bytes([len(raw)]) + raw + struct.pack('<H', module_page)
    dictionary = []
    for at in range(blocks):
        table = bytearray(512)
        free = 38 // 2 + 1
        entries = []
        if at == home and overflowed:
            entries = [(bucket, entry('_other', 0))]
        if at == next_block or not overflowed:
            entries = [(bucket, entry(name, 1))]
        for slot, raw in entries:
            table[slot] = free
            table[free * 2:free * 2 + len(raw)] = raw
            free += (len(raw) + 1) // 2
        assert table[(bucket + step) % 37] == 0
        table[37] = 0xFF if at == home and overflowed else free
        dictionary.append(bytes(table))
    header = bytes([0xF0]) + struct.pack('<HIH', page - 3, len(body), blocks) + bytes([1])
    return pad(header, page) + body[page:] + b''.join(dictionary)


def test_a_library_symbol_past_a_full_dictionary_block_is_found(tmp):
    """Past a full block the search kept the bucket where it stopped rather
    than the name's own: Borland CM.LIB's _strcmp and _strncpy, each one
    block on, were undefined and QCport would not link without them
    extracted."""
    lib = os.path.join(tmp, 'ONE.LIB')
    with open(os.path.join(HERE, 'dict_member.obj'), 'rb') as f:
        member = f.read()
    with open(lib, 'wb') as f:
        f.write(_library(member, '_needed', True))
    exe = os.path.join(tmp, 'OUT.EXE')
    r = subprocess.run([JWLINK, 'option', 'quiet', 'format', 'dos', 'name', exe,
                        'file', os.path.join(HERE, 'dict_caller.obj'), 'library', lib],
                       capture_output=True)
    assert r.returncode == 0 and os.path.exists(exe), (r.stdout + r.stderr).decode()


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
