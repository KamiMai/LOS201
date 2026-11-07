from pathlib import Path
import subprocess,time,signal,os
r=Path(__file__).resolve().parents[1]; app=str(r/'app/sms_app_x86'); logs=r/'logs'
cmd=['valgrind','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=definite,indirect','--error-exitcode=99','--log-file='+str(logs/'valgrind_sms.txt'),app,'--simulate','--other','-d','0','-i','100','--log',str(logs/'host_valgrind_sms.log')]
with open(logs/'valgrind_app_output.txt','w') as f:
 p=subprocess.Popen(cmd,stdout=f,stderr=f); time.sleep(31); p.send_signal(signal.SIGINT); code=p.wait(timeout=15)
print('Valgrind/SIGINT return',code,flush=True)
with open(logs/'strace_app_output.txt','w') as f:
 code=subprocess.run(['strace','-f','-c','-o',str(logs/'strace_sms.txt'),app,'--simulate','--other','-d','30','-i','100','--log',str(logs/'host_strace_sms.log')],stdout=f,stderr=f).returncode
print('strace return',code,flush=True)
