"""
CLI entry point for EventBus.

Usage:
    python -m eventbus scan                          # List pending events
    python -m eventbus emit DATA_GAP --source-team X --source-role Y --severity INFO [--body "..."]
    python -m eventbus run [--interval 30]           # Start poll loop
    python -m eventbus status                        # Show event counts
    python -m eventbus route DATA_GAP                # Show route for event type
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .bus import EventBus
from .config import load_config
from .event import Event
from .router import Router


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eventbus", description="EventBus CLI")
    parser.add_argument("-w", "--workspace", type=Path, default=Path("."), help="Workspace directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    sub.add_parser("scan", help="Scan pending events")

    # emit
    emit_p = sub.add_parser("emit", help="Emit a new event")
    emit_p.add_argument("event_type", help="Event type (e.g. DATA_GAP)")
    emit_p.add_argument("--severity", default="INFO", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    emit_p.add_argument("--source-team", required=True)
    emit_p.add_argument("--source-role", required=True)
    emit_p.add_argument("--context", default="", help="Event context / description (markdown body)")
    emit_p.add_argument("--chain-depth", type=int, default=0)

    # run
    run_p = sub.add_parser("run", help="Start event poll loop")
    run_p.add_argument("--interval", type=int, default=None, help="Poll interval (seconds)")

    # status
    sub.add_parser("status", help="Show event directory statistics")

    # route
    route_p = sub.add_parser("route", help="Look up route for event type")
    route_p.add_argument("event_type", help="Event type to look up")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI main entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    workspace = args.workspace.resolve()
    config = load_config(workspace / "eventbus.yaml")
    bus = EventBus(workspace_dir=workspace, config=config)

    if args.command == "scan":
        events = bus.scan()
        if not events:
            print("No pending events.")
        for ev in events:
            print(f"  {ev.event_type:20s} [{ev.severity:8s}] {ev.event_id[:8]} from {ev.source_team}")
        return 0

    elif args.command == "emit":
        ev = Event.emit(
            event_type=args.event_type,
            severity=args.severity,
            source_team=args.source_team,
            source_role=args.source_role,
            body=args.context,
            chain_depth=args.chain_depth,
            events_dir=bus.events_dir,
        )
        print(f"Emitted: {ev.event_id} → events/pending/{ev.filename}")
        return 0

    elif args.command == "run":
        bus.run_loop(interval=args.interval)
        return 0

    elif args.command == "status":
        counts = bus.status()
        total = sum(counts.values())
        print(f"EventBus Status ({workspace / 'events'}):")
        for d, n in counts.items():
            bar = "█" * n
            print(f"  {d:12s} {n:4d}  {bar}")
        print(f"  {'total':12s} {total:4d}")
        return 0

    elif args.command == "route":
        router = Router()
        info = router.resolve(args.event_type)
        if info:
            print(f"{args.event_type} → team={info['target_team']} mode={info['target_mode']}")
        else:
            print(f"No route for {args.event_type}", file=sys.stderr)
            return 1
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
