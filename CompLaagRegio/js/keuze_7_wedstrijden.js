/*!
 * Copyright (c) 2021-2026 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console, M */
"use strict";

function tel_wedstrijden() {
    // tel hoeveel checkboxes aangekruist zijn
    const count = document.querySelectorAll('input[name^="wedstrijd_"]:checked').length;

    const el_aantal = document.getElementById('aantal');
    el_aantal.innerText = count.toString() + ' wedstrijden';

    const el = document.getElementById('submit_knop');
    el.disabled = (count > 7)
    if (count > 7) {
        el_aantal.classList.add('sv-rood-text');
    } else {
        el_aantal.classList.remove('sv-rood-text');
    }
}

function toon_wedstrijden_2() {
    const els = document.getElementsByClassName('wedstrijden_2');
    Array.prototype.forEach.call(els, function (el) {
        el.classList.remove('hide');
    });

    document.getElementById('id_wedstrijden_2_knop').classList.add('hide');
}


document.addEventListener('DOMContentLoaded', function() {
    // initialisatie van het scherm
    tel_wedstrijden();

    // koppel de knop
    const el = document.getElementById('id_button_toon_meer_wedstrijden');
    if (el) {
        el.addEventListener('click', toon_wedstrijden_2);
    }

    // koppel de checkboxes
    const els = document.querySelectorAll('input[name^="wedstrijd_"]');
    els.forEach(el => el.addEventListener('change', tel_wedstrijden));
});

/* end of file */
