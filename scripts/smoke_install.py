"""Check installed CLI executables against a temporary corpus (no dev dependencies)."""

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from mcp import Client, StdioServerParameters


def executable(name: str) -> str:
    """Resolve the executable belonging to this Python environment."""
    return str(Path(sys.executable).parent / (name + (".exe" if os.name == "nt" else "")))


async def check_stdio(env: dict[str, str]) -> None:
    """Perform a handshake and a real tool call through the installed executable."""
    async with asyncio.timeout(15):
        async with Client(
            StdioServerParameters(command=executable("your-docs-mcp"), env=env)
        ) as client:
            assert len((await client.list_tools()).tools) == 6
            result = await client.call_tool("get_document", {"uri": "docs://guides/hello"})
            assert json.loads(result.content[0].text)["title"] == "Hello world"
    print("your-docs-mcp: protocol round trip passed")


def check_web(name: str, env: dict[str, str]) -> None:
    """Check startup without a stdio peer and bounded process shutdown."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process_env = {**env, "MCP_DOCS_WEB_PORT": str(port), "MCP_DOCS_WEB_HOST": "127.0.0.1"}
    with tempfile.TemporaryFile(mode="w+") as logs:
        process = subprocess.Popen(
            [executable(name)],
            env=process_env,
            stdin=subprocess.PIPE,
            stdout=logs,
            stderr=logs,
        )
        try:
            import time

            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"{name} exited with {process.returncode}")
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/api/health", timeout=1
                    ) as response:
                        health = json.load(response)
                    assert health["documents"] == 1
                    assert health["categories"] > 0
                    print(f"{name}: health check passed")
                    break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.05)
            else:
                raise TimeoutError(f"{name} did not become healthy")
        except BaseException:
            logs.seek(0)
            print(logs.read(), file=sys.stderr)
            raise
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            if process.stdin:
                process.stdin.close()


def main() -> None:
    """Run against installed wheels, including optional web commands on request."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web", action="store_true", help="Also check server-extra executables")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "guides").mkdir()
        (root / "guides" / "hello.md").write_text("# Hello world\n\nWelcome.")
        env = {**os.environ, "DOCS_ROOT": directory}
        asyncio.run(check_stdio(env))
        if args.web:
            for name in ("your-docs-server", "your-docs-web"):
                check_web(name, env)


if __name__ == "__main__":
    main()
