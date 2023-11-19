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
import time
import json

class MyServer(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # no logging please
        pass

    def do_GET(self):
        print("GET request,\nPath: %s\nHeaders:\n%s" % (str(self.path), str(self.headers)))

        if self.path.startswith('/maps/api/directions/json?'):
            # split the request
            args = self.path[26:]
            args = args.replace('%2C', ',').replace('+', ' ')
            spl = args.split('&')
            # print('args:', repr(spl))

            leg1 = {
                "distance": {"text": "15.4km", "value": 15444},
                "duration": {"text": "17 mins", "value": 1030},
                "end_address": "whatever",
                "end_location": {"lat": 0.0, "lng": 0.0},
                "start_address": "where ever",
                "start_location": {"lat": 1.0, "lng": 1.1},
                "steps": [],        # not used
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
                "geocoded_waypoints": [],       # list of dicts
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
            return

        self.send_response(404)

    def do_POST(self):
        data_len = int(self.headers['Content-Length'])
        data = self.rfile.read(data_len).decode('utf-8')
        print("POST request\nPath: %s\nHeaders:\n%s\n\nBody:\n%s" % (str(self.path), str(self.headers), data))

        if "faal" in data:
            self.send_error(401,     # mailgun: 'unauthorized'
                            "Gesimuleerde faal")
        else:
            if "delay" in data:
                time.sleep(3)
            self.send_response(200)

        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))


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

