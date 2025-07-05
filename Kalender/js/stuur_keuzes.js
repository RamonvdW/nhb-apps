/*!
 * Copyright (c) 2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
"use strict";

const dataset = document.getElementById("js_data").dataset;
const urlMaand = dataset.urlMaand;
const urlJaar = dataset.urlJaar;

const el_zoek = document.getElementById('id_zoekterm');
const el_filter_knop = document.getElementById('id_filter_knop');


function maak_url(url_main) {
    // construeer de url om naartoe te navigeren
    const el_soort = document.querySelector("input[name='filter_soort']:checked");
    const el_bogen = document.querySelector("input[name='filter_bogen']:checked");
    const el_discipline = document.querySelector("input[name='filter_discipline']:checked");
    const zoekterm = el_zoek.value;

    let url = url_main + el_soort.dataset.url + '/' + el_bogen.dataset.url + '/' + el_discipline.dataset.url + '/';

    if (zoekterm !== "") {
        // voeg de zoekterm toe als query parameter
        url += '?zoek=' + zoekterm;
    }

    return url;
}

function stuur_keuzes_prev_next(url_prev_next) {
    // wordt gebruikt voor de prev and next knoppen op zowel de jaar als maand pagina's
    window.location.href = maak_url(url_prev_next);
}

function stuur_keuzes_maand() {
    // wordt gebruikt op de maand pagina voor de filters
    // wordt gebruikt op de jaar pagina om naar het maandoverzicht te gaan
    window.location.href = maak_url(urlMaand);
}

function stuur_keuzes_jaar() {
    // wordt gebruikt op de jaar pagina voor de filters
    // wordt gebruikt op de maand pagina om naar het jaaroverzicht te gaan
    window.location.href = maak_url(urlJaar);
}

function stuur_keuzes_zoek() {
    // wordt gebruikt op de maand en jaar pagina's voor het zoeken
    // we tonen de zoekresultaten altijd op het jaaroverzicht
    window.location.href = maak_url(urlJaar);
}

// enter toets in de zoekterm invoer moet keuzes insturen
el_zoek.addEventListener("keyup", event => {
    // console.log(event);
    if (event.key === 'Enter') {
        stuur_keuzes_jaar();
    }
});

// filter uitklappen/inklappen knop
el_filter_knop.addEventListener("click", function(event) {
    const els = document.getElementsByClassName('collapsible_filter');
    Array.prototype.forEach.call(els, function(el) {
        if (el.style.display === "none") {
            el.style.display = "block";
        } else {
            el.style.display = "none";
        }
    });
});

/* end of file */
