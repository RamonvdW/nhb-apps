# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Kleine http server om echte transacties vanuit de applicatie af te handelen tijdens een test.

    Luistert op localhost poort 8126

    Simuleert de e-mail dienst API, inclusief fout-situatie
"""

# used example: https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class MyServer(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # no logging please
        pass

    def handle_get_directions(self, url_encoded_args):
        # split the request
        args = url_encoded_args.replace('%2C', ',').replace('+', ' ')
        spl = args.split('&')
        # print('args:', repr(spl))

        if 'destination=incompleet' in args:
            # onvolledig antwoord geven
            data = {
                "geocoded_waypoints": [],  # list of dicts
                "routes": [],
                "status": "OK",
            }

        elif 'destination=geef fout' in args:
            # fout terug geven
            data = {
                "status": "STATUS_ERROR",
            }

        else:
            leg1 = {
                "distance": {"text": "15.4km", "value": 15444},
                "duration": {"text": "17 mins", "value": 1030},
                "end_address": "whatever",
                "end_location": {"lat": 0.0, "lng": 0.0},
                "start_address": "where ever",
                "start_location": {"lat": 1.0, "lng": 1.1},
                "steps": [],  # not used
                "traffic_speed_entry": [],
                "via_waypoints": []
            }

            route1 = {
                "bounds": {'northeast': {'lat': 0.0, 'lng': 0.0},
                           'southwest': {'lat': 1.0, 'lng': 1.0}},
                "copyrights": "yeah",
                "legs": [
                    leg1,
                ],
                "overview_polyline": {"points": "some_encoding"},
                "summary": "N2",
                "warnings": [],
                "waypoint_order": []
            }

            data = {
                "geocoded_waypoints": [],  # list of dicts
                "routes": [
                    route1,
                ],
                "status": "OK",
            }

        data = json.dumps(data)
        enc_data = data.encode()  # convert string to bytes
        enc_data_len = len(enc_data)

        self.send_response(200)
        self.send_header('Content-type', 'application/hal+json')
        self.send_header('Content-length', str(enc_data_len))
        self.end_headers()

        # stuur de data zelf
        if enc_data_len > 0:
            self.wfile.write(enc_data)
            self.wfile.flush()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def handle_get_geocode(self, url_encoded_args):
        # split the request
        args = url_encoded_args.replace('%2C', ',').replace('+', ' ')
        spl = args.split('&')
        # print('args:', repr(spl))

        if '123ERR ' in args:
            # fout status
            data = {
                "results": [],
                "status": "UNKNOWN_ERROR",
            }

        elif '0000XX ' in args:
            # leeg resultaat
            data = {
                "results": [],
                "status": "OK",
            }

        elif '42GEEN' in args:
            result1 = {
                "geometry": {
                    "location": {"lat": 42.0, "long": 5.123},
                },
            }

            data = {
                "results": [
                    result1,
                ],
                "status": "OK",
            }

        else:
            result1 = {
                "address_components": [
                    {
                        "long_name": "42",
                        "short_name": "42",
                        "types": ["street_number"],
                    },
                    {
                        "long_name": "Straatnaam",
                        "short_name": "Straatnaam",
                        "types": ["route"],
                    },
                    {
                        "long_name": "City",
                        "short_name": "City",
                        "types": ["locality", "political"],
                    },
                    {
                        "long_name": "Netherlands",
                        "short_name": "NL",
                        "types": ["country", "political"],
                    },
                    {
                        "long_name": "1234 AB",
                        "short_name": "1234 AB",
                        "types": ["postal_code"],
                    }
                ],
                "formatted_address": "Straatnaam 42, 1234 AB City, Netherlands",
                "geometry": {
                    "bounds": {'northeast': {'lat': 30.0, 'lng': 3.0},
                               'southwest': {'lat': 50.0, 'lng': 6.0}},
                    "location": {"lat": 42.0, "lng": 5.123},
                },
                "place_id": "whatever",
                "types": ["premise"],
            }

            data = {
                "results": [
                    result1,
                ],
                "status": "OK",
            }

        data = json.dumps(data)
        enc_data = data.encode()  # convert string to bytes
        enc_data_len = len(enc_data)

        self.send_response(200)
        self.send_header('Content-type', 'application/hal+json')
        self.send_header('Content-length', str(enc_data_len))
        self.end_headers()

        # stuur de data zelf
        if enc_data_len > 0:
            self.wfile.write(enc_data)
            self.wfile.flush()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_GET(self):
        # print("GET request,\nPath: %s\nHeaders:\n%s" % (str(self.path), str(self.headers)))

        if self.path.startswith('/maps/api/directions/json?'):
            return self.handle_get_directions(self.path[26:])

        elif self.path.startswith('/maps/api/geocode/json?'):
            return self.handle_get_geocode(self.path[23:])

        self.send_response(404)


def main():
    print('[INFO] Starting test gmaps http server on port 8126')
    httpd = HTTPServer(('localhost', 8126), MyServer)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")

    print('[INFO] Stopping test gmaps http server')
    httpd.server_close()


if __name__ == '__main__':          # pragma: no branch
    main()
else:
    import inspect
    print("Unsupported websim_gmaps.py import. Stack: %s" % inspect.stack(0))

# end of file

