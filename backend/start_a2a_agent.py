"""Startup script for the Local A2A Agent service.

Usage:
    # Start the agent (blocking)
    python -m backend.start_a2a_agent

    # Or in code:
    from backend.start_a2a_agent import start_agent, stop_agent
    start_agent()
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

logger = logging.getLogger("start_a2a_agent")

_agent_process: Optional[asyncio.subprocess.Process] = None
_agent_task: Optional[asyncio.Task] = None


async def _run_agent():
    """Run the Local A2A Agent as a subprocess."""
    global _agent_process

    try:
        _agent_process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "uvicorn",
            "backend.services.local_a2a_agent:app",
            "--host",
            "0.0.0.0",
            "--port",
            "10000",
            "--log-level",
            "info",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.info("Local A2A Agent started with PID %s", _agent_process.pid)

        stdout, stderr = await _agent_process.communicate()
        if _agent_process.returncode is not None and _agent_process.returncode != 0:
            logger.error(
                "Agent exited with code %s: %s",
                _agent_process.returncode,
                stderr.decode(),
            )
        else:
            logger.info("Local A2A Agent stopped")

    except Exception as e:
        logger.error("Failed to start Local A2A Agent: %s", e)
        raise


def start_agent():
    """Start the Local A2A Agent in the background."""
    if _agent_task is not None and not _agent_task.done():
        logger.warning("Local A2A Agent is already running")
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _agent_task = loop.create_task(_run_agent())

    try:
        loop.run_until_complete(_agent_task)
    except KeyboardInterrupt:
        logger.info("Received interrupt, stopping agent...")
        stop_agent()


def stop_agent():
    """Stop the Local A2A Agent."""
    global _agent_process, _agent_task

    if _agent_process and _agent_process.returncode is None:
        _agent_process.send_signal(signal.SIGTERM)
        logger.info("Sent SIGTERM to agent process")

    if _agent_task:
        _agent_task.cancel()
        logger.info("Cancelled agent task")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    print("Starting Local A2A Agent on port 10000...")
    print("Agent Card available at: http://localhost:10000/agent-card")
    print("Press Ctrl+C to stop")
    start_agent()
