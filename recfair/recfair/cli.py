"""Interactive terminal UI for RecFair."""

from __future__ import annotations

import argparse
import json
import sys
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from recfair.config import apply_dotenv, ensure_google_api_key, export_hf_token
from recfair.graphs import multiagent as multiagent_mod
from recfair.graphs import workflow as workflow_mod
from recfair.graphs.registry import get_runner, list_architectures
from recfair.logging import configure_logging

_THREADED = frozenset({workflow_mod.architecture_id(), multiagent_mod.architecture_id()})


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RecFair chat UI")
    parser.add_argument(
        "--arch",
        default="current",
        help="architecture id (baseline, workflow, multiagent, current, ...)",
    )
    return parser.parse_args(argv)


def _reset_thread(arch_id: str, thread_id: str) -> None:
    if arch_id == workflow_mod.architecture_id():
        workflow_mod.reset_checkpoint(thread_id)
    elif arch_id == multiagent_mod.architecture_id():
        multiagent_mod.reset_checkpoint(thread_id)


def main(argv: list[str] | None = None) -> int:
    """Run Rich chat loop."""
    configure_logging()
    apply_dotenv()
    ensure_google_api_key()
    export_hf_token()
    args = _parse_args(argv)
    arch_id, runner = get_runner(args.arch)
    console = Console()
    thread_id = str(uuid.uuid4())
    console.print(
        Panel(
            f"RecFair chat · arch={arch_id}\n"
            f"thread_id={thread_id}\n"
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
        except EOFError, KeyboardInterrupt:
            console.print("\nAté logo.")
            return 0
        if not line.strip():
            continue
        if line.startswith("/"):
            cmd = line.strip().lower().split()
            if cmd[0] in {"/quit", "/exit"}:
                return 0
            if cmd[0] == "/reset":
                _reset_thread(current_arch, thread_id)
                thread_id = str(uuid.uuid4())
                console.print(f"Sessão reiniciada · thread_id={thread_id}")
                continue
            if cmd[0] == "/trace":
                trace = not trace
                console.print(f"trace={'on' if trace else 'off'}")
                continue
            if cmd[0] == "/arch" and len(cmd) > 1:
                current_arch, runner = get_runner(cmd[1])
                thread_id = str(uuid.uuid4())
                console.print(f"arch={current_arch} · thread_id={thread_id}")
                continue
            console.print("Comando desconhecido.")
            continue
        if current_arch in _THREADED:
            output, metrics = runner(line, thread_id=thread_id)
        else:
            output, metrics = runner(line)
        if trace:
            payload = {"output": output.model_dump()}
            scoring = getattr(metrics, "scoring_trace", None)
            if scoring:
                payload["scoring_trace"] = scoring
            agents = getattr(metrics, "agent_traces", None)
            if agents:
                payload["agent_traces"] = agents
                payload["agents_route"] = getattr(metrics, "agents_route", output.agents_route)
                payload["routing_plan"] = getattr(metrics, "routing_plan", [])
                payload["replanned"] = getattr(metrics, "replanned", False)
            console.print_json(json.dumps(payload, ensure_ascii=False))
        else:
            console.print(output.model_dump_json(indent=2))
        route = getattr(metrics, "agents_route", None) or output.agents_route
        route_bit = f" · rota={' > '.join(route)}" if route else ""
        console.print(
            f"[dim]latência={metrics.latencia_s}s · llm={metrics.chamadas_llm} · "
            f"tools={metrics.tool_calls} · halt={output.halt_reason}{route_bit}[/]"
        )


if __name__ == "__main__":
    sys.exit(main())
