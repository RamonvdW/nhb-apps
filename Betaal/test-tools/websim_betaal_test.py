# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Kleine http server om echte transacties vanuit de applicatie af te handelen tijdens een test.

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

payments = dict()       # [payment_id] = dict()
next_payment_id = 0


class MyServer(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # no logging please
        pass

    @staticmethod
    def _get_next_payment_id():
        global next_payment_id
        next_payment_id += 1
        return next_payment_id

    @staticmethod
    def _get_timestamp(minutes=0):
        stamp = datetime.datetime.now()
        if minutes != 0:
            stamp += datetime.timedelta(minutes=minutes)
        return stamp.isoformat()        # 2022-04-23T16:54:51.953365

    def _read_json_body(self):
        json_data = dict()
        content_type = self.headers.get('content-type', '')
        if content_type.lower() == 'application/json':
            content_len = int(self.headers.get('content-length', 0))
            if content_len:
                data = self.rfile.read(content_len)
                json_data = json.loads(data)
        else:
            print('[ERROR] {websim_betaal_test} Unexpected Content-Type: %s' % repr(content_type))

        return json_data

    def _write_response(self, status_code, json_data):
        data = json.dumps(json_data)
        enc_data = data.encode()            # convert string to bytes
        enc_data_len = len(enc_data)

        self.send_response(status_code)
        self.send_header('Content-type', 'application/hal+json')
        self.send_header('Content-length', str(enc_data_len))
        self.end_headers()

        # stuur de data zelf
        if enc_data_len > 0:
            self.wfile.write(enc_data)

    def _handle_get_v2_payments(self, resp):

        if 'status' in resp and resp['status'] == 'open':
            # transition to another state
            description = resp['description']
            if description.startswith('Test betaling '):
                test_code = description[14:]

                if test_code == '39':
                    resp['status'] = 'failed'

                elif test_code == '40':
                    resp['status'] = 'pending'

                elif test_code == '41':
                    # keep status=open
                    pass

                elif test_code.startswith('42') or test_code == '49':
                    # transition to 'paid'
                    resp['status'] = 'paid'
                    resp['paidAt'] = self._get_timestamp()
                    resp['amountRefunded'] = refund = dict()
                    refund['currency'] = resp['amount']['currency']
                    refund['value'] = '0.00'
                    resp['amountRemaining'] = remaining = dict()
                    remaining['currency'] = resp['amount']['currency']
                    remaining['value'] = resp['amount']['value']
                    resp['locale'] = 'en_NL'
                    resp['countryCode'] = 'NL'
                    resp['details'] = details = dict()
                    if resp['method'] == 'ideal':
                        details['consumerName'] = 'T. TEST'
                        details['consumerAccount'] = 'NL72RABO0110438885'  # noqa
                        details['consumerBic'] = 'RABONL2U'  # noqa

                    elif resp['method'] == 'creditcard':
                        details['cardHolder'] = 'T. TEST'
                        details['cardNumber'] = '12345678901234'
                        details['cardLabel'] = 'Dankort'  # noqa
                        details['cardCountryCode'] = 'DK'

                    elif resp['method'] == 'paypal':
                        details['consumerName'] = 'T. TEST'
                        details['consumerAccount'] = 'paypaluser@somewhere.nz'
                        details['paypalReference'] = '9AL35361CF606152E'
                        details['paypalPayerId'] = 'WDJJHEBZ4X2LY'  # noqa
                        details['paypalFee'] = {
                            'currency': resp['amount']['currency'],
                            'value': '2.50'}

                    elif resp['method'] == 'bancontact':
                        details['consumerName'] = None
                        details['consumerAccount'] = 'BE72RABO0110438885'  # noqa
                        details['consumerBic'] = 'AXABBE22'  # noqa

                    elif resp['method'] == 'banktransfer':
                        details['bankName'] = 'Test bank'
                        details['bankAccount'] = 'BE72RABO0110438885'  # noqa
                        details['bankBic'] = 'AXABBE22'  # noqa
                        details['transferReference'] = 'Whatever'

                    value = float(resp['amount']['value']) - 0.26
                    if test_code != '429':
                        resp['settlementAmount'] = {'currency': resp['amount']['currency'],
                                                    'value': '%.2f' % value}
                    del resp['isCancelable']
                    del resp['_links']['checkout']
                    # '_links': {'changePaymentState': {
                    #            'href': 'https://www.mollie.com/checkout/test-mode?method=ideal&token=3.210mge',
                    #            'type': 'text/html'},

                elif test_code == "43":
                    # transition to 'canceled'
                    resp['status'] = 'canceled'
                    resp['canceledAt'] = self._get_timestamp()
                    resp['locale'] = 'en_NL'
                    resp['countryCode'] = 'NL'
                    del resp['isCancelable']
                    del resp['expiresAt']
                    del resp['_links']['checkout']

                elif test_code in ("44", "45"):
                    # transition to 'expired'
                    resp['status'] = 'expired'
                    del resp['expiresAt']
                    resp['expiredAt'] = self._get_timestamp()
                    resp['locale'] = 'en_NL'
                    resp['countryCode'] = 'NL'
                    del resp['_links']['checkout']
                    del resp['_links']['dashboard']

                if test_code in ("425", "426"):
                    details = resp['details']
                    details['consumerName'] = details['cardHolder'] = ''  # zorg dat de velden bestaan
                    del details['consumerName']
                    del details['cardHolder']
                elif test_code == "427":
                    resp['amountRemaining']['value'] = '1&2'
                elif test_code == "428":
                    resp['amountRemaining']['currency'] = 'DKK'

        self._write_response(200, resp)

    def _handle_get_v2_refunds_list_all(self):
        refunds = list()

        refund = {
            'resource': 'refund',
            'id': 're_PX7Jurz8XA',
            'amount': {
                'value': '30.40',
                'currency': 'EUR'
            },
            'status': 'refunded',
            'createdAt': '2024-09-02T09:54:46+00:00',
            'description': 'Terugbetaling Oranje fanshirt',
            'metadata': None,
            'paymentId': 'tr_M4VKcjTjqT',
            'settlementAmount': {
                'value': '-30.40',
                'currency': 'EUR'
            },
            '_links': {
                'self': {
                    'href': MY_URL_BASE + '/v2/payments/tr_M4VKcjTjqT/refunds/re_PX7Jurz8XA',
                    'type': 'application/hal+json',
                },
                'payment': {
                    'href': MY_URL_BASE + '/v2/payments/tr_M4VKcjTjqT',
                    'type': 'application/hal+json',
                }
            }
        }
        refunds.append(refund)

        # one with errors
        refund = {
            'resource': 'refund',
            'id': 're_PX7Jurz8XA',
            'amount': {
                'value': '30.40',
                'currency': 'DKK'                           # wrong currency
            },
            'status': 'refunded',
            'createdAt': '02-09-2024T09:54:46+00:00',       # wrong format
            'description': 'Terugbetaling bad createdAt',
            'metadata': None,
            'paymentId': 'tr_M4VKcjTjqT',
            'settlementAmount': {
                'value': '-30.40',
                'currency': 'EUR'
            },
            '_links': {
                'self': {
                    'href': MY_URL_BASE + '/v2/payments/tr_M4VKcjTjqT/refunds/re_PX7Jurz8XA',
                    'type': 'application/hal+json',
                },
                'payment': {
                    'href': MY_URL_BASE + '/v2/payments/tr_M4VKcjTjqT',
                    'type': 'application/hal+json',
                }
            }
        }
        refunds.append(refund)

        # one with errors
        refund = {
            'resource': 'refund',
            'id': 're_PX7Jurz8XA',
            'amount': None,                 # bad amount
            'status': 'refunded',
            'createdAt': '2024-09-02T09:54:46+00:00',
            'description': 'Terugbetaling bad createdAt',
            'metadata': None,
            'paymentId': 'tr_M4VKcjTjqT',
            '_links': {
                'self': {
                    'href': MY_URL_BASE + '/v2/payments/tr_M4VKcjTjqT/refunds/re_PX7Jurz8XA',
                    'type': 'application/hal+json',
                },
                'payment': {
                    'href': MY_URL_BASE + '/v2/payments/tr_M4VKcjTjqT',
                    'type': 'application/hal+json',
                }
            }
        }
        refunds.append(refund)

        # one with errors
        refund = {
            'resource': 'refund',
            'id': 're_PX7Jurz8XA',
            'amount': {
                'value': '30.##',           # bad number
                'currency': 'EUR'
            },
            'status': 'refunded',
            'createdAt': '2024-09-02T09:54:46+00:00',
            'description': 'Terugbetaling Oranje fanshirt',
            'metadata': None,
            'paymentId': 'tr_M4VKcjTjqT',
            'settlementAmount': {
                'value': '-30.40',
                'currency': 'EUR'
            },
            '_links': {
                'self': {
                    'href': MY_URL_BASE + '/v2/payments/tr_M4VKcjTjqT/refunds/re_PX7Jurz8XA',
                    'type': 'application/hal+json',
                },
                'payment': {
                    'href': MY_URL_BASE + '/v2/payments/tr_M4VKcjTjqT',
                    'type': 'application/hal+json',
                }
            }
        }
        refunds.append(refund)

        resp = {
            '_embedded': {
                'refunds': refunds,
            },
            'count': len(refunds),
        }

        self._write_response(200, resp)

    # noinspection PyTypeChecker
    def do_GET(self):   # noqa
        # print("[DEBUG] {websim_betaal_test} GET request,\nPath: %s\nHeaders:\n%s" % (str(self.path),
        #                                                                              str(self.headers)))

        auth = self.headers.get('authorization')
        if auth and auth.startswith('Bearer '):
            api_key = auth[7:]
        else:
            api_key = None

        if self.path.startswith('/v2/payments/'):
            payment_id = self.path[13:13+30]
            # print('[DEBUG] {websim_betaal_test} GET payment_id: %s' % repr(payment_id))

            try:
                resp = payments[payment_id]
            except KeyError:
                # onbekende payment_id
                self.send_response(404)
                self.end_headers()
            else:
                self._handle_get_v2_payments(resp)
            return

        if api_key != 'test_bad':
            if self.path.startswith('/v2/refunds'):
                # pos = self.path.find('?limit=')
                # if pos > 0:
                #     limit = int(self.path[pos+7:])
                # else:
                #     limit = 250
                self._handle_get_v2_refunds_list_all()
                return

            print('{websim_betaal_test} Unsupported: %s' % repr(self.path))

        # internal server error
        self.send_response(500)
        self.end_headers()

    def do_POST(self):      # noqa
        # print("[DEBUG] {websim_betaal_test} POST request,\nPath: %s\nHeaders:\n%s" % (str(self.path),
        #                                                                               str(self.headers)))

        auth = self.headers.get('authorization')
        if auth and auth.startswith('Bearer '):
            api_key = auth[7:]
        else:
            api_key = None

        if api_key == 'test_fixed':
            payment_id = 'tr_1234AbcdEFGH'
        else:
            payment_id = 'tr_1234AbcdEF%02d' % self._get_next_payment_id()

        if not self.path.startswith('/v2/payments'):
            # internal server error
            self.send_response(500)
            self.end_headers()
            return

        data = self._read_json_body()
        # print('[DEBUG] {websim_betaal_test} POST data: %s' % repr(data))

        try:
            webhook_url = data['webhookUrl']
            redirect_url = data['redirectUrl']
            description = data['description']
            amount = data['amount']
            currency = amount['currency']
            value = amount['value']
        except KeyError:
            self.send_response(400)     # 400 = bad request
            self.end_headers()
            return

        # print('[DEBUG] {websim_betaal_test} POST: description=%s' % repr(description))

        if "Dit geeft code 500" in description:
            self.send_response(500)
            self.end_headers()
            return

        payments[payment_id] = resp = dict()
        resp['resource'] = 'payment'
        resp['id'] = payment_id
        resp['mode'] = 'test'
        resp['createAt'] = self._get_timestamp()
        resp['expiresAt'] = self._get_timestamp(minutes=15)
        resp['amount'] = {'value': value, 'currency': currency}
        resp['amountRefunded'] = {'value': '0.00', 'currency': currency}
        resp['amountRemaining'] = {'value': value, 'currency': currency}
        resp['description'] = description
        # Possible values for 'method' (2024-10-06):
        #   alma applepay bacs bancomatpay bancontact banktransfer belfius blik creditcard directdebit eps      # noqa
        #   giftcard ideal kbc mybank paypal paysafecard przelewy24 satispay trustly twint                      # noqa
        resp['method'] = 'ideal'
        resp['metadata'] = None
        resp['status'] = 'open'
        resp['isCancelable'] = False
        resp['profileId'] = 'ofl_Ab1235ef'
        resp['sequenceType'] = 'oneoff'     # noqa
        resp['redirectUrl'] = redirect_url
        resp['webhookUrl'] = webhook_url
        resp['_links'] = links = dict()
        links['self'] = {'href': MY_URL_SELF % payment_id[3:], 'type': 'application/hal+json'}
        links['checkout'] = {'href': MY_URL_CHECKOUT % payment_id[3:], 'type': 'text/html'}
        links['dashboard'] = {'href': MY_URL_DASHBOARD % payment_id[3:], 'type': 'text/html'}
        # links['documentation'] =

        if description.startswith('Test betaling '):
            test_code = description[14:]
            if test_code[-1] == '+':
                test_code = test_code[:-1]
                if webhook_url:
                    do_post_payment_change = True

            # print('POST: test_code=%s' % test_code)
            if test_code in ('421', '426', '427', '428', '429', '49'):
                resp['method'] = 'ideal'
            elif test_code in ('422', '425'):
                resp['method'] = 'creditcard'
            elif test_code == '423':
                resp['method'] = 'paypal'
            elif test_code == '424':
                resp['method'] = 'bancontact'
            elif test_code == '4291':
                resp['method'] = 'banktransfer'

            if test_code == '45':
                # bijna leeg antwoord
                payments[payment_id] = resp = dict()
                resp['metadata'] = None

            if test_code == '46':
                # foute status
                resp['status'] = 'bogus'

            if test_code == '47':
                # foute payment_id
                resp['id_original'] = resp['id']
                resp['id'] = 'tr_FoutjeBedankt'

            if test_code == '48':
                links['checkout']['href'] = 'http://way.too.long/' + "1234567890" * 50

            if test_code == '49':
                value = float(value)
                resp['amountRefunded']['value'] = round(value * 0.75, 2)
                resp['amountRemaining']['value'] = round(value * 0.25, 2)

            # 39 = failed
            # 40 = pending
            # 41 = open
            # 42 = paid
            # 43 = canceled
            # 44 = expired
            # 45 = bijna leeg antwoord (+expired?!)
            # 46 = foute status
            # 47 = foute id
            # 48 = te lange checkout URL
            # 49 = partly refunded
            if test_code in ("39", "40", "41", "42",
                             "421", "422", "423", "424", "425", "426", "427", "428", "429", "4291",
                             "43", "44", "45", "46", "47", "48", "49"):
                self._write_response(200, resp)
        else:
            # geen corner-case
            self._write_response(200, resp)


def main():
    # print('[INFO] {websim_betaal_test} Starting test payment http server on port %s' % MY_PORT)
    httpd = HTTPServer(('localhost', MY_PORT), MyServer)        # noqa

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")
    except Exception as exc:
        print('[ERROR] {websim_betaal_test} Unhandled exception:')
        print(exc)

    # print('[INFO] {websim_betaal_test} Stopping test payment http server')
    httpd.server_close()


if __name__ == '__main__':          # pragma: no branch
    main()
else:
    import inspect
    print("Unsupported websim_betaal_test.py import. Stack: %s" % inspect.stack(0))

# end of file
