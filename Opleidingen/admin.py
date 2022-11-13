# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import admin
from Opleidingen.models import Opleiding, OpleidingMoment, OpleidingDeelnemer, OpleidingDiploma


class CreateOnlyAdmin(admin.ModelAdmin):
    """
        Extend the ModelAdmin with createonly_fields,
        which act like readonly_fields except when creating a new object
    """

    createonly_fields = ()

    def get_readonly_fields(self, request, obj=None):                       # pragma: no cover
        readonly_fields = list(super().get_readonly_fields(request, obj))
        createonly_fields = list(getattr(self, 'createonly_fields', []))
        if obj:
            # editing an existing object
            readonly_fields.extend(createonly_fields)
        return readonly_fields


class OpleidingAdmin(admin.ModelAdmin):
    """ Admin configuratie voor Opleiding klasse """

    # ordering = ('lid_nr',)

    # search_fields = ('unaccented_naam', 'lid_nr')

    # filter mogelijkheid
    # list_filter = ('geslacht', 'para_classificatie', 'is_actief_lid', HeeftWaIdListFilter)

    # list_select_related = True

    pass


class OpleidingMomentAdmin(admin.ModelAdmin):
    """ Admin configuratie voor OpleidingMoment klasse """

    # search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    # list_select_related = ('sporter', 'boogtype')

    # autocomplete_fields = ('sporter',)
    pass


class OpleidingDeelnemerAdmin(admin.ModelAdmin):
    """ Admin configuratie voor OpleidingDeelnemer klasse """

    # search_fields = ('sporter__lid_nr', 'sporter__unaccented_naam')

    # list_select_related = True

    # readonly_fields = ('sporter',)

    # fieldsets = (
    #     ('Wie',
    #         {'fields': ('sporter',)
    #          }),
    #     ('Disciplines',
    #         {'fields': ('voorkeur_discipline_25m1pijl',
    #                     'voorkeur_discipline_outdoor',
    #                     'voorkeur_discipline_indoor',
    #                     'voorkeur_discipline_clout',
    #                     'voorkeur_discipline_veld',
    #                     'voorkeur_discipline_run',
    #                     'voorkeur_discipline_3d'),
    #          }),
    #     ('Wedstrijdgeslacht',
    #         {'fields': ('wedstrijd_geslacht_gekozen',
    #                     'wedstrijd_geslacht'),
    #          }),
    #     ('Para',
    #         {'fields': ('para_met_rolstoel',
    #                     'opmerking_para_sporter',)
    #          }),
    #     ('Overig',
    #         {'fields': ('voorkeur_eigen_blazoen',
    #                     'voorkeur_meedoen_competitie')
    #          }),
    # )

    pass


class OpleidingDiplomaAdmin(CreateOnlyAdmin):
    """ Admin configuratie voor OpleidingDiploma klasse """

    # search_fields = ('beschrijving', 'category', 'discipline', 'sporter__unaccented_naam')

    list_filter = ('code', 'toon_op_pas')

    list_select_related = ('sporter',)

    createonly_fields = ('sporter',)

    autocomplete_fields = ('sporter',)

    # list_select_related = True


admin.site.register(Opleiding, OpleidingAdmin)
admin.site.register(OpleidingMoment, OpleidingMomentAdmin)
admin.site.register(OpleidingDeelnemer, OpleidingDeelnemerAdmin)
admin.site.register(OpleidingDiploma, OpleidingDiplomaAdmin)

# end of file

