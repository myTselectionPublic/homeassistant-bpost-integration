"""Tests for the bpost web API client."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import unittest
from pathlib import Path


API_PATH = Path(__file__).parents[1] / "custom_components" / "bpost" / "api.py"
SPEC = importlib.util.spec_from_file_location("bpost_api", API_PATH)
assert SPEC is not None and SPEC.loader is not None
API = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = API
SPEC.loader.exec_module(API)


class _FailingTrackingApi(API.BpostWebApi):
    async def _async_fetch_tracking_details(self, tracking_id, postal_code=None):
        raise API.BpostConnectionError("tracking service unavailable")


class _MissingTrackingApi(API.BpostWebApi):
    async def _async_fetch_tracking_details(self, tracking_id, postal_code=None):
        return None


class _ParcelHistoryResponseApi(API.BpostWebApi):
    async def _async_get_text(self, url):
        self.requested_url = url
        return json.dumps('<div id="receiver">Parcel history</div>'), url


class EnrichParcelsTest(unittest.TestCase):
    def test_account_parcel_survives_tracking_connection_error(self) -> None:
        client = _FailingTrackingApi.__new__(_FailingTrackingApi)
        client._postal_code = None
        parcel = API.Parcel(tracking_id="32321234567890123456789012", name="Test parcel")

        result = asyncio.run(client._async_enrich_parcels([parcel]))

        self.assertEqual(result, [parcel])


class ParcelHistoryTest(unittest.TestCase):
    def test_fetches_and_decodes_parcels_history_endpoint(self) -> None:
        client = _ParcelHistoryResponseApi.__new__(_ParcelHistoryResponseApi)
        client._logged_in = True

        result = asyncio.run(client._async_fetch_parcels_history_html())

        self.assertEqual(client.requested_url, API.PARCELS_HISTORY_URL)
        self.assertEqual(result, '<div id="receiver">Parcel history</div>')

    def test_json_html_fragment_only_returns_undelivered_received_parcels(self) -> None:
        response = json.dumps(
            """
            <div id="sender">
              <a href="https://track.bpost.be/btr/web/#/search?itemCode=3232123410">
                Sent parcel
              </a>
            </div>
            <div id="receiver">
              <div class="row border rounded">
                <div class="col-10 small">3232123411 | From Example shop</div>
                <img src="/sites/default/files/parcels-history/out_for_delivery_byCar.svg">
                <div class="small">2026-07-31 | 09:18</div>
                <a href="https://track.bpost.be/btr/web/#/search?itemCode=3232123411&amp;postalCode=1000">
                  Incoming parcel
                </a>
              </div>
              <div class="row border rounded">
                <img src="/sites/default/files/parcels-history/delivered.svg">
                <a href="https://track.bpost.be/btr/web/#/search?itemCode=3232123412&amp;postalCode=1000">
                  Delivered parcel
                </a>
              </div>
            </div>
            """
        )
        response = f'"\n{response[1:-1]}\n"'

        parcels = API.parse_parcels(API._decode_html_fragment(response), received_only=True)

        self.assertEqual([parcel.tracking_id for parcel in parcels], ["3232123411"])
        self.assertEqual(parcels[0].name, "Example shop")
        self.assertEqual(parcels[0].sender, "Example shop")
        self.assertEqual(parcels[0].postal_code, "1000")
        self.assertEqual(parcels[0].status, "out_for_delivery_byCar")
        self.assertEqual(parcels[0].source, "parcel_history")
        self.assertEqual(
            parcels[0].tracking_summary,
            {
                "events": [
                    {
                        "date": "2026-07-31",
                        "time": "09:18",
                        "status": "out_for_delivery_byCar",
                    }
                ]
            },
        )

        client = _MissingTrackingApi.__new__(_MissingTrackingApi)
        client._postal_code = None
        enriched = asyncio.run(client._async_enrich_parcels(parcels))

        self.assertEqual(enriched, parcels)


class TrackingSummaryTest(unittest.TestCase):
    def test_expected_delivery_time_range_is_normalized(self) -> None:
        summary = API._summarize_tracking_details(
            {
                "expectedDeliveryTimeRange": {
                    "date": "2026-08-05",
                    "startTime": "08:00",
                    "endTime": "12:00",
                    "metadata": {"timeZone": "Europe/Brussels"},
                    "unused": None,
                }
            }
        )

        self.assertEqual(
            summary["expected_delivery_time_range"],
            {
                "date": "2026-08-05",
                "start_time": "08:00",
                "end_time": "12:00",
                "metadata": {"time_zone": "Europe/Brussels"},
            },
        )

        scalar_summary = API._summarize_tracking_details(
            {"expectedDeliveryTimeRange": "2026-08-05 08:00-12:00"}
        )
        self.assertEqual(
            scalar_summary["expected_delivery_time_range"],
            "2026-08-05 08:00-12:00",
        )


if __name__ == "__main__":
    unittest.main()
