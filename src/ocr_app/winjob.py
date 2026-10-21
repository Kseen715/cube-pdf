"""Windows job object: kill a worker together with every program it started.

Closing the job handle (including when the GUI crashes) kills the whole tree,
so no orphaned Tesseract processes keep running in the background.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

_kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

_JobObjectExtendedLimitInformation = 9
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000


_IO_COUNTER_NAMES = (
    'ReadOperationCount',
    'WriteOperationCount',
    'OtherOperationCount',
    'ReadTransferCount',
    'WriteTransferCount',
    'OtherTransferCount',
)


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in _IO_COUNTER_NAMES]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('PerProcessUserTimeLimit', wintypes.LARGE_INTEGER),
        ('PerJobUserTimeLimit', wintypes.LARGE_INTEGER),
        ('LimitFlags', wintypes.DWORD),
        ('MinimumWorkingSetSize', ctypes.c_size_t),
        ('MaximumWorkingSetSize', ctypes.c_size_t),
        ('ActiveProcessLimit', wintypes.DWORD),
        ('Affinity', ctypes.c_size_t),
        ('PriorityClass', wintypes.DWORD),
        ('SchedulingClass', wintypes.DWORD),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('BasicLimitInformation', _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ('IoInfo', _IO_COUNTERS),
        ('ProcessMemoryLimit', ctypes.c_size_t),
        ('JobMemoryLimit', ctypes.c_size_t),
        ('PeakProcessMemoryUsed', ctypes.c_size_t),
        ('PeakJobMemoryUsed', ctypes.c_size_t),
    ]


_kernel32.CreateJobObjectW.restype = wintypes.HANDLE
_kernel32.CreateJobObjectW.argtypes = (wintypes.LPVOID, wintypes.LPCWSTR)
_kernel32.SetInformationJobObject.argtypes = (
    wintypes.HANDLE,
    ctypes.c_int,
    wintypes.LPVOID,
    wintypes.DWORD,
)
_kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
_kernel32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
_kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)


def _check(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


class KillOnCloseJob:
    def __init__(self) -> None:
        self._handle = _check(_kernel32.CreateJobObjectW(None, None))

        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits = info.BasicLimitInformation
        limits.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        _check(
            _kernel32.SetInformationJobObject(
                self._handle,
                _JobObjectExtendedLimitInformation,
                ctypes.byref(info),
                ctypes.sizeof(info),
            )
        )

    def assign(self, process_handle: int) -> None:
        _check(_kernel32.AssignProcessToJobObject(self._handle, process_handle))

    def terminate(self) -> None:
        if self._handle:
            _kernel32.TerminateJobObject(self._handle, 1)

    def close(self) -> None:
        if self._handle:
            _kernel32.CloseHandle(self._handle)
            self._handle = None
