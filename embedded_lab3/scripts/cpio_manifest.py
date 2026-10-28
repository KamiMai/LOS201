#!/usr/bin/env python3
"""Describe the rootfs for Linux gen_init_cpio without requiring root."""
from pathlib import Path
import stat
import sys

root = Path(sys.argv[1]).resolve()
print('dir / 755 0 0')
for path in sorted(root.rglob('*')):
    rel = '/' + str(path.relative_to(root))
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        print(f'slink {rel} {path.readlink()} 777 0 0')
    elif stat.S_ISDIR(mode):
        print(f'dir {rel} {stat.S_IMODE(mode):o} 0 0')
    elif stat.S_ISREG(mode):
        print(f'file {rel} {path} {stat.S_IMODE(mode):o} 0 0')
for name, major, minor, mode in (
    ('console', 5, 1, '600'), ('null', 1, 3, '666'),
    ('zero', 1, 5, '666'), ('random', 1, 8, '666'),
):
    print(f'nod /dev/{name} {mode} 0 0 c {major} {minor}')
