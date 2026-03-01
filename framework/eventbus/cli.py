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
    emit_p.add_argument("--chain-id", default=None, help="Chain ID for linking related events")
    emit_p.add_argument("--parent", default=None, help="Parent event ID")

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

    # registry
    reg_p = sub.add_parser("registry", help="Show team capability registry")
    reg_p.add_argument("--scan", action="store_true", help="Force rescan")

    # data
    data_p = sub.add_parser("data", help="Data bus operations")
    data_sub = data_p.add_subparsers(dest="data_command", required=True)

    data_list_p = data_sub.add_parser("list", help="List available data files")
    data_list_p.add_argument("--team", default=None, help="Filter by team name")
    data_list_p.add_argument("--schema", default=None, help="Filter by schema name")

    data_sub.add_parser("schemas", help="List all available schemas")

    data_validate_p = data_sub.add_parser("validate", help="Validate data_refs in an event file")
    data_validate_p.add_argument("event_file", type=Path, help="Path to event .md file")

    # trace
    trace_p = sub.add_parser("trace", help="Visualize event chain")
    trace_p.add_argument("prefix", help="Event ID prefix to trace")

    # knowledge
    know_p = sub.add_parser("knowledge", help="Knowledge base operations")
    know_sub = know_p.add_subparsers(dest="know_command", required=True)

    know_list_p = know_sub.add_parser("list", help="List knowledge entries")
    know_list_p.add_argument("--domain", default=None, help="Filter by domain")

    know_query_p = know_sub.add_parser("query", help="Search knowledge")
    know_query_p.add_argument("keywords", help="Search keywords")

    know_sub.add_parser("stats", help="Knowledge base statistics")

    # cost
    cost_p = sub.add_parser("cost", help="Cost controller")
    cost_p.add_argument("--set", nargs=2, metavar=("CHAIN_ID", "BUDGET"), default=None,
                        help="Set budget: CHAIN_ID MAX_TOKENS")

    # evolve
    evolve_p = sub.add_parser("evolve", help="Extract patterns from a resolved chain")
    evolve_p.add_argument("chain_prefix", help="Chain ID prefix to evolve from")

    # patterns
    sub.add_parser("patterns", help="Show all evolved patterns")

    # shortcut
    shortcut_p = sub.add_parser("shortcut", help="Find shortcut for event type")
    shortcut_p.add_argument("event_type", help="Event type to check")
    shortcut_p.add_argument("context", help="Context string for keyword matching")

    # scheduler
    sched_p = sub.add_parser("scheduler", help="Chain scheduler status")
    sched_p.add_argument("--chains", action="store_true", help="List all chains")

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
            chain_id=args.chain_id,
            parent_event_id=args.parent,
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

        if args.interval is not None and args.interval == 0:
            bus.run_once()
        else:
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

    elif args.command == "registry":
        from .registry import Registry
        reg = Registry(workspace)
        count = reg.scan()
        print(reg.format_registry())
        return 0

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

    elif args.command == "trace":
        cmd_trace(args, workspace)
        return 0

    elif args.command == "knowledge":
        from .memory_bridge import MemoryBridge
        mb = MemoryBridge(workspace)

        if args.know_command == "list":
            results = mb.query(domain=args.domain)
            if not results:
                print("No knowledge entries found.")
            else:
                print(f"Knowledge entries ({len(results)}):")
                for r in results:
                    print(f"  [{r['domain']}] {r['topic']} — from {r['source_team']} ({r['updated_at'][:10]})")
                    if r['preview']:
                        print(f"    {r['preview'][:80]}...")
            return 0

        elif args.know_command == "query":
            # Search across all domains using keywords in topic names
            all_results = mb.query()
            keywords = args.keywords.lower().split()
            matched = []
            for r in all_results:
                text = f"{r['topic']} {r['preview']}".lower()
                if any(k in text for k in keywords):
                    matched.append(r)
            if not matched:
                print(f"No knowledge matching '{args.keywords}'")
            else:
                print(f"Found {len(matched)} result(s):")
                for r in matched:
                    print(f"  [{r['domain']}] {r['topic']} — from {r['source_team']}")
                    print(f"    {r['preview'][:120]}")
            return 0

        elif args.know_command == "stats":
            s = mb.stats()
            print(f"Knowledge Base: {s['total']} entries")
            for domain, count in s['by_domain'].items():
                print(f"  {domain}: {count}")
            return 0

    elif args.command == "evolve":
        from .evolver import Evolver
        ev = Evolver(workspace)
        patterns = ev.evolve_after_chain(args.chain_prefix)
        print(f"Extracted {len(patterns)} pattern(s) from chain '{args.chain_prefix}'")
        for p in patterns:
            print(f"  {p.pattern_id}: {p.event_type} conf={p.confidence:.2f} keywords={p.context_keywords[:5]}")
        return 0

    elif args.command == "patterns":
        from .evolver import Evolver
        ev = Evolver(workspace)
        print(ev.format_patterns())
        return 0

    elif args.command == "shortcut":
        from .evolver import Evolver
        ev = Evolver(workspace)
        pattern = ev.find_shortcut(args.event_type, args.context)
        if pattern:
            print(f"[SHORTCUT] Found: {pattern.pattern_id} conf={pattern.confidence:.2f}")
            print(f"  Solution: {pattern.solution_summary[:200]}")
            print(f"  Skip: {pattern.chain_shortcut.get('skip_event_types', [])}")
        else:
            print(f"No shortcut found for {args.event_type}")
        return 0

    elif args.command == "cost":
        from .cost_controller import CostController
        cc = CostController(workspace)

        if args.set:
            chain_id, budget_str = args.set
            cc.set_budget(chain_id, int(budget_str))
            print(f"Budget set: {chain_id} = {int(budget_str):,} tokens")
        else:
            print(cc.format_report())
        return 0

    elif args.command == "scheduler":
        from .scheduler import Scheduler
        sched = Scheduler(workspace, config)

        if args.chains:
            if not sched.chains:
                print("No chains registered.")
            else:
                for cid, c in sched.chains.items():
                    print(f"  {c.status:10s} {cid} steps={c.current_step} priority={c.priority}")
        else:
            print(sched.format_status())
        return 0

    return 1


def cmd_trace(args, workspace: Path):
    """可视化事件链路 — 按event_id前缀 + body关键词 + chain_depth排序"""
    prefix = args.prefix
    events_dir = workspace / "events"
    all_events: list[tuple[Event, str]] = []
    seen_ids: set[str] = set()

    status_emoji = {"pending": "⏳", "processing": "🔄", "resolved": "✅", "failed": "❌"}

    for status_dir in ["pending", "processing", "resolved", "failed"]:
        dir_path = events_dir / status_dir
        if not dir_path.exists():
            continue
        for f in dir_path.glob("*.md"):
            try:
                event = Event.from_file(f)
                matched = False
                # 1. chain_id精确匹配（优先）
                if event.chain_id and prefix.lower() == event.chain_id.lower():
                    matched = True
                # 2. event_id前缀匹配
                elif prefix.lower() in event.event_id.lower():
                    matched = True
                # 3. body关键词匹配（回退）
                elif prefix.lower() in (event.body or "").lower():
                    matched = True
                if matched and event.event_id not in seen_ids:
                    seen_ids.add(event.event_id)
                    all_events.append((event, status_dir))
            except Exception:
                continue

    if not all_events:
        print(f"No events found matching '{prefix}'")
        return

    # 3. 按chain_depth排序
    all_events.sort(key=lambda x: x[0].chain_depth)

    print(f"\n{'━' * 50}")
    print(f"Event Chain: {prefix}")
    print(f"{'━' * 50}")

    for event, status in all_events:
        depth = event.chain_depth
        emoji = status_emoji.get(status, "?")
        indent = "│  " * depth
        connector = "├→ " if depth > 0 else ""
        source_role = event.metadata.get("source_role", "")
        line = f"{indent}{connector}{event.event_id[:20]} [{event.event_type}] {event.source_team}/{source_role} {emoji}"
        print(line)

    print(f"{'━' * 50}")
    total = len(all_events)
    resolved = sum(1 for _, s in all_events if s == "resolved")
    print(f"Total: {total} events | Resolved: {resolved}/{total}")


if __name__ == "__main__":
    sys.exit(main())
