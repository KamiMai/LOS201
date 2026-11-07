#!/usr/bin/env python3
"""Package self-contained boot/test submissions and calculate SHA-256."""
from pathlib import Path
import tarfile,hashlib,io
repo=Path(__file__).resolve().parents[2]
for n in [1,2]:
    lab=repo/f'assignment{n:02}'
    prefix=f'SE205068_MaiTheTam_Asgn{n:02}'
    output=lab/'output'/f'{prefix}.tar.gz'
    folders=['task1_ioctl','task2_misc','logs','bao_cao','scripts'] if n==1 else ['driver','app','logs','bao_cao','scripts']
    with tarfile.open(output,'w:gz') as tar:
        for folder in folders:
            for path in sorted((lab/folder).rglob('*')):
                if not path.is_file() or path.name.startswith('.') or path.suffix in ['.o','.mod'] or path.name.endswith('.mod.c') or path.name in ['Module.symvers','modules.order']:continue
                tar.add(path,arcname=f'{prefix}/{path.relative_to(lab)}')
        tar.add(lab/f'output/initramfs_asgn{n}.cpio.gz',arcname=f'{prefix}/output/initramfs_asgn{n}.cpio.gz')
        for path in sorted((repo/'assignment_support/kernel').iterdir()):
            tar.add(path,arcname=f'{prefix}/kernel/{path.name}')
        def add_text(name,text,mode=0o644):
            data=text.encode();info=tarfile.TarInfo(f'{prefix}/{name}');info.size=len(data);info.mode=mode
            # Preserve a real filesystem timestamp for generated package instructions.
            info.mtime=int((lab/'README.md').stat().st_mtime)
            tar.addfile(info,io.BytesIO(data))
        add_text('scripts/run-qemu.sh',f'''#!/bin/bash
set -euo pipefail
lab=$(cd "$(dirname "$0")/.." && pwd)
exec qemu-system-arm -M vexpress-a9 -cpu cortex-a9 -m 512M -smp 2 -nographic \\
 -kernel "$lab/kernel/zImage" -dtb "$lab/kernel/vexpress-v2p-ca9.dtb" \\
 -initrd "$lab/output/initramfs_asgn{n}.cpio.gz" \\
 -append 'console=ttyAMA0,115200 rdinit=/sbin/init mem=512M'
''',0o755)
        add_text('README.txt',f'''Mai The Tam - SE205068 - LOS201
Assignment {n:02}

This archive is bootable without the full GitHub checkout.
Run: bash scripts/run-qemu.sh
Press Enter to activate the guest console.
'''+('''Then run:
/opt/asgn1/task1_ioctl/test_asgn1.sh
/opt/asgn1/task2_misc/test_counter.sh
''' if n==1 else '''Then run: test_arm.sh
For an interactive run after the test: sms_app -d 0 -v
Press Ctrl+C to stop cleanly.
Video and personal reflection were omitted at the student's request.
''')+'''
To rebuild drivers, set KDIR to a built Linux 5.15 ARM tree using kernel/kernel.config.
The full repository includes source/image build scripts and the report generator:
https://github.com/KamiMai/LOS201
The kernel source archive and toolchain are external build dependencies.
HOST profiling uses an explicitly selected simulator; see the report for limitations.
''')
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix+'.sha256').write_text(f'{digest}  {output.name}\n')
    with tarfile.open(output) as tar:
        names=tar.getnames()
        assert len(names)==len(set(names)), 'duplicate archive member'
        assert all(x.startswith(prefix+'/') and '..' not in Path(x).parts for x in names)
    print(output.name,output.stat().st_size,len(names),digest)
