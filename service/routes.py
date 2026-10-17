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

from flask import abort, jsonify
from flask import current_app as app  # Import Flask application
from service.models import Promotion  # noqa: F401 pylint: disable=unused-import
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

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
    """List all Promotions"""
    app.logger.info("Request to list all Promotions")

    promotions = Promotion.all()
    results = [promotion.serialize() for promotion in promotions]

    return jsonify(results), status.HTTP_200_OK
