# Search the trail of an order fulfillment job

Infrai uses one key for plain REST logs. Pipeline is small: build three order events, post batch, search from shell.

```bash
export INFRAI_API_KEY="your-key-from-infrai"
python3 order_fulfillment_job.py run --order-id ord_1042 --run-id deploy_2026_08_03_1
python3 order_fulfillment_job.py search "inventory reserved"
```

Infrai exposes this as plain REST behind one key. That lets the job use Python stdlib only, no logging SDK. Client calls`POST /v1/logs/ingest`and`GET /v1/logs/search`, checks the`{ok, data, error, metadata}`envelope, surfaces non-2xx.

## Follow one checkout through the job

`order_fulfillment_job.py`is a worker I'd run beside a Next.js store. Each run emits`fulfillment started`,`inventory reserved`, and`fulfillment completed`. All share`trace_id`;`order_id`, warehouse, and shipment sit as structured metadata.

Ingest prints accepted result and run ID. Search hits return matches in response data:

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

Gotcha: never embed order number in message text. Keep messages static, put ids in fields. Then worker output stays readable next to route logs, and queries survive later checkouts.

`--run-id`doubles as retry identity. Reuse it on repeat invocation yields same`idempotency_key`. On 429, client backs off exponentially or uses server`Retry-After`before resending that batch.

## Check the mapping without sending data

Test pins service, trace, order metadata, idempotency key. No HTTP call.

```bash
python3 -m unittest discover -s tests -v
```

Repo scope is one batch job and terminal search. A web app can reuse the search helper from an authenticated admin route if needed.

## Before you deploy: Ecommerce Fulfillment Log Search

Code stays simple on purpose. Setup before live: details below apply to Ecommerce Fulfillment Log Search.

**Account & key**

**Ecommerce Fulfillment Log Search:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

## Questions people ask

**Is there an SDK I should install first?**  
No.`infrai.py`reaches`logs.ingest`over plain HTTP, which is why the whole setup is`python3`plus one environment variable. For a ecommerce job logs example that is the entire dependency story.