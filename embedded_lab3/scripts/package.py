#!/usr/bin/env python3
"""Create the submission archive without recursively archiving itself."""
from pathlib import Path
import hashlib
import tarfile

lab = Path(__file__).resolve().parent.parent
archive = lab / 'output' / 'MaiTheTam_Lab03.tar.gz'
prefix = 'MaiTheTam_Lab03'
skip = {'perf_failed_capture.data', 'perf_debug.data'}
with tarfile.open(archive, 'w:gz', dereference=False) as tar:
    for name in ('apps', 'configs', 'scripts', 'logs'):
        for path in sorted((lab / name).rglob('*')):
            if path.is_dir() or path.name in skip or path.name.endswith(('.old', '.complete', '.failed')):
                continue
            tar.add(path, arcname=f'{prefix}/{path.relative_to(lab)}', recursive=False)
    tar.add(lab/'output/initramfs_lab3.cpio.gz', arcname=f'{prefix}/output/initramfs_lab3.cpio.gz')
    tar.add(lab/'report/LAB03_BaoCao.pdf', arcname=f'{prefix}/bao_cao/LAB03_BaoCao.pdf')
    tar.add(lab/'report/build_report.py', arcname=f'{prefix}/report/build_report.py')
    tar.add(lab/'README.md', arcname=f'{prefix}/README.md')
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(archive.parent / (archive.name + '.sha256')).write_text(f'{digest}  {archive.name}\n')
print(archive)
print(f'SHA256 {digest}')
