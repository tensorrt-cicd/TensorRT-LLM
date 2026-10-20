# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit coverage for the CI port allocator's loopback connect probe."""

import socket

__extra_import_path__ = ["~/tests/integration"]
import defs.common as common


def _unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_port_answers_on_loopback_detects_a_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        assert common._port_answers_on_loopback(listener.getsockname()[1])


def test_port_answers_on_loopback_is_false_for_an_unused_port():
    assert not common._port_answers_on_loopback(_unused_port())


def test_reserve_port_skips_a_bindable_port_that_another_listener_answers(monkeypatch):
    """A port the host redirects can be bound locally but never reached; skip it."""
    redirected, usable = _unused_port(), _unused_port()
    monkeypatch.setattr(common, "PORTS_IN_USE", set())
    monkeypatch.setattr(common, "_port_answers_on_loopback", lambda port: port == redirected)

    port = common.reserve_port_from_range(
        (min(redirected, usable), max(redirected, usable)), "test"
    )

    assert port is not None
    assert port != redirected
    assert redirected not in common.PORTS_IN_USE


def test_reserve_port_returns_none_when_every_port_is_redirected(monkeypatch):
    port = _unused_port()
    monkeypatch.setattr(common, "PORTS_IN_USE", set())
    monkeypatch.setattr(common, "_port_answers_on_loopback", lambda p: True)

    assert common.reserve_port_from_range((port, port), "test") is None
