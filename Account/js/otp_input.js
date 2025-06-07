/*!
 * Copyright (c) 2025 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */

/* jshint esversion: 6 */
/* global console */
"use strict";

const el_otp1 = document.getElementById("otp1");
const el_otp2 = document.getElementById("otp2");
const el_otp3 = document.getElementById("otp3");
const el_otp4 = document.getElementById("otp4");
const el_otp5 = document.getElementById("otp5");
const el_otp6 = document.getElementById("otp6");
const el_code = document.getElementById("id_otp_code");
const el_submit_knop = document.getElementById("submit_knop");


window.addEventListener(
    "keydown",
    (e) => {
        if (!e.defaultPrevented) {
            if ("0123456789".indexOf(e.key) >= 0) {
                if (el_code.value.length < 6) {
                    el_code.value = el_code.value + e.key;
                    show_otp();
                    e.preventDefault();
                }
            } else if (e.key === "Backspace") {
                if (el_code.value.length > 0) {
                    el_code.value = el_code.value.slice(0, -1);
                    show_otp();
                    e.preventDefault();
                }
            }
        }
    },
    true);


window.addEventListener(
    "paste",
    (e) => {
        if (!e.defaultPrevented)
        {
            const data = e.clipboardData.getData("text");
            // console.log('paste:', data);

            let changed = false;
            data.split("").forEach(d => {
                if ("0123456789".indexOf(d) >= 0) {
                    el_code.value = el_code.value + d;
                    changed = true;
                }
            });

            if (changed) {
                show_otp();
                if (el_code.value.length === 6) {
                    el_submit_knop.click();
                }
            }

            e.preventDefault();
        }
    },
    true);


function show_otp() {
    // remove space, make array 1 character each, keep only digits, keep first 6 entries
    let spl = el_code.value.split("").slice(0, 6);
    // amend the array to ensure 6 entries
    spl.push('', '', '', '', '', '');
    // console.log('spl:', spl);

    // distribute input over the 6 input boxes
    el_otp1.value = spl[0];
    el_otp2.value = spl[1];
    el_otp3.value = spl[2];
    el_otp4.value = spl[3];
    el_otp5.value = spl[4];
    el_otp6.value = spl[5];

    // user is not tabbing around but actually change the input
    // we now set the focus to the first empty box
    const boxes = [el_otp1, el_otp2, el_otp3, el_otp4, el_otp5, el_otp6];
    let empty = spl.indexOf('');
    if (empty < 0 || empty > 5) {
        empty = 5;
    }
    const el = boxes[empty];
    el.focus();
}

/* end of file */
