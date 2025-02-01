# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Count
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import GESLACHT_ALLE, ORGANISATIES2LONG_STR, ORGANISATIE_WA, ORGANISATIE_IFAA
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from BasisTypen.operations import get_organisatie_boogtypen, get_organisatie_klassen
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Locatie.definities import BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN
from Locatie.models import WedstrijdLocatie
from Sporter.models import get_sporter
from Vereniging.models import Vereniging
from Wedstrijden.definities import (ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS, WEDSTRIJD_STATUS_TO_STR,
                                    WEDSTRIJD_WA_STATUS_TO_STR, WEDSTRIJD_STATUS_ONTWERP, WEDSTRIJD_STATUS2URL,
                                    WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING, WEDSTRIJD_STATUS_GEACCEPTEERD,
                                    WEDSTRIJD_STATUS_GEANNULEERD, WEDSTRIJD_WA_STATUS_A, WEDSTRIJD_WA_STATUS_B,
                                    WEDSTRIJD_DUUR_MAX_DAGEN, WEDSTRIJD_BEGRENZING_TO_STR,
                                    AANTAL_SCHEIDS_GEEN_KEUZE, AANTAL_SCHEIDS_EIGEN)
from Wedstrijden.models import Wedstrijd
from types import SimpleNamespace
import datetime

TEMPLATE_WEDSTRIJDEN_WIJZIG_WEDSTRIJD = 'wedstrijden/wijzig-wedstrijd.dtl'


class WijzigWedstrijdView(UserPassesTestMixin, View):

    """ Via deze view kunnen de HWL of BB een wedstrijd wijzigen """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_WIJZIG_WEDSTRIJD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_MWZ, Rol.ROL_HWL)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'uitvoerende_vereniging',
                                         'locatie')
                         .prefetch_related('sessies',
                                           'sessies__wedstrijdklassen',
                                           'wedstrijdklassen')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL and wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
            raise PermissionDenied('Wedstrijd niet van jouw vereniging')

        context['wed'] = wedstrijd

        # zorg dat de huidige datum weer gekozen kan worden
        context['now'] = now = timezone.now()
        context['begin_jaar'] = min(now.year, wedstrijd.datum_begin.year)

        context['min_date'] = min(datetime.date(now.year, now.month, now.day), wedstrijd.datum_begin)
        context['max_date'] = datetime.date(now.year + 2, 12, 31)

        context['opt_status'] = opt_status = list()
        for code, status_str in WEDSTRIJD_STATUS_TO_STR.items():
            opt = SimpleNamespace()
            opt.status_str = status_str
            opt.selected = (code == wedstrijd.status)
            opt_status.append(opt)
        # for

        if self.rol_nu == Rol.ROL_HWL:
            if wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP:
                if not wedstrijd.is_ter_info:
                    wedstrijd.wacht_op_sessies = wedstrijd.sessies.count() == 0

                if wedstrijd.verkoopvoorwaarden_status_acceptatie:
                    context['url_next_tekst'] = 'Vraag om goedkeuring'
                    context['url_next_status'] = reverse('Wedstrijden:zet-status',
                                                         kwargs={'wedstrijd_pk': wedstrijd.pk})
            else:
                context['limit_edits'] = True

        if self.rol_nu == Rol.ROL_MWZ:

            context['wijzig_kwalificatie_scores'] = True

            if wedstrijd.status == WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING:
                wedstrijd.wacht_op_keuze_scheids = wedstrijd.aantal_scheids == AANTAL_SCHEIDS_GEEN_KEUZE

                context['url_prev_tekst'] = 'Afkeuren'
                context['url_next_tekst'] = 'Accepteren'
                context['url_next_status'] = reverse('Wedstrijden:zet-status',
                                                     kwargs={'wedstrijd_pk': wedstrijd.pk})

            elif wedstrijd.status == WEDSTRIJD_STATUS_GEACCEPTEERD:
                context['url_annuleer'] = reverse('Wedstrijden:zet-status',
                                                  kwargs={'wedstrijd_pk': wedstrijd.pk})

        if wedstrijd.status == WEDSTRIJD_STATUS_GEANNULEERD:
            context['limit_edits'] = True
            context['block_edits'] = True
            context['niet_verwijderbaar'] = True

        # bereken hoeveel dagen de wedstrijd duurt
        duur_dagen = (wedstrijd.datum_einde - wedstrijd.datum_begin).days + 1
        context['duur_dagen'] = duur_dagen

        context['opt_duur'] = opt_duur = list()
        for lp in range(WEDSTRIJD_DUUR_MAX_DAGEN):
            opt = SimpleNamespace()
            dagen = lp + 1
            opt.sel = "duur_%s" % dagen
            if dagen == 1:
                opt.keuze_str = '1 dag'
            else:
                opt.keuze_str = '%s dagen' % dagen

            opt.selected = (dagen == duur_dagen)

            opt_duur.append(opt)
        # for

        context['opt_sluit'] = opt_sluit = list()
        for lp in range(1, 14+1):
            opt = SimpleNamespace()
            opt.sel = 'sluit_%s' % lp
            opt.selected = (wedstrijd.inschrijven_tot == lp)
            opt.datum = wedstrijd.datum_begin - datetime.timedelta(days=lp)
            if lp == 1:
                opt.keuze_str = '1 dag voor aanvang'
            else:
                opt.keuze_str = '%s dagen voor aanvang' % lp

            opt_sluit.append(opt)
        # for

        context['opt_begrenzing'] = opt_begrenzing = list()
        for code, begrenzing_str in WEDSTRIJD_BEGRENZING_TO_STR.items():
            opt = SimpleNamespace()
            opt.sel = 'begrenzing_%s' % code
            opt.keuze_str = begrenzing_str
            opt.selected = (code == wedstrijd.begrenzing)
            if opt.selected:
                wedstrijd.begrenzing_str = begrenzing_str
            opt_begrenzing.append(opt)
        # for

        if wedstrijd.uitvoerende_vereniging:
            ver = wedstrijd.uitvoerende_vereniging
        else:
            ver = wedstrijd.organiserende_vereniging
        locaties = (ver
                    .wedstrijdlocatie_set
                    .exclude(zichtbaar=False)
                    .order_by('pk'))
        try:
            binnen_locatie = locaties.get(adres_uit_crm=True)
        except WedstrijdLocatie.DoesNotExist:
            binnen_locatie = None

        max_banen = 1
        context['opt_locatie'] = opt_locatie = list()
        for locatie in locaties:
            # buitenbaan aanvullen met de gegevens van de accommodatie
            locatie.keuze_str = 'Binnen accommodatie'
            if locatie.baan_type == BAAN_TYPE_BUITEN:
                locatie.keuze_str = 'Buiten accommodatie'
                if not binnen_locatie:
                    # rare situatie: wel een buitenbaan, maar geen accommodatie
                    continue        # met de for
                locatie.adres = binnen_locatie.adres
                locatie.plaats = binnen_locatie.plaats
            elif locatie.baan_type == BAAN_TYPE_EXTERN:
                locatie.keuze_str = locatie.naam

            locatie.sel = "loc_%s" % locatie.pk
            locatie.selected = (wedstrijd.locatie == locatie)
            locatie.keuze_str += ' [disciplines: %s]\n' % locatie.disciplines_str()
            locatie.keuze_str += locatie.adres_oneliner()
            opt_locatie.append(locatie)

            max_banen = max(locatie.banen_18m, locatie.banen_25m, locatie.buiten_banen, max_banen)
        # for

        wedstrijd.org_str = ORGANISATIES2LONG_STR[wedstrijd.organisatie]

        disc2str = ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS[wedstrijd.organisatie]

        wedstrijd.disc_str = (ORGANISATIES2LONG_STR[wedstrijd.organisatie] + ' / ' + disc2str[wedstrijd.discipline])

        context['opt_disc'] = opt_disc = list()
        for afk, disc in disc2str.items():
            opt = SimpleNamespace()
            opt.sel = 'disc_%s' % afk
            opt.keuze_str = disc
            opt.selected = (wedstrijd.discipline == afk)
            opt_disc.append(opt)
        # for

        # zoek uit welke wedstrijdklassen in gebruik zijn bij de sessies
        klassen_gebruikt = list()
        bogen_gebruikt = list()
        for sessie in wedstrijd.sessies.all():
            for klasse in sessie.wedstrijdklassen.select_related('boogtype').all():
                if klasse.pk not in klassen_gebruikt:
                    klassen_gebruikt.append(klasse.pk)
                    if klasse.boogtype.pk not in bogen_gebruikt:
                        bogen_gebruikt.append(klasse.boogtype.pk)
            # for
        # for

        context['opt_bogen'] = opt_bogen = list()
        gekozen_boog_pks = list(wedstrijd.boogtypen.values_list('pk', flat=True))
        for obj in get_organisatie_boogtypen(wedstrijd.organisatie):
            obj.sel = 'boog_%s' % obj.afkorting
            obj.gebruikt = (obj.pk in bogen_gebruikt)
            obj.selected = (obj.pk in gekozen_boog_pks)
            opt_bogen.append(obj)
        # for

        context['opt_klasse'] = opt_klasse = list()
        context['wedstrijd_is_a_status'] = (wedstrijd.wa_status == WEDSTRIJD_WA_STATUS_A)
        gekozen_pks = list(wedstrijd.wedstrijdklassen.values_list('pk', flat=True))
        volg_nr = 0
        code = 0
        code2klasse = dict()
        blokkeer2klasse = dict()
        for klasse in get_organisatie_klassen(wedstrijd.organisatie, gekozen_boog_pks):
            klasse.sel = 'klasse_%s' % klasse.pk
            klasse.gebruikt = (klasse.pk in klassen_gebruikt)
            klasse.selected = (klasse.pk in gekozen_pks)

            if klasse.leeftijdsklasse.wedstrijd_geslacht == GESLACHT_ALLE:
                code += 1
                klasse.code = code
                code2klasse[code] = klasse
                code += 1
                klasse.code_blokkeer = code
                blokkeer2klasse[code] = klasse
            else:
                code2klasse[code] = klasse
                klasse.code = code
                klasse.code_blokkeer = 0

            if wedstrijd.organisatie == ORGANISATIE_IFAA:
                # zet de internationale klasse afkorting erachter
                klasse.beschrijving += ' [%s]' % klasse.afkorting

            volg_nr += 1
            klasse.volg_nr = volg_nr

            opt_klasse.append(klasse)
        # for

        for klasse in opt_klasse:
            if klasse.code_blokkeer == 0:
                # verwijs terug naar de klasse die deze blokkeert
                try:
                    klasse2 = blokkeer2klasse[klasse.code]
                except KeyError:
                    # niet nodig
                    pass
                else:
                    klasse.code_blokkeer = klasse2.code
        # for
        del blokkeer2klasse

        # blokkeer checkbox als de te blokkeren klassen niet uit te zetten zijn
        for klasse in opt_klasse:
            if klasse.gebruikt and klasse.code_blokkeer > 0:
                klasse2 = code2klasse[klasse.code_blokkeer]
                if not klasse2.selected:
                    klasse2.disabled = True
        # for

        if wedstrijd.organisatie == ORGANISATIE_WA:
            context['toon_wa_status'] = True
            wedstrijd.wa_status_str = WEDSTRIJD_WA_STATUS_TO_STR[wedstrijd.wa_status]
            context['opt_wa'] = opt_wa = list()
            for afk, descr in WEDSTRIJD_WA_STATUS_TO_STR.items():
                opt = SimpleNamespace()
                opt.sel = 'wa_%s' % afk
                opt.keuze_str = descr
                opt.selected = (wedstrijd.wa_status == afk)
                opt.disabled = (afk == WEDSTRIJD_WA_STATUS_A and not wedstrijd.voorwaarden_a_status_acceptatie)
                opt_wa.append(opt)
            # for

        context['opt_aanwezig'] = aanwezig = list()
        for mins in (10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60):
            opt = SimpleNamespace()
            opt.sel = 'aanwezig_%d' % mins
            opt.keuze_str = "%d minuten" % mins
            opt.selected = (wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn == mins)
            aanwezig.append(opt)
        # for

        context['prijs_euro_normaal_str'] = str(wedstrijd.prijs_euro_normaal).replace('.', ',')
        context['prijs_euro_onder18_str'] = str(wedstrijd.prijs_euro_onder18).replace('.', ',')

        context['url_voorwaarden_a_status'] = settings.VOORWAARDEN_A_STATUS_URL
        context['url_voorwaarden_verkoop'] = settings.VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL

        # aantal banen waar uit gekozen kan worden
        max_banen = min(80, max_banen)
        context['opt_banen'] = [nr for nr in range(2, max_banen + 1)]  # 1 baan = handmatig in .dtl

        if wedstrijd.organiserende_vereniging.ver_nr in settings.WEDSTRIJDEN_KIES_UITVOERENDE_VERENIGING:
            # voor deze wedstrijd mag een andere uitvoerende vereniging gekozen worden
            context['toon_uitvoerende'] = True
            if wedstrijd.uitvoerende_vereniging:
                selected_ver_nr = wedstrijd.uitvoerende_vereniging.ver_nr
            else:
                selected_ver_nr = wedstrijd.organiserende_vereniging.ver_nr

            context['opt_uitvoerende_vers'] = (Vereniging
                                               .objects
                                               .exclude(geen_wedstrijden=True)
                                               .annotate(aantal=Count('wedstrijdlocatie'))
                                               .filter(aantal__gte=1)
                                               .order_by('ver_nr'))
            for ver in context['opt_uitvoerende_vers']:
                ver.sel = 'ver_%s' % ver.ver_nr
                ver.selected = (ver.ver_nr == selected_ver_nr)
                ver.keuze_str = ver.ver_nr_en_naam()
            # for

        if self.rol_nu == Rol.ROL_MWZ:
            context['toon_ter_info'] = True

            context['keuze_aantal_scheids'] = [
                (AANTAL_SCHEIDS_GEEN_KEUZE, 'Nog geen keuze gemaakt'),
                (AANTAL_SCHEIDS_EIGEN, 'Eigen scheidsrechters'),
                (0, 'Geen scheidsrechters'),
                (1, '1 scheidsrechter'),
                (2, '2 scheidsrechters'),
                (3, '3 scheidsrechters'),
                (4, '4 scheidsrechters'),
                (5, '5 scheidsrechters'),
                (6, '6 scheidsrechters'),
            ]

            if wedstrijd.aantal_scheids != AANTAL_SCHEIDS_GEEN_KEUZE:
                context['keuze_aantal_scheids'].pop(0)

        else:
            if wedstrijd.aantal_scheids == AANTAL_SCHEIDS_GEEN_KEUZE:
                wedstrijd.aantal_scheids_str = ''
            elif wedstrijd.aantal_scheids == 0:
                wedstrijd.aantal_scheids_str = 'Geen scheidsrechters'
            elif wedstrijd.aantal_scheids == 1:
                wedstrijd.aantal_scheids_str = '1 scheidsrechter'
            else:   # wedstrijd.aantal_scheids > 1:
                wedstrijd.aantal_scheids_str = '%s scheidsrechters' % wedstrijd.aantal_scheids

            if wedstrijd.aantal_scheids not in (0, AANTAL_SCHEIDS_GEEN_KEUZE):
                wedstrijd.url_sr_contact = reverse('Scheidsrechter:wedstrijd-hwl-contact',
                                                   kwargs={'wedstrijd_pk': wedstrijd.pk})

        context['url_opslaan'] = reverse('Wedstrijden:wijzig-wedstrijd',
                                         kwargs={'wedstrijd_pk': wedstrijd.pk})

        if wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP:
            context['url_verwijder'] = context['url_opslaan']

        if self.rol_nu == Rol.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (None, 'Wijzig wedstrijd')
            )
        else:
            context['kruimels'] = (
                (reverse('Wedstrijden:manager'), 'Wedstrijdkalender'),
                (None, 'Wijzig wedstrijd')
            )

        return render(request, self.template_name, context)

    @staticmethod
    def _verplaats_sessies(wedstrijd, oude_datum_begin):
        if wedstrijd.datum_begin == oude_datum_begin:
            return

        # bereken hoeveel dagen de wedstrijd verplaatst is
        delta = wedstrijd.datum_begin - oude_datum_begin

        # pas alle sessies aan met dezelfde hoeveelheid
        for sessie in wedstrijd.sessies.all():
            sessie.datum += delta
            sessie.save(update_fields=['datum'])
        # for

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'wedstrijdklassen',
                                           'sessies',
                                           'sessies__wedstrijdklassen')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL and wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
            raise PermissionDenied('Wedstrijd niet van jouw vereniging')

        limit_edits = False
        block_edits = False
        if self.rol_nu == Rol.ROL_HWL and wedstrijd.status != WEDSTRIJD_STATUS_ONTWERP:
            limit_edits = True

        if wedstrijd.status == WEDSTRIJD_STATUS_GEANNULEERD:
            limit_edits = True
            block_edits = True

        # verwijderen alleen toestaan in de ontwerp fase
        if wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP and request.POST.get('verwijder_wedstrijd'):
            wedstrijd.delete()
        else:
            oude_datum_begin = wedstrijd.datum_begin

            # zoek uit welke wedstrijdklassen in gebruik zijn bij de sessies
            klassen_pks_gebruikt_in_sessies = list()
            bogen_pks_gebruikt_in_sessies = list()
            for sessie in wedstrijd.sessies.all():
                for klasse in sessie.wedstrijdklassen.select_related('boogtype').all():
                    if klasse.pk not in klassen_pks_gebruikt_in_sessies:
                        klassen_pks_gebruikt_in_sessies.append(klasse.pk)
                        if klasse.boogtype.pk not in bogen_pks_gebruikt_in_sessies:
                            bogen_pks_gebruikt_in_sessies.append(klasse.boogtype.pk)
                # for
            # for

            disc2str = ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS[wedstrijd.organisatie]

            wedstrijd.titel = request.POST.get('titel', wedstrijd.titel)[:50]

            if not limit_edits:
                akkoord = request.POST.get('akkoord_verkoop', '')
                if akkoord:
                    account = get_account(request)
                    sporter = get_sporter(account)
                    wedstrijd.verkoopvoorwaarden_status_who = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                    wedstrijd.verkoopvoorwaarden_status_when = timezone.now()
                    wedstrijd.verkoopvoorwaarden_status_acceptatie = True

                datum_ymd = request.POST.get('datum_begin', '')[:10]    # afkappen voor de veiligheid
                if datum_ymd:
                    try:
                        datum = datetime.datetime.strptime(datum_ymd, '%Y-%m-%d')
                    except ValueError:
                        raise Http404('Geen valide datum')

                    datum = datetime.date(datum.year, datum.month, datum.day)
                    now = timezone.now()
                    min_date = min(datetime.date(now.year, now.month, now.day), wedstrijd.datum_begin)
                    max_date = datetime.date(now.year + 2, 12, 31)
                    if min_date <= datum <= max_date:
                        wedstrijd.datum_begin = datum

            if not limit_edits:
                duur = request.POST.get('wedstrijd_duur', '')
                if duur.startswith('duur_'):
                    try:
                        duur = int(duur[5:10])      # afkappen voor de veiligheid
                    except ValueError:
                        raise Http404('Fout in wedstrijd duur')

                    wedstrijd.datum_einde = wedstrijd.datum_begin
                    duur -= 1
                    if 1 <= duur < 5:
                        wedstrijd.datum_einde += datetime.timedelta(days=duur)

            if not block_edits:
                sluit = request.POST.get('sluit', '')
                if sluit.startswith('sluit_'):
                    try:
                        sluit = int(sluit[6:10])        # afkappen voor de veiligheid
                    except ValueError:
                        raise Http404('Fout in sluiting wedstrijd')

                    if 1 <= sluit <= 14:
                        wedstrijd.inschrijven_tot = sluit

            if not limit_edits:
                disc = request.POST.get('discipline', '')
                for afk in disc2str.keys():
                    if disc == 'disc_' + afk:
                        wedstrijd.discipline = afk
                # for

            if not limit_edits:
                wa_status = request.POST.get('wa_status', '')
                if wa_status == 'wa_%s' % WEDSTRIJD_WA_STATUS_B:
                    wedstrijd.wa_status = WEDSTRIJD_WA_STATUS_B

                elif wa_status == 'wa_%s' % WEDSTRIJD_WA_STATUS_A:
                    # moet eerst akkoord zijn gegaan met de voorwaarden
                    akkoord = request.POST.get('akkoord_a_status', '')
                    if akkoord:
                        account = get_account(request)
                        sporter = get_sporter(account)
                        wedstrijd.voorwaarden_a_status_who = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                        wedstrijd.voorwaarden_a_status_when = timezone.now()
                        wedstrijd.voorwaarden_a_status_acceptatie = True

                    if wedstrijd.voorwaarden_a_status_acceptatie:
                        wedstrijd.wa_status = WEDSTRIJD_WA_STATUS_A

                aantal_banen = request.POST.get('aantal_banen', str(wedstrijd.aantal_banen))
                try:
                    aantal_banen = int(aantal_banen[:5])        # afkappen voor de veiligheid
                except ValueError:
                    raise Http404('Fout in aantal banen')

                if 1 <= aantal_banen <= 100:
                    wedstrijd.aantal_banen = aantal_banen

                wedstrijd.scheidsrechters = request.POST.get('scheidsrechters', wedstrijd.scheidsrechters)[:500]

            if not block_edits:
                # begrenzing is "doelgroep"
                begrenzing = request.POST.get('begrenzing', '')[:20]     # afkappen voor de veiligheid
                for code in WEDSTRIJD_BEGRENZING_TO_STR.keys():
                    if begrenzing == 'begrenzing_%s' % code:
                        wedstrijd.begrenzing = code
                        break
                # for

            if not limit_edits:
                boog_pks = list()
                for boog in BoogType.objects.all():
                    if boog.pk in bogen_pks_gebruikt_in_sessies or request.POST.get('boog_%s' % boog.afkorting, ''):
                        # deze boog is gekozen
                        boog_pks.append(boog.pk)
                # for
                wedstrijd.boogtypen.set(boog_pks)

            wedstrijd.contact_naam = request.POST.get('contact_naam', wedstrijd.contact_naam)[:50]
            wedstrijd.contact_email = request.POST.get('contact_email', wedstrijd.contact_email)[:150]
            wedstrijd.contact_website = request.POST.get('contact_website', wedstrijd.contact_website)[:100]
            wedstrijd.contact_telefoon = request.POST.get('contact_telefoon', wedstrijd.contact_telefoon)[:50]

            wedstrijd.bijzonderheden = request.POST.get('bijzonderheden', '')[:1000]

            wedstrijd.uitvoerende_vereniging = None
            if wedstrijd.organiserende_vereniging.ver_nr in settings.WEDSTRIJDEN_KIES_UITVOERENDE_VERENIGING:
                # voor deze wedstrijd mag een andere uitvoerende vereniging gekozen worden
                data = request.POST.get('uitvoerend', '')
                if data:
                    for ver in (Vereniging
                                .objects
                                .exclude(geen_wedstrijden=True)
                                .annotate(aantal=Count('wedstrijdlocatie'))
                                .filter(aantal__gte=1)):
                        sel = 'ver_%s' % ver.ver_nr
                        if data == sel:
                            wedstrijd.uitvoerende_vereniging = ver
                    # for
                    if wedstrijd.uitvoerende_vereniging == wedstrijd.organiserende_vereniging:
                        wedstrijd.uitvoerende_vereniging = None

            data = request.POST.get('locatie', '')
            if data:
                if wedstrijd.uitvoerende_vereniging:
                    ver = wedstrijd.uitvoerende_vereniging
                else:
                    ver = wedstrijd.organiserende_vereniging
                for locatie in (ver
                                .wedstrijdlocatie_set
                                .exclude(zichtbaar=False)):
                    sel = 'loc_%s' % locatie.pk
                    if sel == data:
                        wedstrijd.locatie = locatie
                        break   # from the for
                # for

            aanwezig = request.POST.get('aanwezig', '')     # bevat 'aanwezig_NN'
            if aanwezig.startswith('aanwezig_'):
                for mins in (10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60):
                    sel = 'aanwezig_%d' % mins
                    if aanwezig == sel:
                        wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn = mins
                        break       # from the for
                # for

            if request.POST.get('extern', ''):
                wedstrijd.extern_beheerd = True
            else:
                wedstrijd.extern_beheerd = False

            prijs = request.POST.get('prijs_normaal', '')
            if prijs:
                prijs = prijs.replace(',', '.')   # regionale verschillen afvangen
                try:
                    prijs = float(prijs[:6])      # afkappen voor de veiligheid
                except ValueError:
                    raise Http404('Geen toegestane prijs')

                if prijs < 0.0 or prijs > 999.99:
                    raise Http404('Geen toegestane prijs')

                wedstrijd.prijs_euro_normaal = prijs

            prijs = request.POST.get('prijs_onder18', '')
            if prijs:
                prijs = prijs.replace(',', '.')   # regionale verschillen afvangen
                try:
                    prijs = float(prijs[:6])      # afkappen voor de veiligheid
                except ValueError:
                    raise Http404('Geen toegestane prijs')

                if prijs < 0.0 or prijs > 999.99:
                    raise Http404('Geen toegestane prijs')

                wedstrijd.prijs_euro_onder18 = prijs

            if self.rol_nu == Rol.ROL_MWZ:
                ter_info = request.POST.get('ter_info', '')
                if ter_info:
                    wedstrijd.is_ter_info = True
                else:
                    wedstrijd.is_ter_info = False

                aantal_scheids_str = request.POST.get('aantal_scheids', '')
                try:
                    aantal_scheids = int(aantal_scheids_str[:3])        # afkappen voor de veiligheid
                except ValueError:
                    wedstrijd.aantal_scheids = AANTAL_SCHEIDS_GEEN_KEUZE
                else:
                    if 0 <= aantal_scheids <= 9 or aantal_scheids == AANTAL_SCHEIDS_EIGEN:
                        wedstrijd.aantal_scheids = aantal_scheids

                wedstrijd.eis_kwalificatie_scores = False
                eis = request.POST.get('kwalificatie_scores', '')
                if eis:
                    wedstrijd.eis_kwalificatie_scores = True

            if not block_edits:
                urls = list()
                for nr in range(4):
                    url = request.POST.get('url_uitslag%d' % (nr + 1), '')
                    url = url[:128]     # voorkom fout tijdens save()
                    if len(url) > 4 and url not in urls:
                        urls.append(url)
                # for
                while len(urls) < 4:
                    urls.append('')
                # while
                wedstrijd.url_uitslag_1 = urls[0]
                wedstrijd.url_uitslag_2 = urls[1]
                wedstrijd.url_uitslag_3 = urls[2]
                wedstrijd.url_uitslag_4 = urls[3]

            if not block_edits:
                url = request.POST.get('url_flyer', '')
                url = url[:128]     # voorkom fout tijdens save()
                wedstrijd.url_flyer = url

            wedstrijd.save()

            boog_pks = list(wedstrijd.boogtypen.values_list('pk', flat=True))
            gekozen_klassen = list()
            for klasse in (KalenderWedstrijdklasse
                           .objects
                           .exclude(buiten_gebruik=True)
                           .select_related('boogtype')
                           .order_by('volgorde')):

                if klasse.pk in klassen_pks_gebruikt_in_sessies or request.POST.get('klasse_%s' % klasse.pk, ''):
                    # klasse is gewenst
                    if klasse.boogtype.pk in boog_pks:
                        # klasse boogtype is nog steeds gewenst
                        gekozen_klassen.append(klasse)
            # for

            # werk de manytomany koppelingen bij
            wedstrijd.wedstrijdklassen.set(gekozen_klassen)

            self._verplaats_sessies(wedstrijd, oude_datum_begin)

        if self.rol_nu == Rol.ROL_HWL:
            url = reverse('Wedstrijden:vereniging')
        else:
            url = reverse('Wedstrijden:manager-status', kwargs={'status': WEDSTRIJD_STATUS2URL[wedstrijd.status]})

        return HttpResponseRedirect(url)


# end of file
