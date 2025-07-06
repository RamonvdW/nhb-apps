/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global M, tabel_filter, console */
"use strict";

const dataset = document.getElementById("js_data").dataset;
const wedstrijdMaxScore = parseInt(dataset.wedstrijdMaxScore);
let toonTeamNaam = dataset.toonTeamNaam === "true";
let teamPk2Naam = {};
let xhr_bezig = false;
let zoek_rsp = {};          // meest recent ontvangen zoekresultaat
const rsp_veld_to_el = {
    opzoeken: document.getElementById("id_lid_nr"),
    lid_nr: document.getElementById("id_bondsnummer"),
    naam: document.getElementById("id_naam"),
    vereniging: document.getElementById("id_ver"),
    regio: document.getElementById("id_regio_"),
};
const el_zoek_knop = document.getElementById('id_zoek_knop');
const el_opslaan_knop = document.getElementById('id_opslaan_knop');
const el_toevoegen_knop = document.getElementById('id_btn_toevoegen');
const el_zoekresultaten = document.getElementById("id_zoekresultaten");
const el_zoekstatus = document.getElementById("id_zoekstatus");
const el_filter = document.getElementById(dataset.tableFilterInputId);
const el_table = document.getElementById('table1');

try {
    teamPk2Naam = JSON.parse(document.getElementById('team_pk2naam').textContent);
} catch (e) {
    toonTeamNaam = false;
}


//-------------------------
// OPSLAAN knop
//-------------------------

function opslaan_klaar(xhr) {
    //console.log('opslaan_klaar: ready=',xhr.readyState, 'status=', xhr.status);
    if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
            M.toast({html: 'De scores zijn opgeslagen'});
        } else {
            M.toast({html: 'Opslaan is NIET gelukt'});
        }
    }
}

// sla de ingevoerde scores op door een POST naar de website
function opslaan(_el) {
    const body = el_table.tBodies[0];

    let obj = {
        wedstrijd_pk: dataset.wedstrijdPk
    };
    // begin op row 1 om de clone-template over te slaan
    for (let i = 1; i < body.rows.length; i++) {
        let row = body.rows[i];
        const filter_cmd = row.dataset.tablefilter;
        if (filter_cmd === "stop") {
            break;        // from the for
        }

        // let op: lege scores juist wel meesturen
        // dan kan een verkeerd bondsnummer  nog uit de uitslag gehaald worden door de score leeg te maken!
        const pk = row.cells[0].dataset.pk;
        obj[pk] = row.cells[4].firstChild.value;
    } // for

    xhr_bezig = true;
    const data = JSON.stringify(obj);
    const xhr = new XMLHttpRequest();

    // POST voorkomt caching
    xhr.open("POST", dataset.urlOpslaan, true);         // true = async
    xhr.timeout = 3000;                                  // 3 sec
    xhr.onloadend = function () {
        xhr_bezig = false;
        opslaan_klaar(xhr);
    };
    xhr.ontimeout = function () {
        xhr_bezig = false;
        M.toast({html: 'Opslaan is NIET gelukt'});
    };
    xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
    xhr.send(data);
}


//-------------------------
// ZOEK knop
//-------------------------

function opzoeken_hide_status() {
    el_zoekstatus.classList.add("hide");
}

function opzoeken_toon_status(tekst, color) {
    el_zoekstatus.classList.remove("hide");
    el_zoekstatus.innerText = tekst;
    el_zoekstatus.style.color = color;
}

function opzoeken_klaar(xhr) {
    //console.log('opzoeken_klaar: ready=',xhr.readyState, 'status=', xhr.status)
    let is_fail = true;

    if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
        // verzoek is klaar en we hebben een antwoord
        // responseText is leeg bij connection failure
        if (xhr.responseText !== "") {
            try {
                /** @param {bool} rsp.fail */
                const rsp = JSON.parse(xhr.responseText);
                //console.log('response:', rsp);

                // sla het resultaat op voor gebruik in toevoegen()
                zoek_rsp = rsp;

                // antwoord bevat fail=1 in verschillende situaties:
                // bondsnummer niet gevonden, geen actief lid
                if (rsp.fail === undefined) {
                    // toon het zoekresultaat
                    //console.log('rsp:', rsp);
                    is_fail = false;
                    for (const [rsp_veld, el] of Object.entries(rsp_veld_to_el)) {
                        // voor deze key de data uit de response halen
                        let antwoord = rsp[rsp_veld];

                        if (antwoord !== undefined) {
                            // zet het resultaat in het veld: naam, vereniging, regio
                            el.innerText = antwoord;
                            el.style.color = "";
                        }
                    } // for
                }
            } catch (e) {
                // not a valid JSON response, could be because of 404
            }
        }
    }

    if (is_fail) {
        opzoeken_toon_status("niet gevonden", "red");
        el_toevoegen_knop.disabled = true;
        el_zoekresultaten.classList.add("hide");
    } else {
        opzoeken_hide_status();
        el_toevoegen_knop.disabled = false;
        el_zoekresultaten.classList.remove("hide");
    }
}

function opzoeken_timeout(xhr) {
    // voorkom reactie bij ontvangst laat antwoord
    xhr.abort();

    // note: opzoeken_klaar wordt zo aangeroepen met readyState=0
    // deze zet de foutmelding-status op het scherm
}

function opzoeken(_el) {
    // deze functie wordt aangeroepen bij druk op de ZOEK knop

    // voorkom parallelle verzoeken
    if (xhr_bezig) {
        // verzoek loopt nog, dus laat gebruiker wachten
        return;
    }

    const el_zoek = rsp_veld_to_el.opzoeken;

    // haal de data op die we moeten sturen
    let obj = {
        wedstrijd_pk: dataset.wedstrijdPk,
        lid_nr: el_zoek.value.slice(0, 6)
    };

    // hanteer lege input
    if (obj.lid_nr !== '') {
        // voorkom parallelle verzoeken
        xhr_bezig = true;
        el_toevoegen_knop.disabled = true;
        opzoeken_toon_status("bezig..", "gray");

        const data = JSON.stringify(obj);
        const xhr = new XMLHttpRequest();

        // POST voorkomt caching
        xhr.open("POST", dataset.urlCheckBondsnummer, true);       // true = async
        xhr.timeout = 5000;                   // 5 seconden
        xhr.onloadend = function () {
            opzoeken_klaar(xhr);
            xhr_bezig = false;                // nieuw verzoek toegestaan
        };
        xhr.ontimeout = function () {
            xhr_bezig = false;
            opzoeken_timeout(xhr);
        };
        xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
        xhr.send(data);
    }
}


//-------------------------
// TOEVOEGEN knop
//-------------------------

function toevoegen(_el) {
    // voeg de gevonden sporter toe aan de tabel
    // en geef dit door aan de website via een POST

    // als lid_nr al in de tabel staat, dan niet toevoegen
    // zet focus op score invoer veld
    // en maak zoekveld weer leeg

    // neem de ontvangen resultaten over
    const rsp = zoek_rsp;
    zoek_rsp = {};
    //console.log('toevoegen: rsp:', rsp);

    el_zoekresultaten.classList.add("hide");

    const lid_nr = rsp.lid_nr;

    // zoek het plekje in de tabel waar deze toegevoegd moet worden
    const body = el_table.tBodies[0];
    let row_smaller = 0;
    for (let i = 0; i < body.rows.length; i++) {
        const row = body.rows[i];
        const filter_cmd = row.dataset.tablefilter;
        if (filter_cmd === "stop") {
            break;           // from the for
        }

        const row_lid_nr = row.cells[0].innerText;
        if (row_lid_nr < lid_nr) {
            row_smaller = i;
        }
    } // for

    // table filter uitzetten zodat de nieuwe regel getoond kan worden
    // maak zoekveld leeg; dit triggert tabel_filter()
    el_filter.value = "";
    tabel_filter(el_filter, 'table1');

    // voeg een regel(s) toe aan de tabel, op de juiste positie
    // doe dit door een kopie te maken
    const base_row = body.rows[0];       // regel om te clonen
    let insert_after_row = body.rows[row_smaller];
    let focus_row = null;
    let added_new = false;

    rsp.deelnemers.forEach(deelnemer => {
        // het is mogelijk dat de deelnemer al in de uitslag met 1 van meerdere bogen
        // kijk of de volgende regel toevallig van dit lid is, dan slaan we deze over
        let peek_row = body.rows[row_smaller + 1];
        let peek_pk = peek_row.cells[0].dataset.pk;
        let deelnemer_pk = deelnemer.pk.toString();
        if (peek_pk === deelnemer_pk) {
            // sla deze deelnemer en regel over
            row_smaller = row_smaller + 1;
            insert_after_row = peek_row;

            // geef deze regel focus als we een deelnemer met 1 boog nog een keer toevoegen
            if (!focus_row) {
                focus_row = peek_row;
            }
        } else {
            // deze deelnemer toevoegen
            const new_row = base_row.cloneNode(true);

            // verwijder attributen van de template die toegevoegd zijn door de tabel filter
            new_row.cells[0].removeAttribute("data-clean_text");
            new_row.cells[1].removeAttribute("data-clean_text");
            new_row.cells[2].removeAttribute("data-clean_text");

            // volgende statement is gelijk aan insertAfter, welke niet bestaat
            // werkt ook aan het einde van de tabel
            // zie https://stackoverflow.com/questions/4793604/how-to-insert-an-element-after-another-element-in-javascript-without-using-a-lib
            insert_after_row.parentNode.insertBefore(new_row, insert_after_row.nextSibling);

            // pas de nieuwe regel aan met de gevonden data
            new_row.cells[0].dataset.pk = deelnemer_pk;
            new_row.cells[0].innerText = lid_nr;

            new_row.cells[1].innerText = rsp.naam;

            const span = new_row.cells[2].firstChild;
            span.innerText = "[" + rsp.ver_nr + "]";
            span.nextSibling.innerText = " " + rsp.ver_naam;    // hidden on small

            const team_gem = deelnemer.team_gem;
            if (team_gem !== '') {
                new_row.cells[3].innerText = deelnemer.boog + ' (' + team_gem + ')';
            } else {
                new_row.cells[3].innerText = deelnemer.boog;
            }

            if (toonTeamNaam) {
                new_row.cells[5].innerText = teamPk2Naam[deelnemer.team_pk] || "-";
            }

            // maak de nieuwe row zichtbaar
            new_row.classList.remove('hide');
            if (!added_new) {
                added_new = true;
                focus_row = new_row;
            }

            row_smaller = row_smaller + 1;
            insert_after_row = new_row;
        }
    });

    // scroll nieuwe regel into view + zet focus op invoer score
    if (focus_row) {
        const cell = focus_row.cells[4];    // tr --> td
        const el_input = cell.firstChild;   // td --> input
        if (el_input.focus) {       // TODO: why sometimes undefined?
            el_input.focus();
        }
    }

    // zoekveld weer leeg maken
    rsp_veld_to_el.opzoeken.value = '';

    const el_naam = rsp_veld_to_el.naam;
    el_naam.innerText = "Naam van de sporter";
    el_naam.style.color = "grey";

    const el_ver = rsp_veld_to_el.vereniging;
    el_ver.innerText = "Naam van de vereniging";
    el_ver.style.color = "grey";

    rsp_veld_to_el.regio.innerText = "";

    // toevoegen knop weer disabled maken totdat er iets ingevoerd wordt
    el_toevoegen_knop.disabled = true;
}


//-------------------------
// Lijst ophalen (kaartje)
//-------------------------

function deelnemers_ophalen_toevoegen(rsp) {
    // voeg de sporterboog toe aan de tabel, tenzij al aanwezig
    //  (voorkomt verwijderen van al ingevoerde scores)

    const table = document.getElementById('table1');
    const body = table.tBodies[0];
    const base_row = body.rows[0];       // regel om te clonen

    // verwijder attributen van de template die toegevoegd zijn door de tabel filter
    base_row.cells[0].removeAttribute("data-clean_text");
    base_row.cells[1].removeAttribute("data-clean_text");
    base_row.cells[2].removeAttribute("data-clean_text");

    // table filter uitzetten zodat de nieuwe regels getoond kunnen worden
    // maak zoekveld leeg; dit triggert tabel_filter()
    el_filter.value = "";
    tabel_filter(el_filter, 'table1');

    let deelnemers = rsp.deelnemers;
    // sorteer deelnemers op invoeg-volgorde: bondsnummer
    deelnemers.sort(function (a, b) {
        if (a.lid_nr !== b.lid_nr) {
            return a.lid_nr - b.lid_nr;
        } else {
            return a.pk - b.pk;
        }
    });
    //console.log('sorted deelnemers:', deelnemers);

    let first_added_row;
    let row_nr = 0;
    deelnemers.forEach(deelnemer => {
        /** @param {int} deelnemer.pk */
        /** @param {int} deelnemer.team_pk */
        /** @param {int} deelnemer.ver_nr */
        /** @param {int} deelnemer.lid_nr */
        /** @param {string} deelnemer.boog */
        /** @param {string} deelnemer.naam */
        /** @param {string} deelnemer.ver_naam */
        /** @param {string} deelnemer.team_gem */   // "" or "7.123"
        const pk = deelnemer.pk.toString();
        const lid_nr = deelnemer.lid_nr.toString();
        let skip = false;
        while (row_nr <= body.rows.length)      // stop eerder: op tablefilter=stop
        {
            const row = body.rows[row_nr];

            const filter_cmd = row.dataset.tablefilter;
            if (filter_cmd === "stop") {
                row_nr -= 1;     // terug naar een echte regel
                break;           // from the while
            }

            const row_pk = row.cells[0].dataset.pk;
            const row_lid_nr = row.cells[0].innerText;

            if (pk === row_pk) {
                // dit is een dubbele
                skip = true;
                break;
            } else if (lid_nr < row_lid_nr || (lid_nr === row_lid_nr && pk < row_pk)) {
                // lid_nr is minder dan lid_nr in deze regel
                row_nr -= 1;     // toevoegen voor deze regel
                break;           // from the while
            } else {
                // blijf zoeken
                row_nr += 1;
            }
        }

        if (!skip) {
            const row = body.rows[row_nr];
            const new_row = base_row.cloneNode(true);

            // pas de nieuwe regel aan met de ontvangen data
            new_row.cells[0].innerText = lid_nr;
            new_row.cells[0].dataset.pk = deelnemer.pk;

            new_row.cells[1].innerText = deelnemer.naam;

            const span = new_row.cells[2].firstChild;
            span.innerText = "[" + deelnemer.ver_nr + "]";
            span.nextSibling.innerText = " " + deelnemer.ver_naam;

            const team_gem = deelnemer.team_gem;
            if (team_gem !== '') {
                new_row.cells[3].innerText = deelnemer.boog + ' (' + team_gem + ')';
            } else {
                new_row.cells[3].innerText = deelnemer.boog;
            }

            if (toonTeamNaam) {
                const team_pk = deelnemer.team_pk;
                new_row.cells[5].innerText = teamPk2Naam[team_pk];
            }

            // volgende statement is gelijk aan insertAfter, welke niet bestaat
            // werkt ook aan het einde van de tabel
            // zie https://stackoverflow.com/questions/4793604/how-to-insert-an-element-after-another-element-in-javascript-without-using-a-lib
            row.parentNode.insertBefore(new_row, row.nextSibling);

            row_nr += 1;         // ga verder op de zojuist toegevoegd regel

            if (first_added_row === undefined) {
                first_added_row = row_nr;
            }
        }
    }); // forEach

    // maak alle nieuwe regels in een blok operatie zichtbaar
    if (first_added_row !== undefined) {
        // er zijn regels toegevoegd
        // begin bij 1, want 0 is de clone template
        for (let i = 1; i < body.rows.length; i++) {
            let row = body.rows[i];
            const filter_cmd = row.dataset.tablefilter;
            if (filter_cmd === "stop") {
                break;      // from the for
            }

            // maak de nieuwe row zichtbaar
            row.classList.remove('hide');

            if (i === first_added_row) {
                const cell = row.cells[4];      // tr --> td
                const el = cell.firstChild;               // td --> input
                el.focus();
            }
        }
    }
}

function deelnemers_ophalen_klaar(xhr) {
    //let is_fail = true
    //console.log('deelnemers_ophalen_klaar: ready=',xhr.readyState, 'status=', xhr.status)
    if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
            // verzoek is klaar en we hebben een antwoord
            // responseText is leeg bij connection failure
            if (xhr.responseText !== "") {
                try {
                    /** @param {Array} rsp.deelnemers **/
                    const rsp = JSON.parse(xhr.responseText);
                    deelnemers_ophalen_toevoegen(rsp);
                } catch (e) {
                    // bad JSON, which could be because of 404
                }

                // zet focus op het filter
                const el = document.getElementById("table1_zoeken_input");
                el.focus();
            }
        }
        // else: er is een fout opgetreden
    }
}

function deelnemers_ophalen() {
    if (!xhr_bezig) {
        const obj = {
            deelcomp_pk: dataset.deelcompPk,
            wedstrijd_pk: dataset.wedstrijdPk
        };
        const data = JSON.stringify(obj);
        const xhr = new XMLHttpRequest();

        // POST voorkomt caching
        xhr.open("POST", dataset.urlDeelnemersOphalen, true);   // true = async
        xhr.timeout = 5000;                                       // 5 sec
        xhr.onloadend = function () {
            deelnemers_ophalen_klaar(xhr);
            xhr_bezig = false;
        };
        xhr.ontimeout = function () {
            xhr_bezig = false;
        };     // sta nieuw gebruik knop toe
        xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
        xhr.send(data);
    }
}


//----------------------------
// Controleer ingevoerde score
//----------------------------

function controleer_score(el) {
    let color = "";

    // /\D/.test() matches digits and returns true if there are non-digits
    const value = el.value;
    if (/\D/.test(value) || value < 0 || value > wedstrijdMaxScore) {
        color = "red";
    }

    el.style.color = color;
}


// koppel gebruik van de <enter> knop in het zoekveld aan het klikken op de zoekknop
document.getElementById('id_lid_nr').addEventListener("keyup", function(event) {
    //console.log('event=', event)
    if (event.key === "Enter")
    {
        let el = document.getElementById('id_zoek_knop');
        el.click();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    el_zoek_knop.addEventListener('click', opzoeken);
    el_toevoegen_knop.addEventListener('click', toevoegen);
    el_opslaan_knop.addEventListener('click', opslaan);
    document.querySelector('.score-invoer').addEventListener('input', controleer_score);
});

/* end of file */
