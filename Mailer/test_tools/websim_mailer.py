# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Kleine http server om echte transacties vanuit de applicatie af te handelen tijdens een test.

    Luistert op localhost poort 8123

    Simuleert de e-mail dienst API, inclusief fout-situatie
"""

# used example: https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

from http.server import BaseHTTPRequestHandler, HTTPServer
import time


class MyServer(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # no logging please
        pass

    # def do_GET(self):
    #    print("GET request,\nPath: %s\nHeaders:\n%s" % (str(self.path), str(self.headers)))
    #    self.send_response(200)
    #    self.send_header('Content-type', 'text/html')
    #    self.end_headers()
    #    self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):                                          # noqa
        data_len = int(self.headers['Content-Length'])
        data = self.rfile.read(data_len).decode('utf-8')
        # print("POST request\nPath: %s\nHeaders:\n%s\n\nBody:\n%s" % (str(self.path), str(self.headers), data))

        resp = ''

        if "@bounce.now" in data:
            self.send_response(422)         # postmark: inactive e-mail
            resp = '{"ErrorCode":406,"Message":"You tried to send to recipient(s) tht have been marked as inactive. "'
            resp += "Found inactive addresses: xx@bounce.now. "
            resp += "Inactive recipients are ones that have guaranteed a hard bounce, a spam complains, "
            resp += 'or a manual suppression"}'

        elif "faal" in data:
            self.send_error(401,            # mailgun: 'unauthorized'
                            "Gesimuleerde faal")
        else:
            if "delay" in data:
                time.sleep(3)
            self.send_response(200)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if resp:
            self.wfile.write(resp.encode('utf-8'))


def main():
    print('[INFO] Starting test mailer http server on port 8123')
    httpd = HTTPServer(('localhost', 8123), MyServer)           # noqa

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")

    print('[INFO] Stopping test mailer http server')
    httpd.server_close()


if __name__ == '__main__':          # pragma: no branch
    main()
else:
    import inspect
    print("Unsupported websim_mailer.py import. Stack: %s" % inspect.stack(0))

# end of file
