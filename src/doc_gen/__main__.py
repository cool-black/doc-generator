"""Entry point for python -m doc_gen."""

import asyncio
import sys

# Fix Windows asyncio ProactorEventLoop issue with httpx
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from doc_gen.cli.main import cli

if __name__ == "__main__":
    cli()
