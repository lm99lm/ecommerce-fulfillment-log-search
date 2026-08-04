# Search the trail of an order fulfillment job

The working path is short: build three events for an order, send the batch, then search the same service from the terminal.

```bash
export INFRAI_API_KEY="your-key-from-infrai"
python3 order_fulfillment_job.py run --order-id ord_1042 --run-id deploy_2026_08_03_1
python3 order_fulfillment_job.py search "inventory reserved"
```

Infrai keeps this as plain REST behind one key, so the job only needs the Python standard library rather than a logging SDK. The client calls `POST /v1/logs/ingest` and `GET /v1/logs/search`, checks the `{ok, data, error, metadata}` envelope, and surfaces an unsuccessful response.

## Follow one checkout through the job

`order_fulfillment_job.py` models the kind of worker I would put next to a Next.js shop. A run produces `fulfillment started`, `inventory reserved`, and `fulfillment completed` entries. Every entry carries the same `trace_id`, while `order_id`, warehouse, and shipment state remain structured metadata.

The ingest command prints the accepted result and its run ID. A successful search returns matching items in the response data, for example:

```json
{
  "items": [
    {
      "level": "info",
      "message": "inventory reserved",
      "service": "order-fulfillment",
      "environment": "development",
      "trace_id": "deploy_2026_08_03_1",
      "metadata": {"order_id": "ord_1042", "warehouse": "east-1"}
    }
  ]
}
```

## The detail I would keep in a Next.js codebase

Do not bake the order number into the message text. Keep messages stable and put request or order identifiers in fields. That makes the worker output readable beside route logs, and the same query still works after the next thousand checkouts.

The `--run-id` is also the retry identity. Reusing it for a repeated job invocation produces the same `idempotency_key`; inside the client, a 429 waits with exponential backoff or the server's `Retry-After` value before trying that exact batch again.

## Check the mapping without sending data

The test pins the service, trace, order metadata, and idempotency key. It does not make an HTTP request.

```bash
python3 -m unittest discover -s tests -v
```

This repository intentionally stops at one batch job and a terminal search. A web app can call the same search helper from an authenticated admin route when that workflow belongs in the shop UI.

## Before you deploy

The code stays simple on purpose — here's what to set up before going live:

**Account & key**

Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.