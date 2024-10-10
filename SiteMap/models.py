# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


class SiteMapLastMod(models.Model):
    """ Voor bijhouden lastmod van de sitemap delen """

    # voor welke applicatie?
    app_name = models.CharField(max_length=30)

    # hash over de URLs, om wijzigingen te ontdekken
    md5_digest = models.CharField(max_length=32)

    # wanneer voor het laatste aangepast?
    last_mod = models.DateTimeField()

    def __str__(self):
        return "%s: %s (%s)" % (self.app_name, self.last_mod, self.md5_digest)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "SiteMap LastMod"

    objects = models.Manager()      # for the editor only


# end of file
