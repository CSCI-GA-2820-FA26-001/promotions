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
Module: error_handlers
"""
from flask import jsonify
from flask import current_app as app  # Import Flask application
from werkzeug.exceptions import HTTPException
from service import api
from service.models import DataValidationError
from . import status

ERROR_NAMES = {
    status.HTTP_400_BAD_REQUEST: "Bad Request",
    status.HTTP_404_NOT_FOUND: "Not Found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Method not Allowed",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "Unsupported media type",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
}


def error_body(code, message, name=None):
    """Build the JSON body shared by every error response"""
    return {
        "status": code,
        "error": name or ERROR_NAMES.get(code, "Error"),
        "message": message,
    }


######################################################################
# Error Handlers
#
# Flask-RESTX intercepts exceptions raised under /api before Flask's own
# handlers run, so HTTP errors are registered with both the Flask app and
# the API. Both return the same JSON body.
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """Handles Value Errors from bad data with 400_BAD_REQUEST"""
    message = str(error)
    app.logger.warning(message)
    return error_body(status.HTTP_400_BAD_REQUEST, message), status.HTTP_400_BAD_REQUEST


@app.errorhandler(HTTPException)
def http_error(error):
    """Handles every HTTP error (400, 404, 405, 415, 500, ...) with a JSON body"""
    body, code = _http_error_body(error)
    return jsonify(body), code


@api.errorhandler(HTTPException)
def api_http_error(error):
    """Handles every HTTP error (400, 404, 405, 415, 500, ...) with a JSON body"""
    return _http_error_body(error)


@api.errorhandler
def api_default_error(error):
    """Handles unexpected exceptions with 500_INTERNAL_SERVER_ERROR"""
    message = str(error)
    app.logger.error(message)
    return (
        error_body(status.HTTP_500_INTERNAL_SERVER_ERROR, message),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _http_error_body(error):
    """Return the JSON body and status code for an HTTPException"""
    code = error.code or status.HTTP_500_INTERNAL_SERVER_ERROR
    message = str(error)
    if code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        app.logger.error(message)
    else:
        app.logger.warning(message)
    return error_body(code, message, ERROR_NAMES.get(code, error.name)), code
