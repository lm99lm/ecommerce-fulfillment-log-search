"""Run an e-commerce fulfillment job, ship its logs, or search recent runs."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from infrai import infrai


SERVICE = "order-fulfillment"
ENVIRONMENT = "development"


def fulfillment_entries(order_id: str, run_id: str) -> list[dict[str, Any]]:
    """Build the events emitted by one successful fulfillment run."""
    timestamp = datetime.now(timezone.utc).isoformat()
    common = {
        "service": SERVICE,
        "environment": ENVIRONMENT,
        "timestamp": timestamp,
        "trace_id": run_id,
    }
    return [
        {
            **common,
            "level": "info",
            "message": "fulfillment started",
            "metadata": {"order_id": order_id, "job": "reserve_inventory"},
        },
        {
            **common,
            "level": "info",
            "message": "inventory reserved",
            "metadata": {"order_id": order_id, "warehouse": "east-1"},
        },
        {
            **common,
            "level": "info",
            "message": "fulfillment completed",
            "metadata": {"order_id": order_id, "shipment_state": "label_ready"},
        },
    ]


def ship_fulfillment_logs(order_id: str, run_id: str) -> Any:
    """Ingest a batch with a stable key shared by all retry attempts."""
    return infrai.logs.ingest(
        entries=fulfillment_entries(order_id, run_id),
        idempotency_key=f"fulfillment:{run_id}",
    )


def search_fulfillment_logs(text: str, limit: int = 20) -> Any:
    """Search the same service and environment used by the job."""
    return infrai.logs.search(
        q=text,
        service=SERVICE,
        environment=ENVIRONMENT,
        limit=limit,
    )


def parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(description=__doc__)
    commands = command_parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="ship one fulfillment run")
    run.add_argument("--order-id", required=True)
    run.add_argument("--run-id", default=None)

    search = commands.add_parser("search", help="search fulfillment logs")
    search.add_argument("text")
    search.add_argument("--limit", type=int, default=20)
    return command_parser


def main(argv: Sequence[str] | None = None) -> None:
    args = parser().parse_args(argv)
    if args.command == "run":
        run_id = args.run_id or str(uuid.uuid4())
        result = ship_fulfillment_logs(args.order_id, run_id)
        print(json.dumps({"run_id": run_id, "ingest": result}, indent=2))
        return

    result = search_fulfillment_logs(args.text, args.limit)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
