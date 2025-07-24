/*!
 * Copyright (c) 2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console */
"use strict";

const dataset = document.getElementById("js_data").dataset;


function tel_wedstrijden() {
    // inschrijfmethode 1: tel hoeveel checkboxes aangekruist zijn
    const count = document.querySelectorAll('input[name^="wedstrijd_"]:checked').length;
    const el_aantal = document.getElementById('aantal');
    el_aantal.innerText = count.toString() + ' wedstrijden';

    const el = document.getElementById('submit_knop');
    el.disabled = (count > 7);
    if (count > 7) {
        el_aantal.classList.add('sv-rood-text');
    } else {
        el_aantal.classList.remove('sv-rood-text');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const do_tel = dataset.tel === "1";     // inschrijfmethode 1?
    if (do_tel) {
        // automatisch de eerste update doen
        tel_wedstrijden();
    }
});


function toon_wedstrijden_2() {
    // toon de 2e keus wedstrijden (in de regio, buiten het cluster)
    document.getElementById('id_wedstrijden_2').classList.remove('hide');
    document.getElementById('id_wedstrijden_2_knop').classList.add('hide');
}


/* end of file */
