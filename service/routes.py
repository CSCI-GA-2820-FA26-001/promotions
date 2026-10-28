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
Promotion Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Promotions
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from flask import abort, jsonify, request, url_for
from flask import current_app as app  # Import Flask application
from service.models import (  # noqa: F401 pylint: disable=unused-import
    Promotion,
    PromotionType,
    DataValidationError,
    db,
)
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Return information about the Promotions service"""
    return (
        jsonify({"name": "Promotions Service", "version": "1.0", "url": "/promotions"}),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


@app.route("/promotions", methods=["POST"])
def create_promotion():
    """Create a promotion from the request body."""
    if not request.is_json:
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            description="Content-Type must be application/json",
        )

    promotion = Promotion()
    promotion.deserialize(request.get_json())
    promotion.create()

    collection_url = url_for("create_promotion", _external=True).rstrip("/")
    location = f"{collection_url}/{promotion.id}"
    return (
        jsonify(promotion.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location},
    )


@app.route("/promotions/<int:promotion_id>", methods=["GET"])
def read_promotion(promotion_id):
    """Read a Promotion"""
    app.logger.info("Request to read Promotion with id: %s", promotion_id)

    promotion = Promotion.find(promotion_id)
    if promotion is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Promotion with id {promotion_id} was not found",
        )

    return jsonify(promotion.serialize()), status.HTTP_200_OK


# DELETE A PROMOTION


@app.route("/promotions/<int:promotion_id>", methods=["DELETE"])
def delete_promotion(promotion_id):
    """Delete a Promotion"""
    app.logger.info("Request to delete Promotion with id: %s", promotion_id)

    promotion = Promotion.find(promotion_id)
    if promotion:
        promotion.delete()

    return "", status.HTTP_204_NO_CONTENT


# LIST ALL PROMOTIONS


@app.route("/promotions", methods=["GET"])
def list_promotions():
    """List all Promotions, optionally filtered by query parameters"""
    app.logger.info("Request to list Promotions")

    filters = _parse_filters(request.args)
    promotions = Promotion.find_by_attributes(**filters) if filters else Promotion.all()
    results = [promotion.serialize() for promotion in promotions]

    return jsonify(results), status.HTTP_200_OK


# UPDATE A PROMOTION


@app.route("/promotions/<int:promotion_id>", methods=["PUT"])
def update_promotion(promotion_id):
    """Update an existing Promotion"""
    app.logger.info("Request to update Promotion with id: %s", promotion_id)

    promotion = Promotion.find(promotion_id)

    if promotion is None:
        abort(status.HTTP_404_NOT_FOUND, "Promotion not found")

    try:
        promotion.deserialize(request.get_json())
        promotion.update()
    except DataValidationError:
        db.session.rollback()
        raise

    return jsonify(promotion.serialize()), status.HTTP_200_OK


#  A C T I O N S


@app.route("/promotions/<int:promotion_id>/activate", methods=["PUT"])
def activate_promotion(promotion_id):
    """Activate a Promotion"""
    app.logger.info("Request to activate Promotion with id: %s", promotion_id)

    promotion = Promotion.find(promotion_id)

    if promotion is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Promotion with id {promotion_id} was not found",
        )

    promotion.active = True
    promotion.update()

    return jsonify(promotion.serialize()), status.HTTP_200_OK


@app.route("/promotions/<int:promotion_id>/deactivate", methods=["PUT"])
def deactivate_promotion(promotion_id):
    """Deactivate a Promotion"""
    app.logger.info("Request to deactivate Promotion with id: %s", promotion_id)

    promotion = Promotion.find(promotion_id)

    if promotion is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Promotion with id {promotion_id} was not found",
        )

    promotion.active = False
    promotion.update()

    return jsonify(promotion.serialize()), status.HTTP_200_OK


######################################################################
#  H E L P E R S
######################################################################


def _to_int(name, text):
    try:
        return int(text)
    except ValueError:
        abort(status.HTTP_400_BAD_REQUEST, f"{name} must be an integer")


def _to_value(name, text):
    try:
        value = Decimal(text)
    except InvalidOperation:
        abort(status.HTTP_400_BAD_REQUEST, f"{name} must be a number")
    if not value.is_finite():
        abort(status.HTTP_400_BAD_REQUEST, f"{name} must be a number")
    return value


def _to_date(name, text):
    try:
        return date.fromisoformat(text)
    except ValueError:
        abort(status.HTTP_400_BAD_REQUEST, f"{name} must be an ISO date (YYYY-MM-DD)")


def _to_promotion_type(name, text):
    if text not in PromotionType.__members__:
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"{name} must be one of {list(PromotionType.__members__)}",
        )
    return PromotionType[text]


def _to_bool(name, text):
    if text.lower() not in ("true", "false"):
        abort(status.HTTP_400_BAD_REQUEST, f"{name} must be true or false")
    return text.lower() == "true"


FILTER_PARSERS = {
    "id": _to_int,
    "promotion_type": _to_promotion_type,
    "value": _to_value,
    "product_id": _to_int,
    "start_date": _to_date,
    "end_date": _to_date,
    "active": _to_bool,
}


def _parse_filters(args):
    """Convert supported query parameters to column types; unknown ones are ignored"""
    return {
        name: parser(name, args[name])
        for name, parser in FILTER_PARSERS.items()
        if name in args
    }
