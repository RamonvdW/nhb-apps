/*!
 * Copyright (c) 2019-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

/* global console */

const dataset = document.getElementById("js_data").dataset;

function wissel_naar_rol() {
    // vind de gekozen radiobutton
    const el = document.querySelector("input[type='radio'][name='rol']:checked");

    // haal de specifieke url op om deze rol te activeren
    const url = el.dataset.url;

    // do een form post met de url
    const form = document.createElement('form');
    form.method = 'post';
    form.action = url;
    form.style.display = 'hidden';

    let inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "csrfmiddlewaretoken";
    inp.value = dataset.csrfToken;
    form.appendChild(inp);

    document.body.appendChild(form);
    form.submit();
}


// koppel de knoppen aan de wissel_naar_rol functie
document.addEventListener('DOMContentLoaded', function() {
    dataset.knopIds.split(',').forEach(knop_id => {
        const el = document.getElementById(knop_id);
        if (el) {
            el.addEventListener('click', wissel_naar_rol);
        }
    });
});


/* end of file */
