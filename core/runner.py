# core/runner.py —— 限时执行（requirements.md 三-4 / 第八节安全边界）
# POSIX：setrlimit(CPU/AS/FSIZE) + 墙钟超时；Windows：墙钟超时 + taskkill（信号翻译降级）
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass

MAX_OUTPUT_BYTES = 4 * 1024 * 1024  # stdout/stderr 各 4MB（requirements §八）
STDERR_TAIL_BYTES = 2048  # 报告只留 stderr 末 2KB

IS_WINDOWS = sys.platform == "win32"


@dataclass
class RunResult:
    exit_code: int | None  # 被信号终止时为 None
    signal: int | None
    time_ms: float
    timed_out: bool
    stdout: bytes
    stderr: bytes
    peak_rss_kb: int | None


def stderr_tail(stderr: bytes) -> str | None:
    """stderr 末 2KB（utf-8 宽松解码）；空则 None。"""
    if not stderr:
        return None
    return stderr[-STDERR_TAIL_BYTES:].decode("utf-8", errors="replace")


class _CappedReader(threading.Thread):
    """后台读流：stdout 保留头部 4MB，stderr 保留尾部 4MB（诊断在末尾）。"""

    def __init__(self, stream, keep_head: bool):
        super().__init__(daemon=True)
        self.stream = stream
        self.keep_head = keep_head
        self.buf = bytearray()

    def run(self) -> None:
        try:
            while True:
                chunk = self.stream.read(65536)
                if not chunk:
                    break
                if self.keep_head:
                    room = MAX_OUTPUT_BYTES - len(self.buf)
                    if room > 0:
                        self.buf += chunk[:room]
                else:
                    self.buf += chunk
                    if len(self.buf) > MAX_OUTPUT_BYTES:
                        del self.buf[: len(self.buf) - MAX_OUTPUT_BYTES]
        except (OSError, ValueError):
            pass
        finally:
            try:
                self.stream.close()
            except OSError:
                pass


class _StdinWriter(threading.Thread):
    def __init__(self, stream, data: bytes):
        super().__init__(daemon=True)
        self.stream = stream
        self.data = data

    def run(self) -> None:
        try:
            if self.data:
                self.stream.write(self.data)
        except (OSError, ValueError):
            pass
        finally:
            try:
                self.stream.close()
            except OSError:
                pass


def _posix_preexec(mem_mb: int, cpu_seconds: int):
    """POSIX 子进程资源限制：CPU / 虚拟内存 / 文件大小，禁 core dump。"""
    import resource

    def _apply() -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
        mem = mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        fsize = 64 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    return _apply


def _kill_tree(proc: subprocess.Popen) -> None:
    """超时终止：Windows 走 taskkill /T（进程树），POSIX 直接 SIGKILL。"""
    if IS_WINDOWS and shutil.which("taskkill"):
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        proc.kill()
    except OSError:
        pass


def _cpu_ms_delta(before: float) -> float | None:
    """POSIX 下取子进程 CPU 时间差（ms）；Windows/不可用返回 None。"""
    if IS_WINDOWS:
        return None
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        after = usage.ru_utime + usage.ru_stime
        return max(0.0, (after - before) * 1000.0)
    except Exception:
        return None


def _cpu_ms_before() -> float:
    if IS_WINDOWS:
        return 0.0
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        return usage.ru_utime + usage.ru_stime
    except Exception:
        return 0.0


def run(binary: str | os.PathLike, input_data: bytes, time_ms: int, mem_mb: int) -> RunResult:
    """限时执行 binary，stdin 注入 input_data。

    - 墙钟超时 = time_ms × 1.5（防 IO 卡顿，requirements 三-4）
    - 墙钟超时 / CPU 超时均置 timed_out=True（判定层按 TLE 处理）
    """
    wall_timeout_s = max(0.1, (time_ms / 1000.0) * 1.5)
    cpu_seconds = max(1, int(time_ms / 1000) + (1 if time_ms % 1000 else 0))

    popen_kwargs: dict = dict(
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(str(binary))) or None,
    )
    if not IS_WINDOWS:
        popen_kwargs["preexec_fn"] = _posix_preexec(mem_mb, cpu_seconds)

    cpu_before = _cpu_ms_before()
    start = time.perf_counter()
    try:
        proc = subprocess.Popen([str(binary)], **popen_kwargs)
    except OSError as exc:
        elapsed = (time.perf_counter() - start) * 1000.0
        return RunResult(
            exit_code=None,
            signal=None,
            time_ms=elapsed,
            timed_out=False,
            stdout=b"",
            stderr=f"无法启动进程：{exc}".encode("utf-8"),
            peak_rss_kb=None,
        )

    stdin_writer = _StdinWriter(proc.stdin, input_data)
    out_reader = _CappedReader(proc.stdout, keep_head=True)
    err_reader = _CappedReader(proc.stderr, keep_head=False)
    stdin_writer.start()
    out_reader.start()
    err_reader.start()

    timed_out = False
    try:
        proc.wait(timeout=wall_timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_tree(proc)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass

    stdin_writer.join(timeout=2)
    out_reader.join(timeout=5)
    err_reader.join(timeout=5)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    cpu_ms = _cpu_ms_delta(cpu_before)

    # CPU 时间超限也算超时（判定顺序：TLE 先于 RE）
    if not timed_out and cpu_ms is not None and cpu_ms > time_ms:
        timed_out = True

    exit_code: int | None = proc.returncode
    sig: int | None = None
    if exit_code is not None and exit_code < 0 and not IS_WINDOWS:
        sig = -exit_code  # POSIX：负 returncode = 被信号 -N 终止
        exit_code = None

    return RunResult(
        exit_code=exit_code,
        signal=sig,
        time_ms=elapsed_ms,
        timed_out=timed_out,
        stdout=bytes(out_reader.buf),
        stderr=bytes(err_reader.buf),
        peak_rss_kb=None,
    )
