
from django.conf import settings
from django.utils import timezone
from Account.models import Account
from Taken.taken import maak_taak, check_taak_bestaat
from .models import SiteFeedback
import datetime


def store_feedback(gebruiker, op_pagina, bevinding, feedback):
    """ Deze functie wordt aangeroepen vanuit de view waarin de feedback van de gebruiker
        verzameld is. Deze functie slaat de feedback op in een database tabel.
    """

    # prevent double creation (double/triple-click button)
    obj, is_new = SiteFeedback.objects.get_or_create(
                        site_versie=settings.SITE_VERSIE,
                        gebruiker=gebruiker,
                        op_pagina=op_pagina,
                        feedback=feedback,
                        is_afgehandeld=False,
                        bevinding=bevinding)

    if is_new:
        obj.toegevoegd_op = timezone.now()
        obj.save()

    # maak taken aan om door te geven dat er nieuwe feedback is
    now = timezone.now()
    taak_log = "[%s] Taak aangemaakt" % now
    taak_deadline = now + datetime.timedelta(days=7)
    taak_tekst = "Er is nieuwe Site Feedback om te bekijken"

    for account in (Account
                    .objects
                    .filter(username__in=settings.TAAK_OVER_FEEDBACK_ACCOUNTS)):

        if not check_taak_bestaat(toegekend_aan=account, beschrijving=taak_tekst):
            maak_taak(toegekend_aan=account,
                      deadline=taak_deadline,
                      aangemaakt_door=None,         # systeem
                      beschrijving=taak_tekst,
                      log=taak_log)
    # for


# end of file
