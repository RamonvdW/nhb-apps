/*!
 * Copyright (c) 2019-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

const dataset = document.getElementById("js_data").dataset;

function do_uitschrijven(id) {
    // voer een POST uit om toe te voegen
    let form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', id.getAttribute("data-url"));

    const inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "csrfmiddlewaretoken";
    inp.value = dataset.csrfToken;
    form.appendChild(inp);

    form.style.display = 'hidden';
    document.body.appendChild(form);
    form.submit();
}

function keuze_doorgeven(id) {
    // voer een POST uit om toe te voegen
    let form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', id.getAttribute("data-url"));

    const inp1 = document.createElement('input');
    inp1.type = "hidden";
    inp1.name = "csrfmiddlewaretoken";
    inp1.value = dataset.csrfToken;
    form.appendChild(inp1);

    const inp2 = document.createElement('input');
    inp2.type = "hidden";
    inp2.name = "deelnemer";
    inp2.setAttribute('value', id.getAttribute("data-deelnemer"));
    form.appendChild(inp2);

    const inp3 = document.createElement('input');
    inp3.type = "hidden";
    inp3.name = "keuze";
    inp3.setAttribute('value', id.getAttribute("data-keuze"));
    form.appendChild(inp3);

    form.style.display = 'hidden';
    document.body.appendChild(form);
    form.submit();
}

/* end of file */
