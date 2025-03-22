# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from google.maps.routing_v2.services.routes.transports.rest import RoutesRestTransport
from google.maps.routing_v2.services.routes.transports.base import DEFAULT_CLIENT_INFO, RoutesTransport
from google.auth.api_key import Credentials
from typing import cast, Callable

"""
    Mock om Google Routes te overtuigen met onze simulator te communiceren
"""


class WebsimTransport(RoutesRestTransport):

    _ignore_credentials = 1

    def __init__(
        self,
        *,
        host: str = "routes.googleapis.com",
        credentials=None,
        credentials_file=None,
        scopes=None,
        client_cert_source_for_mtls=None,
        quota_project_id=None,
        client_info=DEFAULT_CLIENT_INFO,
        always_use_jwt_access=False,
        url_scheme="https",
        interceptor=None,
        api_audience=None,
    ) -> None:

        self._credentials = Credentials('my_key')

        super().__init__(
                    host="localhost:8126",
                    credentials=self._credentials,
                    client_info=client_info,
                    always_use_jwt_access=always_use_jwt_access,
                    url_scheme="http",
                    api_audience=api_audience)


def get_routes_transport():
    transport = cast(Callable[..., RoutesTransport], WebsimTransport)
    return transport()


# end of file
