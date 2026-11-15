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
from flask import abort, jsonify, request
from flask import current_app as app  # Import Flask application
from flask_restx import Resource, fields
from service import api  # pylint: disable=cyclic-import
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
        jsonify(
            {
                "name": "Promotions Service",
                "version": "1.0",
                "url": api.url_for(PromotionCollection),
            }
        ),
        status.HTTP_200_OK,
    )


######################################################################
# GET HEALTH
######################################################################
@app.route("/health")
def health():
    """Return the health status of the service"""
    return jsonify({"status": "OK"}), status.HTTP_200_OK


######################################################################
#  S W A G G E R   M O D E L S
######################################################################
ns = api.namespace("promotions", description="Promotion operations")

create_model = api.model(
    "PromotionCreate",
    {
        "name": fields.String(
            required=True,
            max_length=63,
            description="The name of the Promotion",
            example="Autumn Sale",
        ),
        "promotion_type": fields.String(
            required=True,
            enum=list(PromotionType.__members__),
            description="The type of Promotion",
            example="PERCENTAGE_OFF",
        ),
        "value": fields.Float(
            required=True,
            description=(
                "The discount value: a percent for PERCENTAGE_OFF (max 100), "
                "a currency amount for AMOUNT_OFF, and 0 for BOGO"
            ),
            example=15,
        ),
        "product_id": fields.Integer(
            description="The product the Promotion applies to; omit or null for store-wide",
            example=101,
        ),
        "start_date": fields.Date(
            required=True,
            description="The first day of the Promotion (YYYY-MM-DD)",
            example="2026-10-01",
        ),
        "end_date": fields.Date(
            required=True,
            description="The last day of the Promotion (YYYY-MM-DD), on or after start_date",
            example="2026-10-31",
        ),
        "active": fields.Boolean(
            description="Whether the Promotion is active (defaults to true)",
            example=True,
        ),
    },
)

promotion_model = api.inherit(
    "Promotion",
    create_model,
    {
        "id": fields.Integer(readOnly=True, description="The unique id assigned internally by the service"),
        "created_at": fields.DateTime(readOnly=True, description="When the Promotion was created"),
        "updated_at": fields.DateTime(readOnly=True, description="When the Promotion was last updated"),
    },
)

# Query parameters accepted when listing Promotions (see FILTER_PARSERS)
LIST_PARAMS = {
    "id": {"description": "Filter by Promotion id", "type": "integer"},
    "promotion_type": {
        "description": "Filter by Promotion type",
        "type": "string",
        "enum": list(PromotionType.__members__),
    },
    "value": {"description": "Filter by discount value", "type": "number"},
    "product_id": {"description": "Filter by product id", "type": "integer"},
    "start_date": {"description": "Filter by start date (YYYY-MM-DD)", "type": "string"},
    "end_date": {"description": "Filter by end date (YYYY-MM-DD)", "type": "string"},
    "active": {"description": "Filter by active flag", "type": "boolean"},
}


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
#  PATH: /promotions
######################################################################
@ns.route("", strict_slashes=False)
class PromotionCollection(Resource):
    """Handles all interactions with collections of Promotions"""

    @ns.doc("list_promotions", params=LIST_PARAMS)
    @ns.response(400, "A query parameter has an invalid value")
    @ns.response(200, "Success", [promotion_model])
    def get(self):
        """List all Promotions, optionally filtered by query parameters"""
        app.logger.info("Request to list Promotions")

        filters = _parse_filters(request.args)
        promotions = Promotion.find_by_attributes(**filters) if filters else Promotion.all()
        results = [promotion.serialize() for promotion in promotions]

        return results, status.HTTP_200_OK

    @ns.doc("create_promotions")
    @ns.expect(create_model)
    @ns.response(201, "Promotion created", promotion_model)
    @ns.response(400, "The posted data was not valid")
    @ns.response(415, "Content-Type must be application/json")
    def post(self):
        """Create a Promotion from the request body"""
        app.logger.info("Request to create a Promotion")
        if not request.is_json:
            abort(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                description="Content-Type must be application/json",
            )

        promotion = Promotion()
        promotion.deserialize(request.get_json())
        promotion.create()

        location = api.url_for(PromotionResource, promotion_id=promotion.id, _external=True)
        return promotion.serialize(), status.HTTP_201_CREATED, {"Location": location}


######################################################################
#  PATH: /promotions/{promotion_id}
######################################################################
@ns.route("/<int:promotion_id>")
@ns.param("promotion_id", "The Promotion identifier")
class PromotionResource(Resource):
    """Handles all interactions with a single Promotion"""

    @ns.doc("get_promotions")
    @ns.response(404, "Promotion not found")
    @ns.response(200, "Success", promotion_model)
    def get(self, promotion_id):
        """Read a Promotion"""
        app.logger.info("Request to read Promotion with id: %s", promotion_id)
        return _find_or_404(promotion_id).serialize(), status.HTTP_200_OK

    @ns.doc("update_promotions")
    @ns.expect(create_model)
    @ns.response(404, "Promotion not found")
    @ns.response(400, "The posted Promotion data was not valid")
    @ns.response(200, "Promotion updated", promotion_model)
    def put(self, promotion_id):
        """Update an existing Promotion"""
        app.logger.info("Request to update Promotion with id: %s", promotion_id)
        promotion = _find_or_404(promotion_id)

        try:
            promotion.deserialize(request.get_json())
            promotion.update()
        except DataValidationError:
            db.session.rollback()
            raise

        return promotion.serialize(), status.HTTP_200_OK

    @ns.doc("delete_promotions")
    @ns.response(204, "Promotion deleted")
    def delete(self, promotion_id):
        """Delete a Promotion (always returns 204, even if it does not exist)"""
        app.logger.info("Request to delete Promotion with id: %s", promotion_id)

        promotion = Promotion.find(promotion_id)
        if promotion:
            promotion.delete()

        return "", status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /promotions/{promotion_id}/activate
######################################################################
@ns.route("/<int:promotion_id>/activate")
@ns.param("promotion_id", "The Promotion identifier")
class ActivateResource(Resource):
    """Activate action on a Promotion"""

    @ns.doc("activate_promotions")
    @ns.response(404, "Promotion not found")
    @ns.response(200, "Promotion activated", promotion_model)
    def put(self, promotion_id):
        """Activate a Promotion"""
        app.logger.info("Request to activate Promotion with id: %s", promotion_id)
        return _set_active(promotion_id, True), status.HTTP_200_OK


######################################################################
#  PATH: /promotions/{promotion_id}/deactivate
######################################################################
@ns.route("/<int:promotion_id>/deactivate")
@ns.param("promotion_id", "The Promotion identifier")
class DeactivateResource(Resource):
    """Deactivate action on a Promotion"""

    @ns.doc("deactivate_promotions")
    @ns.response(404, "Promotion not found")
    @ns.response(200, "Promotion deactivated", promotion_model)
    def put(self, promotion_id):
        """Deactivate a Promotion"""
        app.logger.info("Request to deactivate Promotion with id: %s", promotion_id)
        return _set_active(promotion_id, False), status.HTTP_200_OK


######################################################################
#  H E L P E R S
######################################################################


def _find_or_404(promotion_id):
    """Return the Promotion with the given id or abort with 404"""
    promotion = Promotion.find(promotion_id)
    if promotion is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            description=f"Promotion with id {promotion_id} was not found",
        )
    return promotion


def _set_active(promotion_id, active):
    """Set the active flag on a Promotion and return it serialized"""
    promotion = _find_or_404(promotion_id)
    promotion.active = active
    promotion.update()
    return promotion.serialize()


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
