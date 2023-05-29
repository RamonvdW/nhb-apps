/*!
 * Copyright(c) 2020-2022 Ramon van der Winkel.
 * All rights reserved.
 * Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
 */
function getCookie(name){'use strict';let cookieValue=null;if(document.cookie&&document.cookie!==""){let cookies=document.cookie.split(";");for(let i=0;i<cookies.length;i++){let cookie=cookies[i].trim();if(cookie.substring(0,name.length+1)===(name+"=")){cookieValue=decodeURIComponent(cookie.substring(name.length+1));break;}}}return cookieValue}function getCookieNumber(name){'use strict';let value=getCookie(name);let number=0;if(value!=null){number=parseInt(value,10);if(isNaN(number)){number=0;}}return number;}function myTableFilter(zoekveld,tableId){'use strict';const table=document.getElementById(tableId);if(table===undefined){return;}const filter=/[\u0300-\u036f]/g;        const filter_tekst=zoekveld.value.normalize("NFD").replace(filter,"").toLowerCase();const filter_kolommen=[];for(let row of table.tHead.rows){let col_nr=0;for(let cell of row.cells){if(cell.hasAttribute("data-filter")){filter_kolommen.push(col_nr);}if(cell.hasAttribute("colSpan")){col_nr+=cell.colSpan;}else{col_nr+=1;}}}const row_deferred_hide=[];      const row_deferred_show=[];const body=table.tBodies[0];for(let i=0;i<body.rows.length;i++)     {const row=body.rows[i];const filter_cmd=row.dataset.tablefilter;if(filter_cmd==="stop"){break;     }let show=false;if(filter_tekst===""){show=true;}else{filter_kolommen.forEach(kolom_nr => {const cell=row.cells[kolom_nr];if(cell===undefined){window.console.log('missing cell in kolom_nr=',kolom_nr,"in row",i,"of row",row)}let clean_text=cell.dataset.clean_text;   if(typeof clean_text==="undefined"){clean_text=cell.innerText.normalize("NFD").replace(filter,"").toLowerCase();cell.dataset.clean_text=clean_text;}if(clean_text.indexOf(filter_tekst)!=-1){show=true;}});}if(show){if(row.style.display=="none"){row_deferred_show.push(i);}}else{if(row.style.display!="none"){row_deferred_hide.push(i);}}}row_deferred_hide.forEach(row_nr => {body.rows[row_nr].style.display="none";});row_deferred_show.forEach(row_nr => {body.rows[row_nr].style.display="table-row";});}