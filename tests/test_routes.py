######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Promotion API Service Test Suite
"""

# pylint: disable=duplicate-code
import json
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Promotion
from tests.factories import PromotionFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestPromotionService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Promotion).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    @staticmethod
    def _valid_create_payload():
        """Return valid data for a create request"""
        return {
            "name": "Autumn Sale",
            "promotion_type": "PERCENTAGE_OFF",
            "value": 15,
            "product_id": 101,
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        }

    def test_index(self):
        """It should return information about the Promotions service"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.is_json)

        data = response.get_json()

        self.assertEqual(data["name"], "Promotions Service")
        self.assertEqual(data["version"], "1.0")
        self.assertEqual(data["url"], "/promotions")

    def test_create_promotion(self):
        """It should create a promotion"""
        payload = self._valid_create_payload()

        response = self.client.post("/promotions", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.get_json()
        self.assertIsNotNone(result["id"])
        self.assertEqual(result["name"], payload["name"])
        self.assertEqual(result["promotion_type"], payload["promotion_type"])
        self.assertEqual(result["value"], 15.0)
        self.assertEqual(result["product_id"], payload["product_id"])
        self.assertEqual(result["start_date"], payload["start_date"])
        self.assertEqual(result["end_date"], payload["end_date"])
        self.assertTrue(result["active"])
        self.assertIsNotNone(result["created_at"])
        self.assertTrue(
            response.headers["Location"].endswith(f"/promotions/{result['id']}")
        )
        self.assertIsNotNone(Promotion.find(result["id"]))

    def test_create_promotion_requires_json(self):
        """It should reject requests without JSON content type"""
        response = self.client.post(
            "/promotions", data="{}", content_type="text/plain"
        )

        self.assertEqual(
            response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
        self.assertEqual(Promotion.query.count(), 0)

    def test_create_promotion_with_invalid_data(self):
        """It should reject invalid promotion data"""
        response = self.client.post("/promotions", json={"name": "Incomplete"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Promotion.query.count(), 0)

    def test_create_promotion_with_malformed_json(self):
        """It should reject malformed JSON"""
        response = self.client.post(
            "/promotions", data='{"name":', content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Promotion.query.count(), 0)

    def test_create_promotion_with_non_object_json(self):
        """It should reject JSON bodies that are not objects"""
        for body in [[], "not an object", 42, None]:
            with self.subTest(body=body):
                response = self.client.post(
                    "/promotions",
                    data=json.dumps(body),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(Promotion.query.count(), 0)

    def test_create_promotion_with_end_date_before_start_date(self):
        """It should reject a promotion that ends before it starts"""
        payload = self._valid_create_payload()
        payload["end_date"] = "2026-09-30"

        response = self.client.post("/promotions", json=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Promotion.query.count(), 0)

    def test_create_promotion_with_percentage_over_100(self):
        """It should reject a percentage discount greater than 100"""
        payload = self._valid_create_payload()
        payload["value"] = 101

        response = self.client.post("/promotions", json=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Promotion.query.count(), 0)

    def test_create_promotion_with_nonzero_bogo_value(self):
        """It should reject a BOGO promotion with a nonzero value"""
        payload = self._valid_create_payload()
        payload["promotion_type"] = "BOGO"
        payload["value"] = 1

        response = self.client.post("/promotions", json=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Promotion.query.count(), 0)

    def test_create_promotion_with_invalid_promotion_type(self):
        """It should reject an invalid promotion type"""
        payload = self._valid_create_payload()
        payload["promotion_type"] = "INVALID_TYPE"

        response = self.client.post("/promotions", json=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Promotion.query.count(), 0)

    def test_create_promotion_ignores_client_managed_fields(self):
        """It should ignore client-supplied IDs and creation timestamps"""
        payload = self._valid_create_payload()
        payload["id"] = 99999999
        payload["created_at"] = "2000-01-01T00:00:00"

        response = self.client.post("/promotions", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.get_json()
        self.assertNotEqual(result["id"], payload["id"])
        self.assertNotEqual(result["created_at"], payload["created_at"])
        self.assertIsNotNone(Promotion.find(result["id"]))

    def test_read_promotion(self):
        """It should read a Promotion by ID"""
        promotion = PromotionFactory()
        promotion.create()

        response = self.client.get(f"/promotions/{promotion.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), promotion.serialize())

    def test_read_empty_promotion(self):
        """It should return not found when the Promotion does not exist"""
        response = self.client.get("/promotions/0")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_promotion(self):
        """It should Delete a Promotion"""
        promotion = PromotionFactory()
        promotion.create()
        self.assertIsNotNone(promotion.id)

        response = self.client.delete(f"/promotions/{promotion.id}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Promotion.find(promotion.id))

    def test_delete_empty_promotion(self):
        """It should remove a Promotion that does not exist"""
        response = self.client.delete("/promotions/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_promotions(self):
        """It should be able to List all Promotions"""
        promotions = []

        for _ in range(3):
            promotion = PromotionFactory()
            promotion.create()
            promotions.append(promotion)

        response = self.client.get("/promotions")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(len(data), 3)

    def test_list_promotions_empty(self):
        """It should return an empty list when there are no Promotions"""
        response = self.client.get("/promotions")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(data, [])

    def test_update_promotion(self):
        """It should update an existing Promotion"""
        promotion = PromotionFactory()
        promotion.create()
        promotion_id = promotion.id

        update_data = promotion.serialize()
        update_data["name"] = "Updated Promotion"

        response = self.client.put(
            f"/promotions/{promotion_id}", json=update_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["name"], "Updated Promotion")
        self.assertEqual(Promotion.find(promotion_id).name, "Updated Promotion")

    def test_update_promotion_not_found(self):
        """It should return 404 when a Promotion does not exist"""
        promotion = PromotionFactory()

        response = self.client.put(
            "/promotions/999999",
            json=promotion.serialize()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )
        self.assertTrue(response.is_json)

    def test_update_promotion_invalid_data(self):
        """It should reject invalid Promotion data"""
        promotion = PromotionFactory()
        promotion.create()
        promotion_id = promotion.id
        original_name = promotion.name

        update_data = promotion.serialize()
        update_data["name"] = "Should Not Be Saved"
        update_data["promotion_type"] = "PERCENTAGE_OFF"
        update_data["value"] = 150

        response = self.client.put(
            f"/promotions/{promotion_id}",
            json=update_data
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertTrue(response.is_json)
        self.assertEqual(
            Promotion.find(promotion_id).name,
            original_name
        )
