# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Kleine http server om echte transacties vanuit de NHB applicaties af te handelen tijdens een test.

    Luistert op localhost poort 8125

    Simuleert de Mollie API, inclusief fout-situaties
"""

# used example: https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime
import json

MY_PORT = 8125

MY_URL_BASE = 'http://localhost:%s' % MY_PORT
MY_URL_SELF = MY_URL_BASE + '/v2/payments/tr_%s'                              # payment_id
MY_URL_CHECKOUT = MY_URL_BASE + '/checkout/select-issuer/ideal/%s'            # payment_id
MY_URL_DASHBOARD = MY_URL_BASE + '/dashboard/org_12345677/payments/tr_%s'     # payment_id


class MyServer(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # no logging please
        pass

    @staticmethod
    def _get_timestamp(minutes=0):
        stamp = datetime.datetime.now()
        if minutes != 0:
            stamp += datetime.timedelta(minutes=minutes)
        return stamp.isoformat()

    def _read_json_body(self):
        json_data = dict()
        content_type = self.headers.get('content-type', '')
        if content_type.lower() == 'application/json':
            content_len = int(self.headers.get('content-length', 0))
            if content_len:
                data = self.rfile.read(content_len)
                json_data = json.loads(data)
        else:
            print('[ERROR] {websim} Unexpected Content-Type: %s' % repr(content_type))

        return json_data

    def _write_response(self, status_code, json_data):
        data = json.dumps(json_data)
        datalen = len(data)

        self.send_response(status_code)
        self.send_header('Content-type', 'application/hal+json')
        self.send_header('Content-length', str(datalen))
        self.end_headers()

        # stuur de data zelf
        if datalen > 0:
            self.wfile.write(data.encode())  # convert string to bytes

    # noinspection PyTypeChecker
    def do_GET(self):
        print("[DEBUG] {websim} GET request,\nPath: %s\nHeaders:\n%s" % (str(self.path), str(self.headers)))

        if self.path.startswith('/v2/payments'):
            data = self._read_json_body()
            print('[DEBUG] {websim} GET data: %s' % repr(data))

            # else:
            #     special = self.path.split('/')[-2]
            #     # print('[DEBUG] {websim} spl=%s, special=%s' % (self.path.split('/'), repr(special)))
            #     if special in ('404', '500'):
            #         # /bondspas/404/<bondsnummer>
            #         special = int(special)
            #         self.send_response(special)
            #         # noinspection PyTypeChecker
            #         self.send_header('Content-length', 0)
            #         self.end_headers()
            #
            #     elif special == '43':
            #
            #         self.send_response(200)
            #         self.send_header('Content-type', 'application/pdf')
            #         # skip content-type header
            #         self.end_headers()
            #
            #     else:
            #         # geen valide bondsnummer
            #         self.send_response(404)
            #         self.end_headers()

        # internal server error
        self.send_response(500)
        self.end_headers()

    def do_POST(self):
        # print("[DEBUG] {websim} POST request,\nPath: %s\nHeaders:\n%s" % (str(self.path), str(self.headers)))

        if self.path.startswith('/v2/payments'):
            data = self._read_json_body()
            # print('[DEBUG] {websim} POST data: %s' % repr(data))

            try:
                webhook_url = data['webhookUrl']
                redirect_url = data['redirectUrl']
                description = data['description']
                amount = data['amount']
                currency = amount['currency']
                value = amount['value']
            except KeyError:
                self.send_response(400)     # 400 = bad request
            else:
                # print('[DEBUG] {websim} POST: description=%s' % description)

                payment_id = '1234AbcdEFGH'

                resp = dict()
                resp['resource'] = 'payment'
                resp['id'] = 'tr_%s' % payment_id
                resp['mode'] = 'test'
                resp['createAt'] = self._get_timestamp()
                resp['expiresAt'] = self._get_timestamp(minutes=15)
                resp['amount'] = {'value': value, 'currency': currency}
                resp['description'] = description
                resp['method'] = 'ideal'
                resp['metadata'] = None
                resp['status'] = 'open'
                resp['isCancelable'] = False
                resp['profileId'] = 'ofl_Ab1235ef'
                resp['sequenceType'] = 'oneoff'
                resp['redirectUrl'] = redirect_url
                resp['webhookUrl'] = webhook_url
                resp['_links'] = links = dict()
                links['self'] = {'href': MY_URL_SELF % payment_id, 'type': 'application/hal+json'}
                links['checkout'] = {'href': MY_URL_CHECKOUT % payment_id, 'type': 'text/html'}
                links['dashboard'] = {'href': MY_URL_DASHBOARD % payment_id, 'type': 'text/html'}
                # links['documentation'] =

                test_code = 0
                if description.startswith('Test betaling '):
                    test_code = description[14:]

                if test_code == "42":
                    self._write_response(200, resp)


        # internal server error
        self.send_response(500)
        self.end_headers()

def main():
    print('[INFO] Starting test payment http server on port %s' % MY_PORT)
    httpd = HTTPServer(('localhost', MY_PORT), MyServer)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")

    print('[INFO] Stopping test payment http server')
    httpd.server_close()


if __name__ == '__main__':          # pragma: no branch
    main()
else:
    import inspect
    print("Unsupported websim_betaal.py import. Stack: %s" % inspect.stack(0))

# end of file
