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


// filter activeer knop afhandeling
//
// filters moeten de namen "filter_1", "filter_2" hebben
// elke radiobutton moet een 'url' in zijn dataset hebben
// maximaal 8 filters
// 1 element met id "filters" moet de template url hebben met daarin ~1, ~2, etc. die vervangen moeten worden
// meerdere knoppen kunnen een onclick hebben met filters_activate()
//
// voorbeeld:
//     <h4
//        id="filters"                        <--
//        data-url="{{ filter_url }}">        <--
//        Filters
//     </h4>
//     <b>Kies een regio:</b>
//     <ul>
//         {% for filter in regio_filters %}
//             <li>
//                 <label for="id_{{ filter.sel }}">
//                     <input
//                        type="radio"
//            -->         name="filter_2"
//                        value="{{ filter.sel }}"
//                        required id="id_{{ filter.sel }}"
//                        {% if filter.selected %}checked{% endif %}
//            -->         data-url="{{ filter.url_part }}">
//                     <span>{{ filter.opt_text }}</span>
//                 </label>
//             </li>
//         {% endfor %}
//     </ul>
//     <button class="btn-sv-rood" onclick="filter_activate()">Activeer</button>

function filters_activate() {

    // get the template url (with the ~1 etc in it)
    let url = document.getElementById("filters").dataset.url;

    // replace the ~1 etc. as far as present in the url
    for (let nr = 1; nr < 8; nr++) {
        let tilde_nr = '~' + nr;
        if (url.includes(tilde_nr)) {
            let el = document.querySelector("input[name='filter_" + nr + "']:checked");
            if (!el) {
                // find the backup, typically <input type="hidden" ..>
                el = document.querySelector("input[name='filter_" + nr + "']");
            }
            url = url.replace(tilde_nr, el.dataset.url);
        }
    }

    // navigate to the final url
    window.location.href = url;
}


// radio button groups in sync laten lopen
// gebruik: als een filter meerdere keren voorkomt, ivm layout (media queries)
// bij het maken van een wijziging wordt deze doorgezet naar het andere filter
//
// voorbeeld:
//
//          <input type="radio"
//                 name="filter_4"
//                 value="{{ filter.sel }}"
//                 data-url="{{ filter.url_part }}">
//
//          <input type="radio"
//                 name="makl2"
//                 value="{{ filter.sel }}"
//        -->      onchange="mirror_radio('makl2', 'filter_4')">
//
function mirror_radio(src_name, dst_name) {
    // zoek het geselecteerde element in de bron radiobutton set
    const src_sel = "input[type='radio'][name=" + src_name + "]:checked";
    const src_value = document.querySelector(src_sel).value;

    // zoek dezelfde optie in de andere radiobutton set
    const dst_sel = "input[type='radio'][name=" + dst_name + "][value=" + src_value + "]";
    const dst_el = document.querySelector(dst_sel);

    // activeer de juiste optie
    dst_el.checked = true;
}


// verander het icon van een collapsible
// hiermee zetten we het plus/min teken aan de rechter kant
function set_collapsible_icon(li_el, new_icon) {
    // li_el = the "li" element that was opened or closed
    // first child element = the div with the header
    const header_el = li_el.childNodes[0];
    // search within the header for the element with the icon class
    const icons = header_el.getElementsByClassName('material-icons-round secondary-content');
    if (icons.length > 0) {
        const icon = icons[0];
        icon.innerText = new_icon;
    }
}

function uitklappen_klaar(id) {
    set_collapsible_icon(id, 'remove');     // expand_less
}

function inklappen_klaar(id) {
    set_collapsible_icon(id, 'add');        // expand_more
}


// framework init, after everything has been loaded and instantiated
window.addEventListener("load", () => {
    // page is fully loaded
    //console.log("load!");

    // de fonts zijn nu helemaal ingeladen, dus we kunnen de iconen tonen
    const icons = document.getElementsByClassName('material-icons-round');
    Array.from(icons).forEach(icon => {
        icon.style.display = 'inline-block';
    });

    // evalueer de posities van de labels van de forms
    // zodat het label niet over het ingevulde input veld staat
    M.updateTextFields();
});


window.addEventListener('resize', () => {
    // the document view (window) has been resized

    // dropdown menu automatisch dichtklappen
    const elems = document.querySelectorAll(".dropdown-trigger");
    Array.from(elems).forEach(elem => {
        const instance = M.Dropdown.getInstance(elem);
        if (instance && instance.isOpen) {
            instance.close();
        }
    });
});


document.addEventListener("DOMContentLoaded", (_event) => {
    // initial HTML document has been completely loaded and parsed, without waiting for stylesheets, images, etc.
    //console.log('loaded!');

    let elems = document.querySelectorAll(".collapsible");

    M.Collapsible.init(elems, { onOpenEnd: uitklappen_klaar,
                                onCloseEnd: inklappen_klaar,
                                //inDuration: 100,    // default is 300
                                //outDuration: 100,   // default is 300
    });

    elems = document.querySelectorAll(".collapsible-header .secondary-content");
    // console.log('header icons:', elems)
    elems.forEach(icon => {
        icon.innerText = 'add';
    });    // gelijk houden aan inklappen_klaar

    // dropdown menu
    elems = document.querySelectorAll(".dropdown-trigger");
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
