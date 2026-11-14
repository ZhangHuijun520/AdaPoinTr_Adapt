"""Read current diagnostic process job limits; never starts a child or scorer."""
import ctypes,json,os,sys
from ctypes import wintypes as W
K=ctypes.WinDLL('kernel32',use_last_error=True)
K.GetCurrentProcess.restype=W.HANDLE
K.IsProcessInJob.argtypes=[W.HANDLE,W.HANDLE,ctypes.POINTER(W.BOOL)]
K.IsProcessInJob.restype=W.BOOL
K.QueryInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,W.LPVOID,W.DWORD,ctypes.POINTER(W.DWORD)]
K.QueryInformationJobObject.restype=W.BOOL
class Basic(ctypes.Structure):
 _fields_=[('PerProcessUserTimeLimit',ctypes.c_int64),('PerJobUserTimeLimit',ctypes.c_int64),('LimitFlags',W.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',W.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',W.DWORD),('SchedulingClass',W.DWORD)]
class IO(ctypes.Structure):
 _fields_=[(name,ctypes.c_uint64) for name in ['ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount']]
class Extended(ctypes.Structure):
 _fields_=[('BasicLimitInformation',Basic),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
inside=W.BOOL();ok=K.IsProcessInJob(K.GetCurrentProcess(),None,ctypes.byref(inside))
r=dict(PID=os.getpid(),parent_PID=os.getppid(),python=sys.executable,IsProcessInJob_success=bool(ok),in_job=bool(inside.value),last_error=ctypes.get_last_error() if not ok else 0,model_or_child_processes_started=0,scoring=0)
if ok and inside.value:
 info=Extended();returned=W.DWORD();queried=K.QueryInformationJobObject(None,9,ctypes.byref(info),ctypes.sizeof(info),ctypes.byref(returned))
 r.update(job_limit_query_success=bool(queried),job_limit_query_error=0 if queried else ctypes.get_last_error(),struct_bytes=ctypes.sizeof(info),returned_bytes=returned.value)
 if queried:
  flags=info.BasicLimitInformation.LimitFlags
  r.update(LimitFlags=flags,LimitFlags_hex=hex(flags),KILL_ON_JOB_CLOSE=bool(flags&0x2000),BREAKAWAY_OK=bool(flags&0x800),SILENT_BREAKAWAY_OK=bool(flags&0x1000),ActiveProcessLimit=info.BasicLimitInformation.ActiveProcessLimit)
print(json.dumps(r))
