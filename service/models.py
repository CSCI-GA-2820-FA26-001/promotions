"""
Models for Promotion

All of the models are stored in this module
"""

import logging
from datetime import date
from decimal import Decimal
from enum import Enum
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class PromotionType(Enum):
    """Enumeration of valid Promotion types"""

    PERCENTAGE_OFF = "PERCENTAGE_OFF"  # value is a percent, e.g. 20 = 20% off
    AMOUNT_OFF = "AMOUNT_OFF"  # value is a currency amount, e.g. 20 = $20 off
    BOGO = "BOGO"  # buy one get one free


class Promotion(db.Model):  # pylint: disable=too-many-instance-attributes
    """
    Class that represents a Promotion

    A Promotion with no product_id applies store-wide.
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    promotion_type = db.Column(db.Enum(PromotionType), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)  # None = store-wide
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f"<Promotion {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Promotion to the database
        """
        logger.info("Creating %s", self.name)
        self.id = None  # pylint: disable=invalid-name
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        """
        Updates a Promotion to the database
        """
        logger.info("Saving %s", self.name)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
        """Removes a Promotion from the data store"""
        logger.info("Deleting %s", self.name)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Promotion into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "promotion_type": self.promotion_type.name,
            "value": float(self.value),
            "product_id": self.product_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def deserialize(self, data):
        """
        Deserializes a Promotion from a dictionary

        The id and timestamps are managed by the database and are ignored.

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.name = _parse_name(data["name"])
            self.promotion_type = _parse_promotion_type(data["promotion_type"])
            self.value = _parse_value(data["value"], self.promotion_type)
            self.product_id = _parse_product_id(data.get("product_id"))
            self.start_date = _parse_date("start_date", data["start_date"])
            self.end_date = _parse_date("end_date", data["end_date"])
            self.active = _parse_active(data.get("active", True))
        except KeyError as error:
            raise DataValidationError("Invalid Promotion: missing " + error.args[0]) from error
        except (TypeError, AttributeError) as error:
            raise DataValidationError(
                "Invalid Promotion: body of request contained bad or no data " + str(error)
            ) from error

        if self.end_date < self.start_date:
            raise DataValidationError("Invalid Promotion: end_date must be on or after start_date")
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the Promotions in the database"""
        logger.info("Processing all Promotions")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a Promotion by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all Promotions with the given name

        Args:
            name (string): the name of the Promotions you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_product_id(cls, product_id):
        """Returns all Promotions for the given product

        Args:
            product_id (int): the id of the product the Promotions apply to
        """
        logger.info("Processing product_id query for %s ...", product_id)
        return cls.query.filter(cls.product_id == product_id)

    @classmethod
    def find_storewide(cls):
        """Returns all store-wide Promotions (those with no product_id)"""
        logger.info("Processing store-wide query ...")
        return cls.query.filter(cls.product_id.is_(None))

    @classmethod
    def find_by_promotion_type(cls, promotion_type):
        """Returns all Promotions of the given type

        Args:
            promotion_type (PromotionType): the type of the Promotions you want to match
        """
        logger.info("Processing promotion_type query for %s ...", promotion_type.name)
        return cls.query.filter(cls.promotion_type == promotion_type)

    @classmethod
    def find_by_active(cls, active=True):
        """Returns all Promotions by their active status

        Args:
            active (boolean): True for active Promotions, False for inactive
        """
        logger.info("Processing active query for %s ...", active)
        return cls.query.filter(cls.active == active)

    @classmethod
    def find_active_on(cls, on_date):
        """Returns all active Promotions that are running on the given date

        Args:
            on_date (date): the date to check, start and end dates are inclusive
        """
        logger.info("Processing active-on query for %s ...", on_date)
        return cls.query.filter(
            cls.active.is_(True),
            cls.start_date <= on_date,
            cls.end_date >= on_date,
        )


######################################################################
#  D E S E R I A L I Z E   H E L P E R S
######################################################################


def _parse_name(value):
    if not isinstance(value, str) or not value.strip():
        raise DataValidationError("Invalid Promotion: name must be a non-empty string")
    return value


def _parse_promotion_type(value):
    if not isinstance(value, str) or value not in PromotionType.__members__:
        raise DataValidationError(
            f"Invalid Promotion: promotion_type must be one of {list(PromotionType.__members__)}"
        )
    return PromotionType[value]


def _parse_value(value, promotion_type):
    # bool is a subclass of int, so exclude it explicitly
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DataValidationError("Invalid Promotion: value must be a number")
    if value < 0:
        raise DataValidationError("Invalid Promotion: value must not be negative")
    if promotion_type == PromotionType.PERCENTAGE_OFF and value > 100:
        raise DataValidationError("Invalid Promotion: PERCENTAGE_OFF value must not exceed 100")
    return Decimal(str(value))


def _parse_product_id(value):
    if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
        raise DataValidationError("Invalid Promotion: product_id must be an integer or null")
    return value


def _parse_date(field, value):
    if not isinstance(value, str):
        raise DataValidationError(f"Invalid Promotion: {field} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise DataValidationError(f"Invalid Promotion: {field} is not a valid date: {value}") from error


def _parse_active(value):
    if not isinstance(value, bool):
        raise DataValidationError("Invalid Promotion: active must be a boolean")
    return value
