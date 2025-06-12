/*!
 * Copyright (c) 2020-2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global M, tabel_filter */
"use strict";

const dataset = document.getElementById("js_data").dataset;
const wedstrijdMaxScore = parseInt(dataset.wedstrijdMaxScore);
const toonTeamNaam = dataset.toonTeamNaam === "true";
const teamPk2Naam = JSON.parse(document.getElementById('team_pk2naam').textContent);

function opzoeken_hide_status() {
    const el = document.getElementById("id_zoekstatus");
    el.classList.add("hide");
}

function opzoeken_toon_status(dataset2, tekst, color) {
    const el = document.getElementById("id_zoekstatus");
    el.classList.remove("hide");
    el.innerHTML = tekst;
    el.style.color = color;
}

function opzoeken_klaar(xhr, btn) {
    //console.log('opzoeken_klaar: ready=',xhr.readyState, 'status=', xhr.status)
    let is_fail = true;
    if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
        // verzoek is klaar en we hebben een antwoord
        // responseText is leeg bij connection failure
        if (xhr.responseText !== "") {
            try {
                const rsp = JSON.parse(xhr.responseText);
                //console.log('response:', rsp);

                // sla het resultaat op voor gebruik in toevoegen()
                const el = document.getElementById('id_zoekresultaat');
                el.value = rsp;

                // antwoord bevat fail=1 in verschillende situaties:
                // bondsnummer niet gevonden, geen actief lid
                if (rsp.fail === undefined) {
                    // toon het zoekresultaat
                    //let deelnemer = rsp['deelnemers'][0];
                    //console.log('deelnemer:', deelnemer);

                    //console.log('btn.dataset:', btn.dataset);
                    is_fail = false;
                    for (let d in btn.dataset) {     // geeft keys
                        if (d !== 'xhr' && d !== 'opzoeken') {      // deze keys overslaan
                            // voor deze key de data uit de response halen
                            let antwoord = rsp[d];

                            if (antwoord !== undefined) {
                                // zet het resultaat in het veld: naam, vereniging, regio
                                let el = document.getElementById(btn.dataset[d]);
                                el.innerHTML = antwoord;
                                el.style.color = "";
                            }
                        }
                    } // for
                }
            } catch (e) {
                // not a valid JSON response, could be because of 404
            }
        }
    }

    const el1 = document.getElementById("id_btn_toevoegen");
    const el2 = document.getElementById("id_zoekresultaten");
    if (is_fail) {
        opzoeken_toon_status(btn.dataset, "niet gevonden", "red");

        el1.disabled = true;
        el2.classList.add("hide");
    } else {
        opzoeken_hide_status();

        el1.disabled = false;
        el2.classList.remove("hide");
    }
}

function opzoeken_timeout(xhr) {
    // voorkom reactie bij ontvangst laat antwoord
    xhr.abort();

    // note: opzoeken_klaar wordt zo aangeroepen met readyState=0
    // deze zet de foutmelding-status op het scherm
}

function opzoeken(btn) {
    // deze functie wordt aangeroepen bij druk op de knop

    // voorkom parallelle verzoeken
    if (btn.dataset.xhr === undefined) {
        opzoeken_toon_status(btn.dataset, "bezig..", "gray");

        const xhr = new XMLHttpRequest();

        // doorloop de data- attributen van de knop
        let obj = {wedstrijd_pk: dataset.wedstrijdPk};

        // haal de data op die we moeten sturen
        for (let d in btn.dataset) {
            if (d === 'opzoeken') {
                // zoek het DOM element met deze id
                let el = document.getElementById(btn.dataset[d]);
                let lid_nr = el.value.slice(0, 6);
                // hanteer lege input
                if (lid_nr === '') {
                    return;
                }
                obj.lid_nr = lid_nr;
            }
        } // for

        // toevoegen knop disabled maken
        document.getElementById('id_btn_toevoegen').disabled = true;

        btn.dataset.xhr = xhr;      // ter voorkoming parallelle verzoeken

        const data = JSON.stringify(obj);

        // POST voorkomt caching
        xhr.open("POST", dataset.urlCheckBondsnummer, true);       // true = async
        xhr.timeout = 3000;                                        // 3 sec
        xhr.onloadend = function () {
            opzoeken_klaar(xhr, btn);
            delete btn.dataset.xhr;                // nieuw verzoek toegestaan
        };
        xhr.ontimeout = function () {
            opzoeken_timeout(xhr);
        };
        xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
        xhr.send(data);
    }
    // else: verzoek loopt nog, dus laat gebruiker wachten
}

function toevoegen() {
    // voeg de gevonden sporter toe aan de tabel
    // en geef dit door aan de website via een POST

    // als lid_nr al in de tabel staat, dan niet toevoegen
    // zet focus op score invoer veld
    // en maak zoekveld weer leeg

    const el_rsp = document.getElementById('id_zoekresultaat');
    const rsp = el_rsp.value;
    //console.log('toevoegen: rsp:', rsp);
    el_rsp.value = "";

    const el_gevonden = document.getElementById('id_zoekresultaten');
    el_gevonden.classList.add("hide");

    const lid_nr = rsp.lid_nr;

    // zoek het plekje in de tabel waar deze toegevoegd moet worden
    const table = document.getElementById('table1');
    const body = table.tBodies[0];
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
    const el_filter = document.getElementById(dataset.tableFilterInputId);
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
        if (peek_pk === deelnemer.pk) {
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
            new_row.cells[0].dataset.pk = deelnemer.pk;
            new_row.cells[0].innerHTML = lid_nr;

            new_row.cells[1].innerHTML = rsp.naam;

            const span = new_row.cells[2].firstChild;
            span.innerHTML = "[" + rsp.ver_nr + "]";
            span.nextSibling.innerHTML = " " + rsp.ver_naam;    // hidden on small

            const team_gem = deelnemer.team_gem;
            if (team_gem !== '') {
                new_row.cells[3].innerHTML = deelnemer.boog + ' (' + team_gem + ')';
            } else {
                new_row.cells[3].innerHTML = deelnemer.boog;
            }

            if (toonTeamNaam) {
                const team_pk = deelnemer.team_pk;
                const team_naam = teamPk2Naam[team_pk];
                new_row.cells[5].innerHTML = team_naam;
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
    //body.rows[row_smaller + 1].cells[4].firstChild.focus();
    if (focus_row) {
        focus_row.cells[4].firstChild.focus();
    }

    // zoekveld weer leeg maken
    document.getElementById('id_lid_nr').value = "";

    const el_naam = document.getElementById('id_naam');
    el_naam.innerHTML = "Naam van de sporter";
    el_naam.style.color = "grey";

    const el_ver = document.getElementById('id_ver');
    el_ver.innerHTML = "Naam van de vereniging";
    el_ver.style.color = "grey";

    document.getElementById('id_regio_').innerHTML = "";

    // toevoegen knop weer disabled maken
    document.getElementById('id_btn_toevoegen').disabled = true;
}

function opslaan_klaar(xhr) {
    //console.log('opslaan_klaar: ready=',xhr.readyState, 'status=', xhr.status)
    if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
            M.toast({html: 'De scores zijn opgeslagen'});
        } else {
            M.toast({html: 'Opslaan is NIET gelukt'});
        }
    }
}

// sla de ingevoerde scores op door een POST naar de website
function opslaan(btn) {
    const table = document.getElementById('table1');
    const body = table.tBodies[0];

    let obj = {wedstrijd_pk: dataset.wedstrijdPk};
    // begin op row 1 om de clone-template over te slaan
    for (let i = 1; i < body.rows.length; i++) {
        let row = body.rows[i];
        const filter_cmd = row.dataset.tablefilter;
        if (filter_cmd === "stop") {
            break;        // from the for
        }

        const pk = row.cells[0].dataset.pk;
        const score = row.cells[4].firstChild.value;
        //console.log('pk:', pk, 'score:', score);

        // lege scores juist wel meesturen, dan kan een verkeerd bondsnummer
        // nog uit de uitslag gehaald worden door de score leeg te maken!
        //if (score !== "")
        obj[pk] = score;
    } // for

    const data = JSON.stringify(obj);

    btn.disabled = true;

    const xhr = new XMLHttpRequest();

    // POST voorkomt caching
    xhr.open("POST", dataset.urlOpslaan, true);         // true = async
    xhr.timeout = 3000;                                  // 3 sec
    xhr.onloadend = function () {
        btn.disabled = false;
        opslaan_klaar(xhr);
    };
    xhr.ontimeout = function () {
        btn.disabled = false;
        M.toast({html: 'Opslaan is NIET gelukt'});
    };
    xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
    xhr.send(data);
}

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
    const el_filter = document.getElementById("table1_zoeken_input");
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
        const pk = deelnemer.pk;
        const lid_nr = deelnemer.lid_nr;
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

            if (pk == row_pk)  // warning: breaks when changed to ===
            {
                // dit is een dubbele
                skip = true;
                break;
            } else if (lid_nr < row_lid_nr || (lid_nr == row_lid_nr && pk < row_pk))      // warning: breaks when changing to ===
            {
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
            new_row.cells[0].innerHTML = lid_nr;
            new_row.cells[0].dataset.pk = deelnemer.pk;

            new_row.cells[1].innerHTML = deelnemer.naam;

            const span = new_row.cells[2].firstChild;
            span.innerHTML = "[" + deelnemer.ver_nr + "]";
            span.nextSibling.innerHTML = " " + deelnemer.ver_naam;

            const team_gem = deelnemer.team_gem;
            if (team_gem !== '') {
                new_row.cells[3].innerHTML = deelnemer.boog + ' (' + team_gem + ')';
            } else {
                new_row.cells[3].innerHTML = deelnemer.boog;
            }

            if (toonTeamNaam) {
                const team_pk = deelnemer.team_pk;
                new_row.cells[5].innerHTML = teamPk2Naam[team_pk];
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
                row.cells[4].firstChild.focus();
            }
        }
    }
}

function deelnemers_ophalen_klaar(xhr, btn) {
    //let is_fail = true
    //console.log('deelnemers_ophalen_klaar: ready=',xhr.readyState, 'status=', xhr.status)
    if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
            // verzoek is klaar en we hebben een antwoord
            // responseText is leeg bij connection failure
            if (xhr.responseText !== "") {
                try {
                    const rsp = JSON.parse(xhr.responseText);
                    deelnemers_ophalen_toevoegen(rsp);
                } catch (e) {
                    // bad JSON, which could be because of 404
                }

                // zet focus op het filter
                const el = document.getElementById("table1_zoeken_input");
                el.focus();
            }
        } else {
            // er is een fout opgetreden
            // maak de knop weer actief voor een nieuwe poging
            btn.disabled = false;
        }
    }
}

function deelnemers_ophalen(btn) {
    btn.disabled = true;         // knop is voor eenmalig gebruik

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
        deelnemers_ophalen_klaar(xhr, btn);
    };
    xhr.ontimeout = function () {
        btn.disabled = false;
    };     // sta nieuw gebruik knop toe
    xhr.setRequestHeader("X-CSRFToken", dataset.csrfToken);
    xhr.send(data);
}


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
    // console.log('event=', event)
    if (event.key === "Enter")
    {
        let el = document.getElementById('id_zoek_knop');
        el.click();
    }
});

/* end of file */
