# ------------------------------------------------------------------------------
# Copyright 2026 Munich Quantum Software Stack Project
#
# Licensed under the Apache License, Version 2.0 with LLVM Exceptions (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://github.com/Munich-Quantum-Software-Stack/QDMI/blob/develop/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# ------------------------------------------------------------------------------

"""MQP Dashboard Resources Module"""

from http import HTTPStatus
from typing import TypedDict
from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from eliot import log_call
import bqp_database_access as database


BLUEPRINT = Blueprint("resources", __name__)


class ResourceResponse(TypedDict):
    """Response schema for resource availability data."""

    resources: list[dict]
    available_resources: list[dict]
    restricted_resource_names: list[str]


@BLUEPRINT.get("/resources")
@jwt_required()
@log_call
def fetch_all_resources() -> tuple[ResourceResponse, HTTPStatus]:
    """
    Fetch all resources that are available to user

    Returns:
        dict: Resource list
        dict: Available resources
    """

    identity = get_jwt_identity()
    try:
        available_resources = database.resources.fetch_resources_available_to_identity(
            identity
        )
        sanitized_available_resources = [
            resource.to_dict() for resource in available_resources
        ]
        resources = database.resources.fetch_all_resources()
        sanitized_resources = [resource.to_dict() for resource in resources]

        sorted_resources_by_name = sorted(
            sanitized_resources, key=lambda x: x["name"], reverse=False
        )
        sorted_available_resources = sorted(
            sanitized_available_resources, key=lambda y: y["name"], reverse=False
        )
        restricted_resource_names = (
            database.resources.fetch_resource_names_restricted_to_identity(identity)
        )
        return {
            "resources": sorted_resources_by_name,
            "available_resources": sorted_available_resources,
            "restricted_resource_names": restricted_resource_names,
        }, HTTPStatus.OK
    except TypeError as error:
        return {"error_message": error}, HTTPStatus.FORBIDDEN
