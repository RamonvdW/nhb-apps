from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse
from django.views.generic import ListView
from Functie.definities import Rollen
from Functie.models import Functie
from Functie.rol import rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving

TEMPLATE_OVERZICHT_VERENIGING = 'functie/overzicht-vereniging.dtl'


class BeheerdersVerenigingView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders binnen een vereniging getoond en gewijzigd worden.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # de huidige rol bepaalt welke functies gewijzigd mogen worden
        # en de huidige functie selecteert de vereniging
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        rol2volg_nr = {'SEC': 1, 'HWL': 2, 'WL': 3}

        # zoek alle rollen binnen deze vereniging
        unsorted = list()
        for obj in (Functie
                    .objects
                    .filter(vereniging=functie_nu.vereniging)):

            # zet beheerders en urls voor de knoppen
            obj.beheerders = [account.volledige_naam()
                              for account in obj.accounts.only('username', 'first_name', 'last_name').all()]

            obj.wijzig_url = None
            obj.email_url = None

            mag_koppelen = False
            mag_email_wijzigen = False
            if rol_nu == Rollen.ROL_SEC and obj.rol in ('SEC', 'HWL'):
                # SEC mag andere SEC and HWL koppelen
                mag_koppelen = True
                if obj.rol != 'SEC':
                    # email voor secretaris komt uit Onze Relaties
                    mag_email_wijzigen = True

            elif rol_nu == Rollen.ROL_HWL and obj.rol in ('HWL', 'WL'):
                # HWL mag andere HWL en WL koppelen
                mag_koppelen = True
                mag_email_wijzigen = True

            elif rol_nu == Rollen.ROL_WL and obj.rol == 'WL':
                mag_email_wijzigen = True

            if mag_koppelen:
                obj.wijzig_url = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': obj.pk})

            if mag_email_wijzigen:
                obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})

            volg_nr = rol2volg_nr[obj.rol]
            tup = (volg_nr, obj.pk, obj)
            unsorted.append(tup)
        # for

        unsorted.sort()
        return [obj for _, _, obj in unsorted]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        # als er geen knop in beeld hoeft te komen, dan kan de tabel wat smaller
        context['show_wijzig_kolom'] = False
        for obj in context['object_list']:
            if obj.wijzig_url:
                context['show_wijzig_kolom'] = True
                break   # from the for
        # for

        context['terug_url'] = reverse('Vereniging:overzicht')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, 'Beheerders'),
        )

        return context

# end of file
