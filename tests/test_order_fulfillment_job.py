"""Focused tests for the domain fields and retry identity."""

import unittest
from unittest.mock import patch

from order_fulfillment_job import fulfillment_entries, ship_fulfillment_logs


class FulfillmentLoggingTest(unittest.TestCase):
    def test_entries_keep_order_context_structured(self) -> None:
        entries = fulfillment_entries("ord_1042", "run_9")

        self.assertEqual(3, len(entries))
        self.assertTrue(all(entry["service"] == "order-fulfillment" for entry in entries))
        self.assertTrue(all(entry["trace_id"] == "run_9" for entry in entries))
        self.assertTrue(all(entry["metadata"]["order_id"] == "ord_1042" for entry in entries))

    @patch("order_fulfillment_job.infrai.logs.ingest")
    def test_run_id_becomes_idempotency_key(self, ingest) -> None:
        ingest.return_value = {"accepted": 3}

        result = ship_fulfillment_logs("ord_1042", "run_9")

        self.assertEqual({"accepted": 3}, result)
        self.assertEqual("fulfillment:run_9", ingest.call_args.kwargs["idempotency_key"])


if __name__ == "__main__":
    unittest.main()
