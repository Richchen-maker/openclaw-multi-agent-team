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
from .databus import DataBus, DataRef
from .event import Event
from .router import Router
from .watchdog import Watchdog, watchdog_loop


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
    run_p.add_argument("--daemon", action="store_true", help="Run as background daemon (continuous poll)")
    run_p.add_argument("--live", action="store_true", help="Use OpenClawDispatcher (actually spawn sub-agents)")

    # status
    sub.add_parser("status", help="Show event directory statistics")

    # route
    route_p = sub.add_parser("route", help="Look up route for event type")
    route_p.add_argument("event_type", help="Event type to look up")

    # watchdog
    wd_p = sub.add_parser("watchdog", help="Run watchdog health checks (V2)")
    wd_p.add_argument("--fix", action="store_true", help="Auto-recover issues with smart recovery engine")
    wd_p.add_argument("--dashboard", action="store_true", help="Show health dashboard")
    wd_p.add_argument("--history", nargs="?", const="24h", default=None, metavar="PERIOD",
                       help="Show history (24h, 7d, etc.)")
    wd_p.add_argument("--loop", action="store_true", help="Continuous monitoring")
    wd_p.add_argument("--interval", type=int, default=120, help="Loop interval in seconds")

    # data
    data_p = sub.add_parser("data", help="Data bus operations")
    data_sub = data_p.add_subparsers(dest="data_command", required=True)

    data_list_p = data_sub.add_parser("list", help="List available data files")
    data_list_p.add_argument("--team", default=None, help="Filter by team name")
    data_list_p.add_argument("--schema", default=None, help="Filter by schema name")

    data_sub.add_parser("schemas", help="List all available schemas")

    data_validate_p = data_sub.add_parser("validate", help="Validate data_refs in an event file")
    data_validate_p.add_argument("event_file", type=Path, help="Path to event .md file")

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
        # --live: force OpenClawDispatcher
        if args.live:
            from .dispatcher import OpenClawDispatcher
            bus.dispatcher = OpenClawDispatcher(workspace, config)

        # --daemon: fork to background, write PID file
        if args.daemon:
            import os
            pid_dir = workspace / "events" / ".watchdog"
            pid_dir.mkdir(parents=True, exist_ok=True)
            pid_file = pid_dir / config.get("daemon_pid_file", "eventbus.pid")

            child_pid = os.fork()
            if child_pid > 0:
                # Parent: write child PID and exit
                pid_file.write_text(str(child_pid))
                print(f"EventBus daemon started (PID {child_pid}), pid file: {pid_file}")
                return 0
            else:
                # Child: detach and run
                os.setsid()
                sys.stdin.close()

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

    elif args.command == "watchdog":
        if args.loop:
            watchdog_loop(workspace, interval=args.interval)
            return 0

        wd = Watchdog(workspace)

        # --history
        if args.history is not None:
            period = args.history
            hours = 24
            if period.endswith("d"):
                hours = int(period[:-1]) * 24
            elif period.endswith("h"):
                hours = int(period[:-1])
            print(wd.format_history(hours))
            return 0

        report = wd.check_all()

        # --dashboard
        if args.dashboard:
            print(wd.format_dashboard(report))
            return 0 if report.status == "HEALTHY" else 1

        # Default: V2 report
        print(wd.format_report(report))
        if args.fix and report.status != "HEALTHY":
            results = wd.auto_recover_all(report)
            for alert, ok in results:
                tag = "✅" if ok else "❌"
                print(f"  {tag} {alert.check_type} [{alert.event_id[:8] if alert.event_id else '-'}]: {alert.recovery_action}")
        return 0 if report.status == "HEALTHY" else 1

    elif args.command == "data":
        databus = DataBus(workspace)

        if args.data_command == "list":
            refs = databus.find_data(team=args.team, schema=args.schema)
            if not refs:
                print("No data files found.")
            else:
                print(f"Found {len(refs)} data file(s):")
                for ref in refs:
                    status = "✅" if ref.exists(workspace) else "❌"
                    print(f"  {status} [{ref.ref_type}] {ref.path}")
                    if ref.description:
                        print(f"     {ref.description}")
            return 0

        elif args.data_command == "schemas":
            schemas = databus.list_schemas()
            print(f"Available schemas ({len(schemas)}):")
            for name, desc in schemas.items():
                print(f"  {name}: {desc}")
            return 0

        elif args.data_command == "validate":
            ev = Event.from_file(args.event_file.resolve())
            refs = databus.parse_refs(ev)
            if not refs:
                print("No data_refs in this event.")
                return 0
            print(f"Validating {len(refs)} data ref(s):")
            all_ok = True
            for ref, valid, msg in databus.validate_refs(refs):
                tag = "✅" if valid else "❌"
                print(f"  {tag} {ref.path} — {msg}")
                if not valid:
                    all_ok = False
            return 0 if all_ok else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
