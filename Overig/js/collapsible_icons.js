/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console, M */
"use strict";

// verander het icon van een collapsible
// hiermee zetten we het plus/min teken aan de rechter kant
function set_collapsible_icon(el_li, new_icon) {
    // el_li = the collapsible-header "li" element that was opened or closed

    // the li contains a div with the collapsible-header class
    const el_header = el_li.firstElementChild;

    // the collapsible-header div typically contains a span and an li for an icon
    // when an icon is used, the secondary-content class is present
    const icons = el_header.getElementsByClassName('material-symbol secondary-content');
    if (icons.length > 0) {
        // icon(s) found
        const icon = icons[0];
        icon.innerText = new_icon;
    }
}

function uitklappen_klaar(id) {
    set_collapsible_icon(id, 'remove');     // alt: expand_less
}

function inklappen_klaar(id) {
    set_collapsible_icon(id, 'add');        // alt: expand_more
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
    elems = document.querySelectorAll(".collapsible-header .secondary-content");
    elems.forEach(icon => {
        icon.innerText = 'add';                     // gelijk houden aan inklappen_klaar
    });
});


// end of file
