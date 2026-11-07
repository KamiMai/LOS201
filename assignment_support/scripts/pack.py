#!/usr/bin/env python3
"""Assemble an assignment image from the existing LAB03 userspace."""
from pathlib import Path
import shutil, subprocess, sys, gzip
repo=Path(__file__).resolve().parents[2]
number=int(sys.argv[1]); lab=repo/f'assignment{number:02}'
root=repo.parents[1]/'work'/f'asgn{number}-rootfs'
# Caller may select a short reproducible build directory outside the checkout.
import os
root=Path(os.environ.get('ASGN_ROOTFS',str(root)))
if root.exists(): shutil.rmtree(root)
shutil.copytree(repo/'embedded_lab3/rootfs/initramfs',root,symlinks=True)
(root/'etc/init.d/rcS').write_text("""#!/bin/sh
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev
mount -t tmpfs none /tmp
mkdir -p /dev/mqueue
mount -t mqueue none /dev/mqueue
hostname se205068-assignment
ifconfig lo 127.0.0.1 up
ifconfig eth0 up
udhcpc -i eth0 -s /etc/udhcpc.script -q -n >/dev/null 2>&1 &
echo 'Assignment image ready; modules are loaded by the test scripts.'
""")
(root/'etc/init.d/rcS').chmod(0o755)
for d in ['dev','proc','sys','tmp','opt']:(root/d).mkdir(exist_ok=True)
if number==1:
 for task in ['task1_ioctl','task2_misc']:
  shutil.copytree(lab/task,root/'opt/asgn1'/task,ignore=shutil.ignore_patterns('*.o','*.cmd','*.mod*','Module.symvers','modules.order'),dirs_exist_ok=True)
else:
 shutil.copy2(lab/'driver/sms_sensor_driver.ko',root/'lib/modules/5.15.0/sms_sensor_driver.ko')
 shutil.copy2(lab/'app/sms_app',root/'bin/sms_app')
 shutil.copy2(lab/'scripts/test_arm.sh',root/'bin/test_arm.sh')
gen=os.environ.get('GEN_INIT_CPIO',str(repo.parents[1]/'work/assignments-kernel/linux-5.15/usr/gen_init_cpio'))
manifest=subprocess.check_output([sys.executable,str(Path(__file__).with_name('cpio_manifest.py')),str(root)])
raw=subprocess.check_output([gen,'-'],input=manifest)
(lab/'output').mkdir(exist_ok=True)
out=lab/f'output/initramfs_asgn{number}.cpio.gz'
with out.open('wb') as f:
 with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0,compresslevel=9) as z:z.write(raw)
print(out)
