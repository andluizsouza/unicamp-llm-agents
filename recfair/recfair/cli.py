"""Interactive terminal UI for RecFair."""

from __future__ import annotations

import argparse
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from recfair.config import apply_dotenv, ensure_google_api_key
from recfair.graphs.registry import get_runner, list_architectures
from recfair.logging import configure_logging


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RecFair chat UI")
    parser.add_argument(
        "--arch",
        default="current",
        help="architecture id (baseline, current, ...)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run Rich chat loop."""
    configure_logging()
    apply_dotenv()
    ensure_google_api_key()
    args = _parse_args(argv)
    arch_id, runner = get_runner(args.arch)
    console = Console()
    console.print(
        Panel(
            f"RecFair chat · arch={arch_id}\n"
            f"Comandos: /quit /reset /trace /arch <id>\n"
            f"Arquiteturas: {', '.join(list_architectures())}",
            title="RecFair",
        )
    )
    trace = False
    current_arch = arch_id
    while True:
        try:
            line = Prompt.ask("[bold cyan]você[/]")
        except (EOFError, KeyboardInterrupt):
            console.print("\nAté logo.")
            return 0
        if not line.strip():
            continue
        if line.startswith("/"):
            cmd = line.strip().lower().split()
            if cmd[0] in {"/quit", "/exit"}:
                return 0
            if cmd[0] == "/reset":
                console.print("Sessão reiniciada (E1: sem memória persistente).")
                continue
            if cmd[0] == "/trace":
                trace = not trace
                console.print(f"trace={'on' if trace else 'off'}")
                continue
            if cmd[0] == "/arch" and len(cmd) > 1:
                current_arch, runner = get_runner(cmd[1])
                console.print(f"arch={current_arch}")
                continue
            console.print("Comando desconhecido.")
            continue
        output, metrics = runner(line)
        if trace:
            console.print_json(json.dumps(output.model_dump(), ensure_ascii=False))
        else:
            console.print(output.model_dump_json(indent=2))
        console.print(
            f"[dim]latência={metrics.latencia_s}s · llm={metrics.chamadas_llm} · "
            f"tools={metrics.tool_calls} · halt={output.halt_reason}[/]"
        )


if __name__ == "__main__":
    sys.exit(main())
