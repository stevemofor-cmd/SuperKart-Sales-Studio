from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "deployment"))

from backend_files.app import app  # noqa: E402
from common.contracts import MODEL_FEATURES  # noqa: E402


class BackendContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def setUp(self):
        self.batch = pd.read_csv(ROOT / "sourceData" / "Batch_Data_SuperKart.csv")

    def test_health_reports_loaded_model(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["model_loaded"])

    def test_single_prediction_uses_expected_response_contract(self):
        response = self.client.post(
            "/v1/predict",
            json=self.batch.iloc[0].to_dict(),
        )
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertIn("Predicted_Product_Store_Sales_Total", result)
        self.assertGreater(result["Predicted_Product_Store_Sales_Total"], 0)

    def test_unknown_store_type_is_rejected_explicitly(self):
        payload = self.batch.iloc[0].to_dict()
        payload["Store_Type"] = "Supermarket Type3"
        response = self.client.post("/v1/predict", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported Store_Type", response.get_json()["error"])

    def test_batch_reports_supported_and_unsupported_rows(self):
        upload = io.BytesIO(self.batch.to_csv(index=False).encode("utf-8"))
        response = self.client.post(
            "/v1/predictbatch",
            data={"file": (upload, "batch.csv")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["rows_received"], 10)
        self.assertEqual(result["predicted_count"], 8)
        self.assertEqual(result["error_count"], 2)
        self.assertEqual([item["row"] for item in result["errors"]], [5, 10])
        self.assertEqual(
            set(result["predictions"][0]),
            {"row", "Predicted_Product_Store_Sales_Total"},
        )

    def test_batch_rejects_missing_required_columns(self):
        bad = pd.DataFrame([{"Product_MRP": 20.0}]).to_csv(index=False)
        response = self.client.post(
            "/v1/predictbatch",
            data={"file": (io.BytesIO(bad.encode("utf-8")), "bad.csv")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("missing columns", response.get_json()["error"])

    def test_contract_has_ten_model_features(self):
        self.assertEqual(len(MODEL_FEATURES), 10)


if __name__ == "__main__":
    unittest.main()
