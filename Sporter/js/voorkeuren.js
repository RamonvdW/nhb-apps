/*!
 * Copyright (c) 2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

const el_opslaan_knop = document.getElementById("submit_knop");

function gewijzigd() {
    // het formulier is aangepast
    // toon de gebruiker de floating "opslaan" knop
    el_opslaan_knop.disabled = false;
    el_opslaan_knop.parentElement.style.display = "block";
}

/* end of file */
