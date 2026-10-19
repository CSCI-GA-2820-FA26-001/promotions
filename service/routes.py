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

from flask import jsonify, request, abort
from flask import current_app as app  # Import Flask application
from service.models import Promotion, DataValidationError, db  # noqa: F401 pylint: disable=unused-import
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Return information about the Promotions service"""
    return jsonify({
        "name": "Promotions Service",
        "version": "1.0",
        "url": "/promotions"
    }), status.HTTP_200_OK


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

# Todo: Place your REST API code here ...


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
    """List all Promotions"""
    app.logger.info("Request to list all Promotions")

    promotions = Promotion.all()
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
