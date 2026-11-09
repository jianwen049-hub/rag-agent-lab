"""CLI entry: ingest | chat | repl."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from rag_agent.agent import run_query
from rag_agent.config import get_settings
from rag_agent.ingest import ingest

console = Console()


def cmd_ingest(args: argparse.Namespace) -> int:
    settings = get_settings()
    console.print(Panel.fit(
        f"data={settings.data_dir}\npersist={settings.persist_dir}",
        title="ingest",
    ))
    n = ingest(reset=args.reset, settings=settings)
    console.print(f"Done. chunks={n}")
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    question = " ".join(args.question).strip()
    if not question:
        console.print("[red]Empty question[/red]")
        return 2
    console.print(Panel(question, title="user"))
    answer = run_query(question)
    console.print(Panel(Markdown(answer), title="agent"))
    return 0


def cmd_repl(_: argparse.Namespace) -> int:
    console.print(
        "[bold]RAG Agent REPL[/bold] — type a question, or exit/quit to leave.\n"
        "Tip: run [cyan]python -m rag_agent.cli ingest[/cyan] first if index is empty."
    )
    while True:
        try:
            question = console.input("[bold green]you>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye")
            return 0
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            console.print("bye")
            return 0
        try:
            answer = run_query(question)
            console.print(Panel(Markdown(answer), title="agent"))
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Error:[/red] {exc}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag_agent",
        description="RAG + tool-calling agent lab",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ing = sub.add_parser("ingest", help="Load data/*.md into Chroma")
    p_ing.add_argument(
        "--reset",
        action="store_true",
        help="Delete persist dir before writing",
    )
    p_ing.set_defaults(func=cmd_ingest)

    p_chat = sub.add_parser("chat", help="One-shot agent query")
    p_chat.add_argument("question", nargs="+", help="User question")
    p_chat.set_defaults(func=cmd_chat)

    p_repl = sub.add_parser("repl", help="Interactive loop")
    p_repl.set_defaults(func=cmd_repl)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
