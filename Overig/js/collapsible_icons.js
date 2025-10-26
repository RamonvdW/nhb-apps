/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console, M */
"use strict";

const svg_expand = '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 -960 960 960"><path fill="#f94137" d="M440.39-440.39H225.48q-16.71 0-28.16-11.5t-11.45-28.29q0-16.78 11.45-28.1 11.45-11.33 28.16-11.33h214.91v-214.91q0-16.64 11.5-28.41t28.29-11.77q16.78 0 28.1 11.77 11.33 11.77 11.33 28.41v214.91h214.91q16.64 0 28.41 11.5t11.77 28.29q0 16.78-11.77 28.1-11.77 11.33-28.41 11.33H519.61v214.91q0 16.71-11.5 28.16t-28.29 11.45q-16.78 0-28.1-11.45-11.33-11.45-11.33-28.16v-214.91Z"/></svg>';
const svg_shrink = '<svg xmlns="http://www.w3.org/2000/svg" height="21" width="21" viewBox="0 -960 960 960"><path fill="#f94137" d="M225.48-440.39q-16.71 0-28.16-11.5t-11.45-28.29q0-16.78 11.45-28.1 11.45-11.33 28.16-11.33h509.04q16.71 0 28.44 11.5 11.74 11.5 11.74 28.29 0 16.78-11.74 28.1-11.73 11.33-28.44 11.33H225.48Z"/></svg>';

// verander het icon van een collapsible
// hiermee zetten we het plus/min teken aan de rechter kant
function set_collapsible_icon(el_li, svg) {
    // el_li = the collapsible-header "li" element that was opened or closed

    // the li contains a div with the collapsible-header class
    const el_header = el_li.firstElementChild;

    // the collapsible-header div can contain an element for the icon
    const icons = el_header.getElementsByClassName('collapsible-icon');
    if (icons.length > 0) {
        // icon(s) found
        const icon = icons[0];
        icon.innerHTML = svg;
    }
}

function uitklappen_klaar(id) {
    set_collapsible_icon(id, svg_shrink);
}

function inklappen_klaar(id) {
    set_collapsible_icon(id, svg_expand);
}


// initial HTML document has been completely loaded and parsed, without waiting for stylesheets, images, etc.
document.addEventListener("DOMContentLoaded", (_event) => {
    //console.log('loaded!');

    const options =  {
                        onOpenEnd: uitklappen_klaar,
                        onCloseEnd: inklappen_klaar,
                        //inDuration: 100,    // default is 300
                        //outDuration: 100,   // default is 300
                    };

    // initialiseer de collapsible(s)
    let elems = document.querySelectorAll(".collapsible");
    M.Collapsible.init(elems, options);

    // zet the initiële icons
    elems = document.querySelectorAll(".collapsible-header .collapsible-icon");
    elems.forEach(icon => {
        icon.innerHTML = svg_expand;
    });
});


// end of file
