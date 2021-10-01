# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Kleine http server om echte transacties vanuit de NHB applicaties af te handelen tijdens een test.

    Luistert op localhost poort 8124

    Simuleert de bondspas downloader API, inclusief fout-situatie
"""

# used example: https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

from http.server import BaseHTTPRequestHandler, HTTPServer
import time


class MyServer(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # no logging please
        pass

    def do_GET(self):
        print("GET request,\nPath: %s\nHeaders:\n%s" % (str(self.path), str(self.headers)))
        # self.path is the url

        if self.path.startswith('/bondspas/'):
            bondsnummer = self.path.split('/')[-1]
            try:
                bondsnummer = int(bondsnummer)
            except ValueError:
                # geen valide bondsnummer
                self.send_response(404)
            else:
                if 100000 < bondsnummer < 199999:
                    data = "abcdefghijklmnopqrstuvwxyz_0123456789_ABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
                    data *= int((150 * 1024) / len(data))  # make 150kByte
                    datalen = len(data)

                    self.send_response(200)
                    self.send_header('Content-type', 'application/pdf')
                    self.send_header('Content-length', datalen)
                    self.end_headers()

                    # stuur het bestand zelf
                    self.wfile.write(data.encode())      # convert string to bytes
                else:
                    # geen valide bondsnummer
                    self.send_response(404)

        else:
            # internal server error
            self.send_response(500)


def main():
    print('[INFO] Starting test bondspas http server on port 8124')
    httpd = HTTPServer(('localhost', 8124), MyServer)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")

    print('[INFO] Stopping test bondspas http server')
    httpd.server_close()


if __name__ == '__main__':          # pragma: no branch
    main()
else:
    import inspect
    print("Unsupported websim_bondspas.py import. Stack: %s" % inspect.stack(0))

# end of file

