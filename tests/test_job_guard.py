# -*- coding: utf-8 -*-
import socket
import time

import pytest

import job_guard


def test_net_default_timeout_is_set():
    assert socket.getdefaulttimeout() == job_guard.NET_TIMEOUT


def test_run_limited_returns_value():
    assert job_guard.run_limited("x", 5, lambda a: a * 2, 21) == 42


def test_run_limited_passes_errors():
    def boom():
        raise ValueError("bad")
    with pytest.raises(ValueError):
        job_guard.run_limited("x", 5, boom)


def test_run_limited_stops_hang_and_says_where():
    logs = []

    def hang_here():
        time.sleep(30)

    t0 = time.time()
    with pytest.raises(TimeoutError) as e:
        job_guard.run_limited("us", 2, hang_here, beat_s=1, log=logs.append)
    assert time.time() - t0 < 10
    assert "hang_here" in str(e.value)  # بيقول واقف في أنهي دالة
    assert any("لسه شغال" in m for m in logs) and any("⛔" in m for m in logs)
