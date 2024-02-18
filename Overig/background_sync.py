# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Helper om een een management taak te kietelen die in de achtergrond draait en wacht op een nieuwe opdracht.
    De management taak wordt typisch gebruikt om vele verzoeken 1 voor 1 af te handelen, zodat er geen
    concurrency problemen ontstaan.

    De queue met data van de verzoeken is typisch een database tabel.

    Elke taak kan met een unieke naam benaderd worden.
"""

import socket
import select


class BackgroundSync(object):
    """
        BackgroundSync: implementatie voor zowel de zendende als ontvangende kant.

        ping()          is voor de zender
        wait_for_ping() is voor de ontvanger
                        accepteert een maximale tijd om te wachten (default: 1 seconde)

        Ontvanger en zender moeten geconfigureerd worden met hetzelfde poortnummer.
        Deze kunnen het beste dus globaal gealloceerd worden, typisch in settings.py

        De manier waarop de synchronisatie gedaan wordt is niet relevant voor zender of ontvanger.
        De huidige implementation geeft geen belasting op de database.
    """

    def __init__(self, poort_nummer):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._address = ('localhost', poort_nummer)
        self._is_setup = False
        self._listener = None

    def __del__(self):
        self._sock.close()

    def _setup_receiver(self):
        if not self._is_setup:
            try:
                self._sock.bind(self._address)
            except OSError:
                # typisch: Address already in use
                pass
            else:
                self._sock.setblocking(False)
                self._is_setup = True

    def ping(self):
        self._sock.sendto(b'ping', self._address)

    def wait_for_ping(self, timeout=1.0) -> bool:
        """ returns True when a ping was received or False in case of a timeout """
        got_ping = False

        self._setup_receiver()

        if self._is_setup:
            # wait for data to arrive, or timeout
            select.select((self._sock,), (), (), timeout)

            # try to read the data, regardless of whether anything arrived
            # this works because the socket is non-blocking
            try:
                data = self._sock.recv(10)
            except BlockingIOError:
                # no data received
                pass
            else:
                # receive some data
                got_ping = True

        return got_ping


# end of file
