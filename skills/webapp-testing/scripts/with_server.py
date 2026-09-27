#!/usr/bin/env python3
"""Run a command with one or more temporary local servers.

Pass matching --server and --port options, followed by -- and the test command.
Server commands are executed through the shell to support project run scripts.
Adapted from Composio's webapp-testing helper; see ../LICENSE.txt.
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import ExitStack


def port_is_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            return True
    except OSError:
        return False


def wait_for_server(process: subprocess.Popen[bytes], port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Server process exited before port {port} was ready")
        if port_is_open(port):
            return
        time.sleep(0.2)
    raise RuntimeError(f"Server did not open port {port} within {timeout:g}s")


def stop_server(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()
    except ProcessLookupError:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", action="append", required=True,
                        help="project server command; repeat for multiple servers")
    parser.add_argument("--port", type=int, action="append", required=True,
                        help="expected local TCP port; repeat to match --server")
    parser.add_argument("--timeout", type=float, default=30,
                        help="seconds to wait for each server (default: 30)")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="test command after --")
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if len(args.server) != len(args.port):
        parser.error("each --server needs one --port")
    if not command:
        parser.error("provide a test command after --")
    if args.timeout <= 0 or any(not 1 <= port <= 65535 for port in args.port):
        parser.error("timeout must be positive and ports must be in 1..65535")
    if len(set(args.port)) != len(args.port):
        parser.error("ports must be distinct")

    processes: list[subprocess.Popen[bytes]] = []
    with ExitStack() as stack:
        try:
            for server, port in zip(args.server, args.port):
                if port_is_open(port):
                    raise RuntimeError(f"Port {port} is already in use")
                log = stack.enter_context(tempfile.TemporaryFile(mode="w+b"))
                process = subprocess.Popen(
                    server, shell=True, stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=(os.name == "posix"),
                )
                processes.append(process)
                try:
                    wait_for_server(process, port, args.timeout)
                except RuntimeError:
                    log.seek(0)
                    diagnostic = log.read()[-2000:].decode("utf-8", errors="replace")
                    if diagnostic:
                        print(diagnostic, file=sys.stderr)
                    raise
            return subprocess.run(command, check=False).returncode
        except (OSError, RuntimeError) as error:
            print(f"with_server: {error}", file=sys.stderr)
            return 1
        finally:
            for process in reversed(processes):
                stop_server(process)


if __name__ == "__main__":
    raise SystemExit(main())
