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
import threading
import datetime
import requests     # voor de callback
import string
import socket
import json
import time
import copy


MY_PORT = 8125

MY_URL_BASE = 'http://localhost:%s' % MY_PORT
MY_URL_SELF = MY_URL_BASE + '/v2/payments/%s'                              # payment_id
MY_URL_CHECKOUT = MY_URL_BASE + '/checkout/select-issuer/ideal/%s'         # payment_id
MY_URL_DASHBOARD = MY_URL_BASE + '/dashboard/org_12345677/payments/%s'     # payment_id
MY_URL_CHECKOUT_DONE = MY_URL_BASE + '/checkout/done/%s'


def out_debug(msg):
    print('[DEBUG] {websim_betaal} ' + msg)


def out_warning(msg):
    print('[WARNING] {websim_betaal} ' + msg)


def out_error(msg):
    print('[ERROR] {websim_betaal} ' + msg)


def out_info(msg):
    print('[INFO] {websim_betaal} ' + msg)


class Payments(object):

    """ Payments administration, with persistent storage
        This implementation does not support concurrency.
    """

    _fname = 'websim_data.json'
    _id_chars = string.ascii_uppercase + string.digits + string.ascii_lowercase

    def __init__(self):
        self.payments = dict()      # ["payment_id"] = dict()
        self._load()
        self._unique = 0
        for lp in range(100):
            self._generate_unique_payment_id()

    def _load(self):
        try:
            data = open(self._fname, 'r').read()
        except (OSError, IOError) as exc:
            normaal = False
            try:
                if exc.errno == 2:
                    out_info('Starting with a clean payments memory')
                    normaal = True
            except KeyError:
                pass
            if not normaal:
                out_error('Could not load payments admin: %s' % str(exc))
        else:
            self.payments = json.loads(data)

    def save(self):
        data = json.dumps(self.payments, indent=4, sort_keys=True)
        open(self._fname, 'w').write(data)

    def get_payment_if_exists(self, payment_id):
        if payment_id in self.payments:
            return self.payments[payment_id]
        return None

    def get_or_create_payment(self, payment_id):
        """ Returns:
            payment dict, is_created
        """
        if payment_id in self.payments:
            return self.payments[payment_id], False     # False means not newly created

        self.payments[payment_id] = payment = dict()
        return payment, True                            # True means: newly created

    def _generate_unique_payment_id(self):
        """ Mollie payment identifiers start with tr_ followed by 10 positions
            using digits and both upper- and lowercase letters.
        """
        # construct unique number from the current date/time
        now = datetime.datetime.now()

        # split microseconds into 4 parts
        rest = now.microsecond >> 6     # ignore lowest 6 bits
        micro1 = rest % 64
        rest = rest >> 6
        micro2 = rest % 64
        rest = rest >> 6
        micro3 = rest % 64

        self._unique = (self._unique + 1) % 64

        # put the parts in some consistent order, 10 parts
        parts = [
            self._unique,
            micro3,
            now.second,
            now.hour,
            int(now.year / 64),
            now.month,
            micro1,
            now.day,
            now.minute,
            micro2,
            int(now.year % 64),
        ]
        # out_debug('parts: %s' % repr(parts))

        # encode the parts into the available characters
        new_id = "tr_"
        id_chars_len = len(self._id_chars)
        for nr in parts:
            while nr >= id_chars_len:
                nr -= id_chars_len
            # while
            new_id += self._id_chars[nr]
        # for
        # out_debug('generated id: %s' % repr(new_id))
        return new_id

    def create_new_payment(self):
        payment_id = self._generate_unique_payment_id()
        self.payments[payment_id] = payment = dict()

        payment_without_prefix = payment_id[3:]

        payment['mode'] = 'test'
        payment['resource'] = 'payment'
        payment['id'] = payment_id
        payment['profileId'] = 'ofl_Ab1235ef'
        payment['sequenceType'] = 'oneoff'
        payment['_links'] = links = dict()
        links['self'] = {'href': MY_URL_SELF % payment_without_prefix, 'type': 'application/hal+json'}
        links['checkout'] = {'href': MY_URL_CHECKOUT % payment_without_prefix, 'type': 'text/html'}
        links['dashboard'] = {'href': MY_URL_DASHBOARD % payment_without_prefix, 'type': 'text/html'}
        # links['documentation'] =

        return payment_id, payment


# global
payments = Payments()
monitor_keep_running = True


def monitor_payment_changes():
    # wait some time, to ensure POST is possible (allow runserver to load)
    for lp in range(5):
        time.sleep(1)
        if not monitor_keep_running:
            return
    # for

    # out_info('Starting monitoring of payment status changes')

    while monitor_keep_running:
        # check for changes
        for payment_id, data in payments.payments.items():
            try:
                status = data['status']
                webhook_url = data['webhookUrl']
            except KeyError:
                # geen status of geen webhook
                pass
            else:
                try:
                    reported_status = data['reported_status']
                except KeyError:
                    reported_status = ''

                if reported_status != status:
                    if status != 'open':
                        # roep de webhook aan
                        try:
                            r = requests.post(webhook_url, data={'id': payment_id})
                        except requests.exceptions.ConnectionError as exc:
                            out_warning('Failed to invoked webhook: %s' % repr(exc))
                        else:
                            out_debug('Webhook POST result with payment_id=%s: %s, %s' % (payment_id,
                                                                                          r.status_code,
                                                                                          r.reason))

                            if r.status_code == 200:
                                data['reported_status'] = status
                                payments.save()
        # for

        time.sleep(1)
        if monitor_keep_running:
            time.sleep(1)

    # while


class MyHandler(BaseHTTPRequestHandler):
    """ This class handles an https request
        A new instance is created for every request, so not storage possible inside.
    """

    def log_message(self, fmt, *args):
        # no logging please
        pass

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
            out_error('Unexpected Content-Type: %s' % repr(content_type))

        return json_data

    def _write_response(self, status_code, json_data):

        json_data = copy.deepcopy(json_data)
        try:
            del json_data['reported_status']    # voor intern gebruik
        except KeyError:
            pass

        data = json.dumps(json_data)
        enc_data = data.encode()            # convert string to bytes
        enc_data_len = len(enc_data)

        self.send_response(status_code)
        self.send_header('Content-type', 'application/hal+json')
        self.send_header('Content-length', str(enc_data_len))
        self.end_headers()

        if len(data) != enc_data_len:
            out_warning('write_response: lengths difference: %s, %s' % (len(data), enc_data_len))

        # stuur de data zelf
        if enc_data_len > 0:
            self.wfile.write(enc_data)
            self.wfile.flush()

    def _handle_get_payment_status(self, payment_id):
        out_debug('GET payment_id: %s' % repr(payment_id))

        resp = payments.get_payment_if_exists(payment_id)
        if resp:
            # exists, so return
            self._write_response(200, resp)
        else:
            # onbekende payment_id
            self.send_response(404)
            self.end_headers()

    def _handle_get_checkout(self, payment_id):
        out_debug('GET checkout: payment_id=%s' % repr(payment_id))

        resp = payments.get_payment_if_exists(payment_id)
        if not resp:
            # onbekende payment_id
            out_warning('GET checkout: unknown payment_id=%s' % repr(payment_id))
            resp = {'status': 404, 'title': 'Not found'}
            self._write_response(200, resp)
            return

        status = resp['status']
        out_debug('status is %s' % repr(status))

        if status != 'open':
            redirect_url = resp['redirectUrl']
            out_debug('GET checkout: redirect to %s' % repr(redirect_url))
            self.send_response(302)  # 302 = redirect
            self.send_header('Location', redirect_url)
            self.end_headers()
            return

        page = '<!DOCTYPE html><html lang="nl">'
        page += '<head><title>Betalen</title>'
        page += """<style>
button {
font-size: 20px;
padding: 10px;
border-radius: 5px;
box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.14), 0 3px 1px -2px rgba(0, 0, 0, 0.12), 0 1px 5px 0 rgba(0, 0, 0, 0.2);
}
</style></head>"""
        page += '<body style="background:lightgrey">'
        page += '<div  style="text-align:center; margin-top:10%; width:250px; background:white; margin-left:auto; margin-right:auto; padding:25px; border-radius:20px; color:black; font-size:20px; box-shadow: 0 5px 5px 0 rgba(0, 0, 0, 0.14), 0 3px 1px -2px rgba(0, 0, 0, 0.12), 0 1px 5px 0 rgba(0, 0, 0, 0.2);">'

        page += '<p style="color:red">Dit is slechts een simulatie</p>'

        page += '<p>%s</p>' % resp['description']

        amount = resp['amount']
        page += '<p>%s %s</p>' % (amount['value'], amount['currency'])

        if status == 'open':
            page += """
<form method="post" action="{{url}}">
    <input type="hidden" name="status" value="pay">
    <button style="margin:20px">Volledig betalen</button>
</form>
<form method="post" action="{{url}}">
    <input type="hidden" name="status" value="pay10">
    <button style="margin:20px">Tientje betalen</button>
</form>
<form method="post" action="{{url}}">
    <input type="hidden" name="status" value="cancel">
    <button style="margin:20px">Afbreken</button>
</form>
<form method="post" action="{{url}}">
    <input type="hidden" name="status" value="expire">
    <button style="margin:20px">Timeout</button>
</form>               
            """

        page += '<p style="color:red">Dit is slechts een simulatie</p>'
        page += '</div></body></html>'

        payment_id_zonder_prefix = payment_id[3:]
        url = MY_URL_CHECKOUT_DONE % payment_id_zonder_prefix
        data = page.replace('{{url}}', url)

        enc_data = data.encode('utf-8')  # convert string to bytes
        enc_data_len = len(enc_data)

        if len(data) != enc_data_len:
            out_warning('GET checkout: lengths difference: %s, %s' % (len(data), enc_data_len))

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(enc_data_len))
        self.end_headers()

        # stuur de data zelf
        if enc_data_len > 0:
            self.wfile.write(enc_data)
            self.wfile.flush()

    # noinspection PyTypeChecker
    def do_GET(self):               # noqa
        # get rid of trivial requests we do not support, to avoid logging them
        if self.path.startswith('/favicon.ico'):
            self.send_response(404)     # not found
            self.end_headers()
            return

        # out_debug("GET request,\nPath: %s\nHeaders:\n%s" % (str(self.path), str(self.headers)))
        out_debug('GET %s' % repr(self.path))

        if self.path.startswith('/v2/payments/'):
            # get payment status
            auth = self.headers.get('authorization')
            if auth and auth.startswith('Bearer '):
                api_key = auth[7:]
            else:
                # mandatory header ontbreekt: stuur json met "status": 401, "title": "Unauthorized request"
                resp = {'status': 404, 'title': 'Unauthorized request'}
                self._write_response(200, resp)
                return

            payment_id = self.path[13:13 + 30]
            self._handle_get_payment_status(payment_id)

        elif self.path.startswith('/checkout/select-issuer/'):
            # /checkout/select-issues/method/payment_id
            pos = self.path.rfind('/')
            payment_id = 'tr_' + self.path[pos + 1:]
            self._handle_get_checkout(payment_id)

        else:
            # internal server error
            self.send_response(500)
            self.end_headers()

    def _handle_post_create_payment(self, data):
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

        payment_id, resp = payments.create_new_payment()

        resp['createAt'] = self._get_timestamp()
        resp['expiresAt'] = self._get_timestamp(minutes=15)
        resp['amount'] = {
                'value': value,
                'currency': currency,
        }
        resp['description'] = description
        resp['method'] = 'ideal'
        resp['metadata'] = None
        resp['status'] = 'open'
        resp['isCancelable'] = False
        resp['redirectUrl'] = redirect_url
        resp['webhookUrl'] = webhook_url

        payments.save()

        self._write_response(200, resp)

    def _change_payment_status(self, payment, gekozen_status):
        payment_id = payment['id']
        out_debug('Payment %s status %s --> %s' % (repr(payment_id), repr(payment['status']), repr(gekozen_status)))

        if payment['status'] == 'open' and gekozen_status in ('pay', 'pay10'):
            value_to_pay = float(payment['amount']['value'])
            if gekozen_status == 'pay10':
                try:
                    value_settled = float(payment['settlementAmount']['value'])
                except KeyError:
                    value_settled = 0.0
                value_settled += 10.0
                value_settled = min(value_to_pay, value_settled)
            else:
                value_settled = value_to_pay
                payment['status'] = 'paid'
                del payment['isCancelable']
                del payment['_links']['checkout']
            payment['paidAt'] = self._get_timestamp()
            payment['amountRefunded'] = {
                'currency': payment['amount']['currency'],
                'value': '0.00',
            }
            payment['amountRemaining'] = {
                'currency': payment['amount']['currency'],
                'value': payment['amount']['value'],
            }
            payment['locale'] = 'en_NL'
            payment['countryCode'] = 'NL'
            if payment['method'] == 'ideal':
                payment['details'] = {
                    'consumerName': 'T. TEST',
                    'consumerAccount': 'NL72RABO0110438885',      # noqa
                    'consumerBic': 'RABONL2U',                    # noqa
                }
            payment['settlementAmount'] = {
                'currency': payment['amount']['currency'],
                'value': '%.2f' % value_settled,
            }

        elif payment['status'] == 'open' and gekozen_status == 'cancel':
            payment['status'] = 'canceled'
            payment['cancelledAt'] = self._get_timestamp()
            del payment['isCancelable']
            del payment['_links']['checkout']

        elif payment['status'] == 'open' and gekozen_status == 'expire':
            payment['status'] = 'expired'
            payment['expiredAt'] = self._get_timestamp()
            del payment['isCancelable']
            del payment['expiresAt']
            del payment['_links']['checkout']

        payments.save()

    def _handle_post_checkout_done(self, payment_id, body):
        # user has pressed one of the buttons on the checkout page
        # the url contains the action keyword

        resp = payments.get_payment_if_exists(payment_id)
        if not resp:
            # onbekende payment_id
            out_debug('POST checkout done: Onbekende payment_id=%s' % repr(payment_id))
            self.send_response(404)
            self.end_headers()
            return

        # doe de update
        if body == b'status=pay':
            self._change_payment_status(resp, 'pay')
        elif body == b'status=pay10':
            self._change_payment_status(resp, 'pay10')
        elif body == b'status=cancel':
            self._change_payment_status(resp, 'cancel')
        elif body == b'status=expire':
            self._change_payment_status(resp, 'expire')
        else:
            out_debug('POST checkout done: Niet ondersteunde methode voor payment_id %s: %s' % (repr(payment_id),
                                                                                                repr(body)))
            self.send_response(404)
            self.end_headers()
            return

        redirect_url = resp['redirectUrl']
        out_debug('POST checkout done: redirect_url=%s' % repr(redirect_url))
        self.send_response(302)         # 302 = redirect
        self.send_header('Location', redirect_url)
        self.end_headers()

        # monitor roept de webhook aan

    def do_POST(self):              # noqa
        # out_debug("POST request,\nPath: %s\nHeaders:\n%s" % (str(self.path), str(self.headers)))
        out_debug('POST %s' % repr(self.path))

        # FUTURE: validate api key
        # foute api key: stuur json met "status": 401, "title": "Unauthorized request"

        if self.path.startswith('/v2/payments'):
            auth = self.headers.get('authorization')
            if auth and auth.startswith('Bearer '):
                api_key = auth[7:]
            else:
                # mandatory header ontbreekt: stuur json met "status": 401, "title": "Unauthorized request"
                resp = {'status': 404, 'title': 'Unauthorized request'}
                self._write_response(200, resp)
                return

            # de body is een json file
            data = self._read_json_body()
            if not data:
                resp = {'status': 404, 'title': 'Bad request'}
                self._write_response(200, resp)
                return

            # geen payment_id, want die gaan we aanmaken
            out_debug('POST create payment: data=%s' % repr(data))
            self._handle_post_create_payment(data)

        elif self.path.startswith('/checkout/done/'):
            # user has pressed one of the buttons on the checkout page
            # the url contains the action keyword

            # geen api check, want dit is intern aan de checkout kant

            # haal de payment_id uit de url
            pos = self.path.rfind('/')
            payment_id = 'tr_' + self.path[pos + 1:]
            out_debug('POST checkout done: payment_id=%s' % repr(payment_id))

            # haal de body binnen
            content_len = int(self.headers.get('Content-Length'))
            if content_len > 1024:
                # slecht verzoek
                self.send_response(500)
                self.end_headers()
                return
            body = self.rfile.read(content_len)
            out_debug('POST checkout done: body=%s' % repr(body))

            self._handle_post_checkout_done(payment_id, body)

        else:
            # onbekende URL
            self.send_response(500)
            self.end_headers()


class MyServerThread(threading.Thread):
    def __init__(self, addr, sock):
        super().__init__()
        self._addr = addr
        self._sock = sock
        self.daemon = True
        self.start()

    @staticmethod
    def dummy():
        # this method is used as function for service_bind and server_close for the HTTP daemon
        return None

    def run(self):
        httpd = HTTPServer(self._addr, MyHandler, bind_and_activate=False)      # noqa

        # prevent the HTTP server from re-binding every handler.
        # see https://stackoverflow.com/questions/46210672/
        httpd.socket = self._sock
        httpd.server_bind = self.dummy
        httpd.server_close = self.dummy
        httpd.serve_forever()


def main():

    # maak een thread aan waarmee we de payment status changes kunnen genereren
    monitor_thread = threading.Thread(target=monitor_payment_changes)
    monitor_thread.start()

    out_info('Starting CPSP server on port %s' % MY_PORT)

    addr = ('localhost', MY_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)      # nodig voor Linux
    sock.bind(addr)
    sock.listen(5)      # 5 = queue depth, maar ivm connection keep-alive ook max. aantal verbindingen

    # start 5 server instanties
    x = [MyServerThread(addr, sock),        # noqa
         MyServerThread(addr, sock),
         MyServerThread(addr, sock),
         MyServerThread(addr, sock),
         MyServerThread(addr, sock)]

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("")

    out_info('Stopping test payment http server')

    out_debug('Waiting for thread to finish')
    global monitor_keep_running
    monitor_keep_running = False
    monitor_thread.join()


if __name__ == '__main__':          # pragma: no branch
    main()
else:
    import inspect
    out_debug("Direct import is not supported. Origin: %s" % inspect.stack(0))

# end of file
