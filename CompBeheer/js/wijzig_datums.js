/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console, M */
"use strict";

const dataset = document.getElementById("js_data").dataset;
const alle_datums = JSON.parse(document.getElementById('js_datums').textContent);
const aantal_datums = Object.keys(alle_datums).length;

// de 'bezig' vlag voorkomt recursion
let bezig = true;

function post_datums()
{
    // voer een POST uit om toe te voegen
    const form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', dataset.urlWijzig);

    for (let nr = 1; nr <= aantal_datums; nr++) {
        const el = document.getElementById('datum' + nr);
        const inp = document.createElement('input');
        inp.type = "hidden";
        inp.name = "datum" + nr;
        inp.value = el.M_Datepicker.toString('yyyy-mm-dd');
        form.appendChild(inp);
    }

    const inp = document.createElement('input');
    inp.type = "hidden";
    inp.name = "csrfmiddlewaretoken";
    inp.value = dataset.csrfToken;
    form.appendChild(inp);

    form.style.display = 'hidden';
    document.body.appendChild(form);
    form.submit();
}

function rode_datums() {
    // controleer dat de datums opvolgend zijn
    if (!bezig) {
        bezig = true;
        const el = document.getElementById('datum1');
        let date = el.M_Datepicker.toString('yyyy-mm-dd');

        for (let nr = 2; nr <= aantal_datums; nr++)
        {
            const el2 = document.getElementById('datum' + nr);
            const date2 = el2.M_Datepicker.toString('yyyy-mm-dd');

            el2.classList.remove('sv-rood-text');
            if (date2 <= date) {
                el2.classList.add('sv-rood-text');
            }
            date = date2;
        }
        bezig = false;
    }
}

// For a given date, get the ISO week number
// Source: https://stackoverflow.com/questions/6117814/
function getWeekNumber(d) {
    // Copy date so don't modify original
    let weekday = 1 + d.getUTCDay();     // 1 = monday
    d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    // Set to nearest Thursday: current date + 4 - current day number
    // Make Sunday's day number 7
    d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
    // get first day of year
    let yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    // calculate full weeks to nearest Thursday
    let weekNo = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    // Return array of year and week number
    let year_str = d.getUTCFullYear().toString().substring(2);    // 2021 --> 21
    let week_str = weekNo.toString();
    if (weekNo < 10) {
        week_str = "0" + week_str;
    }
    return "wk" + year_str + week_str + "." + weekday;
}

function week_nummers() {
    // vertaal de datum naar het week nummer
    for (let nr = 1; nr <= 12; nr++) {
        const el_datum = document.getElementById('datum' + nr);
        const date = el_datum.M_Datepicker.date;

        const el_week_nr = document.getElementById('week_nr' + nr);
        el_week_nr.innerHTML = getWeekNumber(date);
    }
}

function gewijzigd() {
    // het formulier is aangepast en moet opgeslagen worden
    if (!bezig) {
        // rode_datums geeft nieuwe aanroepen naar deze functie
        rode_datums();
        week_nummers();

        // enable de 'opslaan' knop
        const el = document.getElementById("opslaan_knop");
        el.disabled = false;
        el.parentElement.style.display = "block";
    }
}

// initialisatie van de datum pickers
document.addEventListener('DOMContentLoaded', function() {
    const beginJaar = parseInt(dataset.beginJaar);
    const minDate = new Date(beginJaar, 2-1, 1);               // month is 0-based
    const maxDate = new Date(beginJaar + 1, 6-1, 22);     // month is 0-based
    const competitieJaren = [beginJaar, beginJaar + 1];

    for (let nr = 1; nr <= aantal_datums; nr++) {
        const el = document.getElementById('datum' + nr);
        M.Datepicker.init(el, {
            defaultDate: new Date(alle_datums[nr]),
            setDefaultDate: true,
            minDate: minDate, maxDate: maxDate,
            yearRange: competitieJaren
        });
    }

    bezig = false;   // klaar met initialisatie van alle date pickers (hier boven)
    rode_datums();
    week_nummers();
});

/* end of file */
