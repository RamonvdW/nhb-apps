/*!
 * Copyright (c) 2022-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console */
"use strict";

const dataset = document.getElementById("js_data").dataset;
let verwijder_ids = [];

try {
    verwijder_ids = JSON.parse(document.getElementById('verwijder_ids').textContent);
} catch (e) {
    verwijder_ids = [];
}


function verwijder(event) {
    const el = event.currentTarget;         // the element with the event handler
    const url = el.dataset.url;

    el.disabled = true;                     // double-click prevention

    // voer een POST uit om toe te voegen
    let form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', url);

    let inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "csrfmiddlewaretoken";
    inp.value = dataset.csrfToken;
    form.appendChild(inp);

    form.style.display = 'hidden';
    document.body.appendChild(form);
    form.submit();

    // POST is synchroon
    // antwoord bevat een nieuwe pagina (of een redirect)
}


// koppel de knop click events aan de verwijder functie
document.addEventListener('DOMContentLoaded', function() {
    verwijder_ids.forEach(knop_id => {
        const el_knop = document.getElementById(knop_id);
        el_knop.addEventListener('click', verwijder);
    });
});

/* end of file */
