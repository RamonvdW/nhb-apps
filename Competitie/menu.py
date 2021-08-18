# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Functie.rol import rol_get_huidige
from Plein.menu import menu_dynamics
from .models import Competitie


def menu_dynamics_competitie(request, context, comp_pk=None, actief=''):

    # voeg de seizoenen toe als sub-menus
    context['menu_competities'] = comps = list()
    menu_actief = 'competitie'

    rol_nu = rol_get_huidige(request)

    # zet de huidige competitie bovenaan
    # en de competitie-in-voorbereiding daar onder
    # groepeer per competitie-type (afstand)
    for obj in Competitie.objects.order_by('afstand', 'begin_jaar'):

        obj.bepaal_openbaar(rol_nu)

        if obj.is_openbaar:
            label = obj.titel()
            menu = 'competitie-%s' % obj.pk
            url = reverse('Competitie:overzicht',
                          kwargs={'comp_pk': obj.pk})

            comp = {'url': url,
                    'menu': menu,
                    'label': label}
            comps.append(comp)

            if obj.pk == comp_pk:
                menu_actief = menu
    # for

    # voeg de historische competitie toe, helemaal onderaan
    label = 'Vorig seizoen'
    url = reverse('HistComp:top')
    menu = 'competitie-hist'

    comp = {'url': url,
            'menu': menu,
            'label': label}
    comps.append(comp)

    if actief == 'histcomp':
        menu_actief = menu

    # print('context:')
    # for key, value in context.items():
    #     print('  %s: %s' % (key, repr(value)))

    menu_dynamics(request, context, actief=menu_actief)


def get_url_voor_competitie(functie_nu):
    """ Geef de url terug naar de specifieke bondscompetities overzicht pagina voor de BKO/RKO/RCL """

    # bepaal bij welke competitie deze rol hoort
    afstand = functie_nu.comp_type  # 18/25
    comps = Competitie.objects.filter(afstand=afstand).order_by('begin_jaar')  # laagste (oudste) eerst

    if len(comps) > 0:
        url = reverse('Competitie:overzicht', kwargs={'comp_pk': comps[0].pk})
    else:
        # er zijn competities
        url = None

    return url

# end of file
