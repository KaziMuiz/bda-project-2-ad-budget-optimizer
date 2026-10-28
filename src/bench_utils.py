"""
bench_utils.py - a small stopwatch + memory meter used by every benchmark
"""
import threading
import time

import psutil


def measure(func, *args):
    """Run func(*args). Return (result, seconds, extra_memory_in_MB).
    Memory = the highest RAM used (this process + any helper processes)
    minus the RAM already in use before we started."""
    me = psutil.Process()
    peak = [0]
    stop = threading.Event()

    def total_rss():
        total = me.memory_info().rss
        for child in me.children(recursive=True):
            try:
                total += child.memory_info().rss
            except psutil.Error:
                pass
        return total

    def watch():
        while not stop.is_set():
            peak[0] = max(peak[0], total_rss())
            time.sleep(0.05)

    base = total_rss()
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    start = time.perf_counter()
    result = func(*args)
    seconds = time.perf_counter() - start
    stop.set()
    watcher.join()
    return result, seconds, max(peak[0] - base, 0) / 1024 / 1024