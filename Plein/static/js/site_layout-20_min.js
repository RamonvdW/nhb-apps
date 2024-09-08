/*!
 * Copyright (c) 2020-2024 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */
function getCookie(name){'use strict';let cookieValue=null;if(document.cookie&&document.cookie!==""){let cookies=document.cookie.split(";");for(let i=0;i<cookies.length;i++){let cookie=cookies[i].trim();if(cookie.substring(0,name.length+1)===(name+"=")){cookieValue=decodeURIComponent(cookie.substring(name.length+1));break;}}}return cookieValue;}function getCookieNumber(name){'use strict';let value=getCookie(name);let number=0;if(value!=null){number=parseInt(value,10);if(isNaN(number)){number=0;}}return number;}function myTableFilter(zoekveld,tableId){'use strict';const table=document.getElementById(tableId);if(table===null){return;}const filter=/[\u0300-\u036f]/g;        const filter_tekst=zoekveld.value.normalize("NFD").replace(filter,"").toLowerCase();const filter_kolommen=[];for(let row of table.tHead.rows){let col_nr=0;for(let cell of row.cells){if(cell.hasAttribute("data-filter")){filter_kolommen.push(col_nr);}if(cell.hasAttribute("colSpan")){col_nr+=cell.colSpan;}else{col_nr+=1;}}}const row_deferred_hide=[];      const row_deferred_show=[];const body=table.tBodies[0];for(let i=0;i<body.rows.length;i++)     {const row=body.rows[i];const filter_cmd=row.dataset.tablefilter;if(filter_cmd==="stop"){break;     }let show=false;if(filter_tekst===""){show=true;}else{filter_kolommen.forEach(kolom_nr => {const cell=row.cells[kolom_nr];if(cell===undefined){window.console.log('missing cell in kolom_nr=',kolom_nr,"in row",i,"of row",row);}let clean_text=cell.dataset.clean_text;   if(typeof clean_text==="undefined"){clean_text=cell.innerText.normalize("NFD").replace(filter,"").toLowerCase();cell.dataset.clean_text=clean_text;}if(clean_text.indexOf(filter_tekst)!=-1){show=true;}});}if(show){if(row.style.display=="none"){row_deferred_show.push(i);}}else{if(row.style.display!="none"){row_deferred_hide.push(i);}}}row_deferred_hide.forEach(row_nr => {body.rows[row_nr].style.display="none";});row_deferred_show.forEach(row_nr => {body.rows[row_nr].style.display="table-row";});}function filters_activate(){'use strict';let url=document.getElementById("filters").dataset.url;for(let nr=1;nr<8;nr++){let tilde_nr='~'+nr;if(url.includes(tilde_nr)){let el=document.querySelector("input[name='filter_"+nr+"']:checked");if(!el){el=document.querySelector("input[name='filter_"+nr+"']");}url=url.replace(tilde_nr,el.dataset.url);}}window.location.href=url;}function mirror_radio(src_name,dst_name){'use strict';const src_sel="input[type='radio'][name="+src_name+"]:checked";const src_value=document.querySelector(src_sel).value;const dst_sel="input[type='radio'][name="+dst_name+"][value="+src_value+"]";const dst_el=document.querySelector(dst_sel);dst_el.checked=true;}function set_collapsible_icon(li_el,new_icon){const header_el=li_el.childNodes[0];const icons=header_el.getElementsByClassName('material-icons-round secondary-content');if(icons.length>0){const icon=icons[0];icon.innerText=new_icon;}}function uitklappen_klaar(id){set_collapsible_icon(id,'remove');    }function inklappen_klaar(id){set_collapsible_icon(id,'add');       }function sitelayout_loaded(){let elems=document.querySelectorAll(".collapsible");M.Collapsible.init(elems,{onOpenEnd:uitklappen_klaar,onCloseEnd:inklappen_klaar,});elems=document.querySelectorAll(".collapsible-header .secondary-content");elems.forEach(icon => {icon.innerText='add';});   elems=document.querySelectorAll(".dropdown-trigger");M.Dropdown.init(elems,{coverTrigger:false,constrainWidth:false});elems=document.querySelectorAll(".tooltipped");M.Tooltip.init(elems,{enterDelay:1000});elems=document.querySelectorAll("select");M.FormSelect.init(elems,{});elems=document.querySelectorAll(".modal");M.Modal.init(elems,{'endingTop':'35%'});if(history.length<2){const el=document.getElementById("id_kruimels_back");if(el) el.style.display="none";}window.addEventListener("load",sitelayout_load);window.addEventListener('resize',sitelayout_resize);}function sitelayout_load(){const icons=document.getElementsByClassName('material-icons-round');Array.from(icons).forEach(icon => {icon.style.display='inline-block'});const tables=document.getElementsByTagName("table");Array.from(tables).forEach(table => {if(table.id!==""){const inputs=table.getElementsByTagName("input");if(inputs.length>=1) myTableFilter(inputs[0],table.id);}});M.updateTextFields();}function sitelayout_resize(){const elems=document.querySelectorAll(".dropdown-trigger");Array.from(elems).forEach(elem => {const instance=M.Dropdown.getInstance(elem);if(instance.isOpen){instance.close();}});}