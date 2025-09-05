/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console, M */
"use strict";

// helper functie om een opgeslagen cookie in te lezen
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


// framework init, after everything has been loaded and instantiated
window.addEventListener("load", () => {
    // page is fully loaded
    //console.log("load!");

    // de fonts zijn nu helemaal ingeladen, dus we kunnen de iconen tonen
    const icons = document.getElementsByClassName('material-symbol');
    Array.from(icons).forEach(icon => {
        icon.style.display = 'inline-block';
    });

    // evalueer de posities van de labels van de forms
    // zodat het label niet over het ingevulde input veld staat
    M.updateTextFields();
});


// the document view (window) has been resized
window.addEventListener('resize', () => {

    // dropdown menu automatisch dichtklappen
    const elems = document.querySelectorAll(".dropdown-trigger");
    Array.from(elems).forEach(elem => {
        const instance = M.Dropdown.getInstance(elem);
        if (instance && instance.isOpen) {
            instance.close();
        }
    });
});


// initial HTML document has been completely loaded and parsed, without waiting for stylesheets, images, etc.
document.addEventListener("DOMContentLoaded", (_event) => {
    //console.log('loaded!');

    // dropdown menu
    let elems = document.querySelectorAll(".dropdown-trigger");
    M.Dropdown.init(elems, {coverTrigger: false, constrainWidth: false});

    // tooltips
    elems = document.querySelectorAll(".tooltipped");
    M.Tooltip.init(elems, {enterDelay: 1000});

    // rolgordijnen
    elems = document.querySelectorAll("select");
    M.FormSelect.init(elems, {});

    // modals
    elems = document.querySelectorAll(".modal");
    M.Modal.init(elems, {'endingTop': '35%'});

    // materialboxed = media zoom
    elems = document.querySelectorAll('.materialboxed');
    M.Materialbox.init(elems, {});

    // console.log('history.length:', history.length)

    if (history.length < 2) {
        // nothing to go back to
        // typically happens when opening a manual page in a new window
        const el = document.getElementById("id_kruimels_back");
        // element bestaat niet als broodkruimels uitgezet zijn, zoals op het Plein zelf
        if (el) {
            el.style.display = "none";
        }
    }

});


// end of file
