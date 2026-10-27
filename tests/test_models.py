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
Test cases for Promotion Model
"""

# pylint: disable=duplicate-code
import os
import logging
from datetime import date
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.models import Promotion, PromotionType, DataValidationError, db
from .factories import PromotionFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  P R O M O T I O N   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestPromotionModel(TestCase):
    """Test Cases for Promotion Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Promotion).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  C R E A T E   /   R E A D   /   U P D A T E   /   D E L E T E
    ######################################################################

    def test_create_a_promotion(self):
        """It should Create a Promotion and assert that it exists"""
        promotion = Promotion(
            name="Summer Sale",
            promotion_type=PromotionType.PERCENTAGE_OFF,
            value=Decimal("20.00"),
            product_id=101,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 8, 31),
            active=True,
        )
        self.assertEqual(str(promotion), "<Promotion Summer Sale id=[None]>")
        self.assertIsNone(promotion.id)
        self.assertEqual(promotion.name, "Summer Sale")
        self.assertEqual(promotion.promotion_type, PromotionType.PERCENTAGE_OFF)
        self.assertEqual(promotion.value, Decimal("20.00"))
        self.assertEqual(promotion.product_id, 101)
        self.assertEqual(promotion.start_date, date(2026, 6, 1))
        self.assertEqual(promotion.end_date, date(2026, 8, 31))
        self.assertTrue(promotion.active)

    def test_add_a_promotion(self):
        """It should Create a Promotion and add it to the database"""
        self.assertEqual(Promotion.all(), [])
        promotion = PromotionFactory()
        promotion.create()
        self.assertIsNotNone(promotion.id)
        self.assertIsNotNone(promotion.created_at)
        self.assertIsNotNone(promotion.updated_at)
        self.assertEqual(len(Promotion.all()), 1)

    def test_add_a_storewide_promotion(self):
        """It should Create a store-wide Promotion with no product_id"""
        promotion = PromotionFactory(product_id=None)
        promotion.create()
        found = Promotion.find(promotion.id)
        self.assertIsNone(found.product_id)

    def test_active_defaults_to_true(self):
        """It should default active to True when it is not set"""
        promotion = Promotion(
            name="Default Active",
            promotion_type=PromotionType.BOGO,
            value=Decimal("0"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
        promotion.create()
        self.assertTrue(Promotion.find(promotion.id).active)

    def test_create_promotion_with_missing_name(self):
        """It should not Create a Promotion without a name"""
        promotion = PromotionFactory(name=None)
        self.assertRaises(DataValidationError, promotion.create)

    def test_read_a_promotion(self):
        """It should Read a Promotion"""
        promotion = PromotionFactory()
        promotion.create()
        found = Promotion.find(promotion.id)
        self.assertEqual(found.id, promotion.id)
        self.assertEqual(found.name, promotion.name)
        self.assertEqual(found.promotion_type, promotion.promotion_type)
        self.assertEqual(found.value, promotion.value)
        self.assertEqual(found.product_id, promotion.product_id)
        self.assertEqual(found.start_date, promotion.start_date)
        self.assertEqual(found.end_date, promotion.end_date)
        self.assertEqual(found.active, promotion.active)

    def test_read_a_promotion_not_found(self):
        """It should return None when a Promotion is not found"""
        self.assertIsNone(Promotion.find(0))

    def test_update_a_promotion(self):
        """It should Update a Promotion"""
        promotion = PromotionFactory(name="Old Name")
        promotion.create()
        original_id = promotion.id
        promotion.name = "New Name"
        promotion.update()
        self.assertEqual(promotion.id, original_id)
        found = Promotion.all()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].id, original_id)
        self.assertEqual(found[0].name, "New Name")

    def test_update_a_promotion_with_bad_data(self):
        """It should not Update a Promotion with invalid data"""
        promotion = PromotionFactory()
        promotion.create()
        promotion.name = None
        self.assertRaises(DataValidationError, promotion.update)

    def test_delete_a_promotion(self):
        """It should Delete a Promotion"""
        promotion = PromotionFactory()
        promotion.create()
        self.assertEqual(len(Promotion.all()), 1)
        promotion.delete()
        self.assertEqual(len(Promotion.all()), 0)

    def test_delete_a_promotion_with_error(self):
        """It should raise DataValidationError when a delete fails"""
        promotion = PromotionFactory()
        promotion.create()
        with patch("service.models.db.session.commit", side_effect=Exception("boom")):
            self.assertRaises(DataValidationError, promotion.delete)

    def test_list_all_promotions(self):
        """It should List all Promotions in the database"""
        self.assertEqual(Promotion.all(), [])
        for _ in range(5):
            PromotionFactory().create()
        self.assertEqual(len(Promotion.all()), 5)

    ######################################################################
    #  S E R I A L I Z E   /   D E S E R I A L I Z E
    ######################################################################

    def test_serialize_a_promotion(self):
        """It should serialize a Promotion into a dictionary"""
        promotion = PromotionFactory()
        promotion.create()
        data = promotion.serialize()
        self.assertEqual(data["id"], promotion.id)
        self.assertEqual(data["name"], promotion.name)
        self.assertEqual(data["promotion_type"], promotion.promotion_type.name)
        self.assertEqual(data["value"], float(promotion.value))
        self.assertEqual(data["product_id"], promotion.product_id)
        self.assertEqual(data["start_date"], promotion.start_date.isoformat())
        self.assertEqual(data["end_date"], promotion.end_date.isoformat())
        self.assertEqual(data["active"], promotion.active)
        self.assertEqual(data["created_at"], promotion.created_at.isoformat())
        self.assertEqual(data["updated_at"], promotion.updated_at.isoformat())

    def test_deserialize_a_promotion(self):
        """It should deserialize a Promotion from a dictionary"""
        data = PromotionFactory().serialize()
        promotion = Promotion()
        promotion.deserialize(data)
        self.assertEqual(promotion.name, data["name"])
        self.assertEqual(promotion.promotion_type.name, data["promotion_type"])
        self.assertEqual(promotion.value, Decimal(str(data["value"])))
        self.assertEqual(promotion.product_id, data["product_id"])
        self.assertEqual(promotion.start_date.isoformat(), data["start_date"])
        self.assertEqual(promotion.end_date.isoformat(), data["end_date"])
        self.assertEqual(promotion.active, data["active"])

    def test_deserialize_ignores_id_and_timestamps(self):
        """It should not take id or timestamps from the client"""
        data = PromotionFactory().serialize()
        data["id"] = 999
        data["created_at"] = "2000-01-01T00:00:00"
        promotion = Promotion().deserialize(data)
        self.assertIsNone(promotion.id)
        self.assertIsNone(promotion.created_at)

    def test_deserialize_storewide_promotion(self):
        """It should deserialize a Promotion with a missing product_id as store-wide"""
        data = PromotionFactory().serialize()
        del data["product_id"]
        promotion = Promotion().deserialize(data)
        self.assertIsNone(promotion.product_id)

    def test_deserialize_active_defaults_to_true(self):
        """It should default active to True when it is missing"""
        data = PromotionFactory(active=False).serialize()
        del data["active"]
        promotion = Promotion().deserialize(data)
        self.assertTrue(promotion.active)

    def test_deserialize_missing_data(self):
        """It should not deserialize a Promotion with missing required fields"""
        for field in ["name", "promotion_type", "value", "start_date", "end_date"]:
            data = PromotionFactory().serialize()
            del data[field]
            with self.subTest(field=field):
                self.assertRaises(DataValidationError, Promotion().deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not deserialize data that is not a dictionary"""
        for data in ["this is not a dictionary", None, 42]:
            with self.subTest(data=data):
                self.assertRaises(DataValidationError, Promotion().deserialize, data)

    def test_deserialize_bad_values(self):
        """It should not deserialize fields with the wrong type or format"""
        bad_values = {
            "name": [None, 123, "", "a" * 64],
            "promotion_type": ["FREE_LUNCH", 1, None],
            "value": ["twenty", None, True, -5],
            "product_id": ["abc", 1.5, True],
            "start_date": ["not-a-date", 20260101, None],
            "end_date": ["2026-13-45", None],
            "active": ["yes", 1],
        }
        for field, values in bad_values.items():
            for value in values:
                data = PromotionFactory().serialize()
                data[field] = value
                with self.subTest(field=field, value=value):
                    self.assertRaises(DataValidationError, Promotion().deserialize, data)

    def test_deserialize_name_at_max_length(self):
        """It should allow a name that is exactly 63 characters"""
        data = PromotionFactory().serialize()
        data["name"] = "a" * 63
        promotion = Promotion().deserialize(data)
        self.assertEqual(promotion.name, data["name"])

    def test_deserialize_end_date_before_start_date(self):
        """It should not deserialize a Promotion that ends before it starts"""
        data = PromotionFactory().serialize()
        data["start_date"] = "2026-06-30"
        data["end_date"] = "2026-06-01"
        self.assertRaises(DataValidationError, Promotion().deserialize, data)

    def test_deserialize_same_day_promotion(self):
        """It should allow a Promotion that starts and ends on the same day"""
        data = PromotionFactory().serialize()
        data["start_date"] = data["end_date"] = "2026-11-27"
        promotion = Promotion().deserialize(data)
        self.assertEqual(promotion.start_date, promotion.end_date)

    def test_deserialize_percentage_over_100(self):
        """It should not deserialize a PERCENTAGE_OFF Promotion over 100%"""
        data = PromotionFactory(promotion_type=PromotionType.PERCENTAGE_OFF).serialize()
        data["value"] = 150
        self.assertRaises(DataValidationError, Promotion().deserialize, data)

    def test_deserialize_amount_over_100(self):
        """It should allow an AMOUNT_OFF Promotion over 100"""
        data = PromotionFactory(promotion_type=PromotionType.AMOUNT_OFF).serialize()
        data["value"] = 150
        promotion = Promotion().deserialize(data)
        self.assertEqual(promotion.value, Decimal("150"))

    def test_deserialize_bogo_with_zero_value(self):
        """It should deserialize a BOGO Promotion with a value of 0"""
        data = PromotionFactory(promotion_type=PromotionType.BOGO).serialize()
        data["value"] = 0
        promotion = Promotion().deserialize(data)
        self.assertEqual(promotion.value, Decimal("0"))

    def test_deserialize_bogo_with_nonzero_value(self):
        """It should not deserialize a BOGO Promotion with a value other than 0"""
        for value in [1, 0.5, 100]:
            data = PromotionFactory(promotion_type=PromotionType.BOGO).serialize()
            data["value"] = value
            with self.subTest(value=value):
                self.assertRaises(DataValidationError, Promotion().deserialize, data)

    ######################################################################
    #  Q U E R I E S
    ######################################################################

    def test_find_by_name(self):
        """It should Find Promotions by name"""
        promotions = PromotionFactory.create_batch(5)
        for promotion in promotions:
            promotion.create()
        name = promotions[0].name
        count = len([p for p in promotions if p.name == name])
        found = Promotion.find_by_name(name)
        self.assertEqual(found.count(), count)
        for promotion in found:
            self.assertEqual(promotion.name, name)

    def test_find_by_product_id(self):
        """It should Find Promotions by product_id"""
        for product_id in [101, 101, 202, None]:
            PromotionFactory(product_id=product_id).create()
        found = Promotion.find_by_product_id(101)
        self.assertEqual(found.count(), 2)
        for promotion in found:
            self.assertEqual(promotion.product_id, 101)

    def test_find_storewide(self):
        """It should Find store-wide Promotions"""
        for product_id in [101, None, None]:
            PromotionFactory(product_id=product_id).create()
        found = Promotion.find_storewide()
        self.assertEqual(found.count(), 2)
        for promotion in found:
            self.assertIsNone(promotion.product_id)

    def test_find_by_promotion_type(self):
        """It should Find Promotions by promotion_type"""
        types = [PromotionType.BOGO, PromotionType.BOGO, PromotionType.AMOUNT_OFF]
        for promotion_type in types:
            PromotionFactory(promotion_type=promotion_type).create()
        found = Promotion.find_by_promotion_type(PromotionType.BOGO)
        self.assertEqual(found.count(), 2)
        for promotion in found:
            self.assertEqual(promotion.promotion_type, PromotionType.BOGO)

    def test_find_by_active(self):
        """It should Find Promotions by active status"""
        for active in [True, True, False]:
            PromotionFactory(active=active).create()
        self.assertEqual(Promotion.find_by_active(True).count(), 2)
        self.assertEqual(Promotion.find_by_active(False).count(), 1)

    def test_find_active_on(self):
        """It should Find active Promotions running on a given date"""
        running = PromotionFactory(start_date=date(2026, 6, 1), end_date=date(2026, 6, 30), active=True)
        ends_today = PromotionFactory(start_date=date(2026, 5, 1), end_date=date(2026, 6, 15), active=True)
        deactivated = PromotionFactory(start_date=date(2026, 6, 1), end_date=date(2026, 6, 30), active=False)
        expired = PromotionFactory(start_date=date(2026, 5, 1), end_date=date(2026, 5, 31), active=True)
        future = PromotionFactory(start_date=date(2026, 7, 1), end_date=date(2026, 7, 31), active=True)
        for promotion in [running, ends_today, deactivated, expired, future]:
            promotion.create()
        found = Promotion.find_active_on(date(2026, 6, 15))
        self.assertEqual({p.id for p in found}, {running.id, ends_today.id})

    def test_find_by_value(self):
        """It should Find Promotions by value"""
        promotion = PromotionFactory(promotion_type=PromotionType.AMOUNT_OFF, value=Decimal("12.34"))
        promotion.create()
        found = Promotion.find_by_value(Decimal("12.34")).all()
        self.assertEqual([p.id for p in found], [promotion.id])
        self.assertEqual(Promotion.find_by_value(Decimal("99.99")).count(), 0)

    def test_find_by_start_and_end_date(self):
        """It should Find Promotions by start_date and end_date"""
        promotion = PromotionFactory(start_date=date(2026, 5, 1), end_date=date(2026, 5, 31))
        promotion.create()
        self.assertEqual(Promotion.find_by_start_date(date(2026, 5, 1)).count(), 1)
        self.assertEqual(Promotion.find_by_end_date(date(2026, 5, 31)).count(), 1)
        self.assertEqual(Promotion.find_by_start_date(date(2026, 6, 1)).count(), 0)
        self.assertEqual(Promotion.find_by_end_date(date(2026, 6, 30)).count(), 0)

    def test_find_by_attributes(self):
        """It should Find Promotions matching all given attributes"""
        promotion = PromotionFactory(product_id=4242, active=True)
        promotion.create()
        PromotionFactory(product_id=4242, active=False).create()
        found = Promotion.find_by_attributes(product_id=4242, active=True).all()
        self.assertEqual([p.id for p in found], [promotion.id])
        self.assertEqual(Promotion.find_by_attributes().count(), 2)
