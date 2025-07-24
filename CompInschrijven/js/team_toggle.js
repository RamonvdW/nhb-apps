/*!
 * Copyright (c) 2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console */
"use strict";

const dataset = document.getElementById("js_data").dataset;


function do_toggle(id){
    // voer een POST uit om toe te voegen
    const form = document.createElement('form');
    form.name = 'form2';
    form.method = 'post';
    form.action = dataset.urlAfmelden;

    let inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "toggle_deelnemer_pk";
    inp.value = id.getAttribute("data-pk");
    form.appendChild(inp);

    inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "csrfmiddlewaretoken";
    inp.value = dataset.csrfToken;
    form.appendChild(inp);

    form.style.display = 'hidden';
    document.body.appendChild(form);
    form.submit();

    return false;    // false prevents default browser behavior
}

/* end of file */
