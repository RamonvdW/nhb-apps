/*!
 * Copyright (c) 2026 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

const dataset = document.getElementById("js_data").dataset;
const url_aanmaken = dataset.url;
const csrf_token = dataset.csrf;


function add_input_fields(form) {
    const el_voornaam = document.getElementById('id_voornaam');
    const el_achternaam = document.getElementById('id_achternaam');
    const el_email = document.getElementById('id_email');

    let inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "voornaam";
    inp.value = el_voornaam.value;
    form.appendChild(inp);
    const l1= 10 + inp.value.length;

    inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "achternaam";
    inp.value = el_achternaam.value;
    form.appendChild(inp);
    const l2 = 20 + inp.value.length;

    inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "email";
    inp.value = el_email.value;
    form.appendChild(inp);
    const l3 = 30 + inp.value.length;

    let res = Math.max(l1, l2, l3);
    res = res * l2;

    return res;
}

function opsturen() {
    // doe een form post met de ingevoerde velden
    // voer een form POST uit om toe te voegen
    const form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', url_aanmaken);

    const res = add_input_fields(form);

    let inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "csrfmiddlewaretoken";
    inp.value = csrf_token;
    form.appendChild(inp);

    inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "res";
    inp.value = res.toString();
    form.appendChild(inp);

    form.style.display = 'hidden';
    document.body.appendChild(form);
    form.submit();
}


// koppel script aan knop
const el_submit = document.getElementById('submit_knop');
el_submit.addEventListener("click", function (){
    el_submit.disabled = true;
    opsturen();
});

/* end of file */
