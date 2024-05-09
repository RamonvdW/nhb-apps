#!/usr/bin/env python3

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Add a license URL to the meta-data of a font file, in case none is present.
    The license URL is stored in "names" table with ID 14.

    Based on work by Christopher Simpkins:
    https://github.com/chrissimpkins/fontname.py/blob/master/fontname.py
"""

from fontTools import ttLib
import sys

if len(sys.argv) != 3:
    print('[ERROR] Required arguments: <filename to .otf file> <license url>')
    sys.exit(1)

fname = sys.argv[1]
license_url = sys.argv[2]

# load the font
print('[INFO] Loading %s' % repr(fname))
tt = ttLib.TTFont(fname)

# get the names table
names_tab = tt["name"]
print('[INFO] Font name: %s' % names_tab.getBestFullName())

# find the Copyright record (nameID 0)
# (provides languageID and PlatformID)
base = None
for ent in names_tab.names:
    if ent.nameID == 0:
        base = ent
        break
# for

if not base:
    print('[ERROR] Missing copyright entry')
    sys.exit(1)

# find the license URL (nameID 14)
for ent in names_tab.names:
    if ent.nameID == 14:
        print('[INFO] Font already contains a license URL: %s' % ent)
        sys.exit(1)
# for

# print('base: %s' % repr(base))

if len(license_url) > 10:
    print('[INFO] Adding License URL: %s' % repr(license_url))
    names_tab.setName(license_url, 14, base.platformID, base.platEncID, base.langID)

    # fname += ".with_license_url"
    print('[INFO] Saving font: %s' % repr(fname))
    tt.save(fname)
else:
    print('[INFO] Font does not yet contain a license URL')

# end of file
