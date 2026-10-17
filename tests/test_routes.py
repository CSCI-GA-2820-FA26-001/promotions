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

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

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
