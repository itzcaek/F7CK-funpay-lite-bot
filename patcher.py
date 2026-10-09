#!/usr/bin/env python3
"""
FunPay Lite Bot Patcher (поддерживаемые версии: 2.0.6, 2.0.7, 2.3.4, 2.3.5)
Автоматически скачивает, распаковывает и патчит расширение.

Использование:
    python patcher.py

Результат:
    папка funpay-lite-bot-patched/ — готова к загрузке в Chrome
"""

import os
import re
import sys
import json
import struct
import shutil
import urllib.request
import zipfile
import tempfile
from pathlib import Path

# ─── Настройки ───────────────────────────────────────────────
EXTENSION_ID = "amicfiagmpbgfiiopieeemlkblfeeeip"
CRX_URL = (
    f"https://clients2.google.com/service/update2/crx?"
    f"response=redirect&prodversion=128.0&acceptformat=crx2,crx3"
    f"&x=id%3D{EXTENSION_ID}%26uc"
)
OUTPUT_DIR = "funpay-lite-bot-patched"

# ─── Цвета для терминала ─────────────────────────────────────
class C:
    OK = "\033[92m"
    WARN = "\033[93m"
    ERR = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"

def ok(msg):   print(f"{C.OK}[OK]{C.END} {msg}")
def warn(msg): print(f"{C.WARN}[!]{C.END} {msg}")
def err(msg):  print(f"{C.ERR}[X]{C.END} {msg}")
def header(msg): print(f"\n{C.BOLD}{'─'*50}\n  {msg}\n{'─'*50}{C.END}")


# ─── Скачивание CRX ──────────────────────────────────────────
def download_crx():
    header("Скачивание расширения из Chrome Web Store")
    print(f"  URL: {CRX_URL[:60]}...")
    try:
        req = urllib.request.Request(CRX_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        ok(f"Скачано {len(data):,} байт")
        return data
    except Exception as e:
        err(f"Ошибка скачивания: {e}")
        sys.exit(1)


# ─── Извлечение CRX → ZIP → папка ────────────────────────────
def extract_crx(crx_data: bytes, output_path: str):
    header("Распаковка CRX")

    magic = crx_data[:4]
    if magic == b"Cr24":
        version = struct.unpack("<I", crx_data[4:8])[0]
        header_size = struct.unpack("<I", crx_data[8:12])[0]
        zip_start = 12 + header_size
        ok(f"CRX{version} формат, ZIP начинается с байта {zip_start}")
        zip_data = crx_data[zip_start:]
    elif magic == b"PK\x03\x04":
        ok("Файл уже ZIP")
        zip_data = crx_data
    else:
        err(f"Неизвестный формат: {magic}")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(zip_data)
        tmp_path = tmp.name

    try:
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(output_path)
        ok(f"Распаковано в {output_path}/")
    finally:
        os.unlink(tmp_path)


# ─── Патчи ────────────────────────────────────────────────────

CONTENT_SIMPLE_PATCHES = [
    # v2.0.6 toggle
    (
        "Hide colors v2.0.6 → no login required",
        'async function b(){if(l.checked){if(!e){l.checked=!1,W();return}if(!A(e,Nm)){l.checked=!1,z({title:u("featureGatedCommunityTitle"),message:u("nicknameColorHideNeedCommunity"),tier:"community"});return}await D(Vt,!0),r(!0),e.nicknameColor&&lr()}else await D(Vt,!1),r(!1)}',
        'async function b(){if(l.checked){await D(Vt,!0),r(!0),e&&e.nicknameColor&&lr()}else await D(Vt,!1),r(!1)}'
    ),
    # v2.0.7 toggle
    (
        "Hide colors v2.0.7 → no login required",
        'async function b(){if(l.checked){if(!e){l.checked=!1,W();return}if(!A(e,Om)){l.checked=!1,z({title:u("featureGatedCommunityTitle"),message:u("nicknameColorHideNeedCommunity"),tier:"community"});return}await D(Ft,!0),r(!0),e.nicknameColor&&ur()}else await D(Ft,!1),r(!1)}',
        'async function b(){if(l.checked){await D(Ft,!0),r(!0),e&&e.nicknameColor&&ur()}else await D(Ft,!1),r(!1)}'
    ),
    # v2.3.4 toggle: hide nickname styles without account/community gate
    (
        "Hide colors v2.3.4 → no login required",
        'if(y){if(!e){m.checked=!1,nt();return}if(!D(e,dC)){m.checked=!1,Ne({feature:"nickname_color",title:p("featureGatedCommunityTitle"),message:p("nicknameColorHideNeedCommunity"),tier:"community"});return}}if(!e){Y(Mi,!1),l(!1,null);return}',
        'if(!e){Y(Mi,y),l(y,null);return}'
    ),
    # v2.3.5 toggle: hide nickname styles (имена функций переименованы)
    (
        "Hide colors v2.3.5 → no login required",
        'if(y){if(!e){m.checked=!1,nt();return}if(!D(e,EC)){m.checked=!1,Ne({feature:"nickname_color",title:p("featureGatedCommunityTitle"),message:p("nicknameColorHideNeedCommunity"),tier:"community"});return}}if(!e){Y(Bi,!1),l(!1,null);return}',
        'if(!e){Y(Bi,y),l(y,null);return}'
    ),
    # Nickname style save: снимаем требование аккаунта расширения
    (
        "Nickname style save v2.3.4 → no account required",
        'let ae=()=>{m=!1,j()},ye=await q().catch(()=>null);if(!ye)return ae(),ee&&nt(),{ok:!1,code:"NO_AUTH"};',
        'let ae=()=>{m=!1,j()},ye=await q().catch(()=>null);'
    ),
    # Legacy reset helpers (v2.0.6/v2.0.7)
    (
        "lr() — reset nickname color → no-fail",
        'function lr(){chrome.runtime.sendMessage({target:"background",method:"setNicknameColor",payload:{styleKey:null}}).catch(()=>{})}',
        'function lr(){try{localStorage.removeItem("LBNicknameColor")}catch{}chrome.runtime.sendMessage({target:"background",method:"setNicknameColor",payload:{styleKey:null}}).catch(()=>{})}'
    ),
    (
        "ur() — reset nickname color → no-fail",
        'function ur(){chrome.runtime.sendMessage({target:"background",method:"setNicknameColor",payload:{styleKey:null}}).catch(()=>{})}',
        'function ur(){try{localStorage.removeItem("LBNicknameColor")}catch{}chrome.runtime.sendMessage({target:"background",method:"setNicknameColor",payload:{styleKey:null}}).catch(()=>{})}'
    ),
]

CONTENT_FUNCTION_PATCHES = [
    # (описание, начало функции, обязательный маркер внутри старой функции, замена)
    ("ua() v2.0.6 — Community check → always true", "function ua(", 'planKey==="community"', 'function ua(e){return true}'),
    ("pa() v2.0.7 — Community check → always true", "function pa(", 'planKey==="community"', 'function pa(e){return true}'),
    ("uu() v2.3.4 — Community check → always true", "function uu(", 'planKey==="community"', 'function uu(e){return true}'),
    ("hd() v2.3.5 — Community check → always true", "function hd(", 'planKey==="community"', 'function hd(e){return true}'),

    ("yu() v2.0.6 — Pro check → always true", "function yu(", 'planKey==="pro"', 'function yu(){return true}'),
    ("wu() v2.0.7 — Pro check → always true", "function wu(", 'planKey==="pro"', 'function wu(){return true}'),

    ("Fr() v2.0.6 — Tier display → always Pro", "function Fr(", 'tier:"basic"', 'function Fr(e){return{tier:"pro",label:we("pro")}}'),
    ("Ur() v2.0.7 — Tier display → always Pro", "function Ur(", 'tier:"basic"', 'function Ur(e){return{tier:"pro",label:we("pro")}}'),
    ("qE() v2.3.4 — Best subscription → always Premium", "function qE(", "filter(at)", 'function qE(e){return{planKey:"premium",status:"active",expiresAt:null}}'),
    ("zE() v2.3.5 — Best subscription → always Premium", "function zE(", "filter(at)", 'function zE(e){return{planKey:"premium",status:"active",expiresAt:null}}'),

    ("A() v2.0.x — Feature gate → always true", "function A(", ".includes(t)", 'function A(e,t){return true}'),
    ("D() v2.3.4 — Feature gate → always true", "function D(", ".includes(t)", 'function D(e,t){return true}'),
]

BACKGROUND_FUNCTION_PATCHES = [
    # v2.3.4 orders export: async mr() отвечает за /orders/export
    (
        "mr() v2.3.4 — orders export → client-side",
        "async function mr(",
        "/orders/export",
        'async function mr(e,n,r,t,o,a,s){let orders=o.map(h=>_i(h,s?.get(h.orderId)??null));let count=orders.length;let fname="funpaylitebot-"+e+"-export."+n;if(n==="json"){let json=JSON.stringify(orders,null,2);let bytes=new TextEncoder().encode(json);return{ok:!0,file:{base64:Ni(bytes),filename:fname,mime:"application/json",count:count}}}let header=["orderId","description","subcategory","price","currency","counterUsername","counterId","status","orderDateMs","orderDateText","costPrice","costCurrency"];let csvRows=[header.join(",")];for(let ord of orders){let row=header.map(h=>{let v=ord[h];if(v===null||v===undefined)return"";let sv=String(v);if(sv.includes(",")||sv.includes(String.fromCharCode(34))||sv.includes("\\n"))return String.fromCharCode(34)+sv.replace(/"/g,String.fromCharCode(34)+String.fromCharCode(34))+String.fromCharCode(34);return sv});csvRows.push(row.join(","))}let csv=csvRows.join("\\r\\n");let bom=new Uint8Array([239,187,191]);let csvBytes=new TextEncoder().encode(csv);let allBytes=new Uint8Array(bom.length+csvBytes.length);allBytes.set(bom);allBytes.set(csvBytes,bom.length);return{ok:!0,file:{base64:Ni(allBytes),filename:fname.replace(".xlsx",".csv"),mime:"text/csv",count:count}}}'
    ),
    # v2.3.5 orders export: pr() (маппер переименован _i → Li)
    (
        "pr() v2.3.5 — orders export → client-side",
        "async function pr(",
        "/orders/export",
        'async function pr(e,n,r,t,o,a,s){let orders=o.map(h=>Li(h,s?.get(h.orderId)??null));let count=orders.length;let fname="funpaylitebot-"+e+"-export."+n;if(n==="json"){let json=JSON.stringify(orders,null,2);let bytes=new TextEncoder().encode(json);return{ok:!0,file:{base64:Ni(bytes),filename:fname,mime:"application/json",count:count}}}let header=["orderId","description","subcategory","price","currency","counterUsername","counterId","status","orderDateMs","orderDateText","costPrice","costCurrency"];let csvRows=[header.join(",")];for(let ord of orders){let row=header.map(h=>{let v=ord[h];if(v===null||v===undefined)return"";let sv=String(v);if(sv.includes(",")||sv.includes(String.fromCharCode(34))||sv.includes("\\n"))return String.fromCharCode(34)+sv.replace(/"/g,String.fromCharCode(34)+String.fromCharCode(34))+String.fromCharCode(34);return sv});csvRows.push(row.join(","))}let csv=csvRows.join("\\r\\n");let bom=new Uint8Array([239,187,191]);let csvBytes=new TextEncoder().encode(csv);let allBytes=new Uint8Array(bom.length+csvBytes.length);allBytes.set(bom);allBytes.set(csvBytes,bom.length);return{ok:!0,file:{base64:Ni(allBytes),filename:fname.replace(".xlsx",".csv"),mime:"text/csv",count:count}}}'
    ),
    # v2.0.x orders export: pt()
    (
        "pt() v2.0.x — orders export → client-side",
        "function pt(",
        "/orders/export",
        'function pt(e,r,t,n,o,s,a){let orders=o.map(g=>Ro(g,a?.get(g.orderId)??null));let count=orders.length;let fname="funpaylitebot-"+e+"-export."+r;if(r==="json"){let json=JSON.stringify(orders,null,2);let bytes=new TextEncoder().encode(json);let b64="";for(let i=0;i<bytes.length;i+=32768)b64+=String.fromCharCode.apply(null,Array.from(bytes.subarray(i,i+32768)));return{ok:!0,file:{base64:btoa(b64),filename:fname,mime:"application/json",count:count}}}let header=["orderId","description","subcategory","price","currency","counterUsername","counterId","status","orderDateMs","orderDateText","costPrice","costCurrency"];let csvRows=[header.join(",")];for(let ord of orders){let row=header.map(h=>{let v=ord[h];if(v===null||v===undefined)return"";let sv=String(v);if(sv.includes(",")||sv.includes(String.fromCharCode(34))||sv.includes("\\n"))return String.fromCharCode(34)+sv.replace(/"/g,String.fromCharCode(34)+String.fromCharCode(34))+String.fromCharCode(34);return sv});csvRows.push(row.join(","))}let csv=csvRows.join("\\r\\n");let bom=new Uint8Array([239,187,191]);let csvBytes=new TextEncoder().encode(csv);let allBytes=new Uint8Array(bom.length+csvBytes.length);allBytes.set(bom);allBytes.set(csvBytes,bom.length);let b64="";for(let i=0;i<allBytes.length;i+=32768)b64+=String.fromCharCode.apply(null,Array.from(allBytes.subarray(i,i+32768)));return{ok:!0,file:{base64:btoa(b64),filename:fname.replace(".xlsx",".csv"),mime:"text/csv",count:count}}}'
    ),
    # v2.3.4 finances export: async lr() отвечает за /finances/export
    (
        "lr() v2.3.4 — finances export → client-side",
        "async function lr(",
        "/finances/export",
        'async function lr(e,n,r,t,o){let txs=t.map(Oi);let count=txs.length;let fname="funpaylitebot-finances-export."+e;if(e==="json"){let json=JSON.stringify(txs,null,2);let bytes=new TextEncoder().encode(json);return{ok:!0,file:{base64:Ui(bytes),filename:fname,mime:"application/json",count:count}}}let header=["id","dateMs","txType","status","title","signed","currency","refOrderId"];let csvRows=[header.join(",")];for(let tx of txs){let row=header.map(h=>{let v=tx[h];if(v===null||v===undefined)return"";let sv=String(v);if(sv.includes(",")||sv.includes(String.fromCharCode(34))||sv.includes("\\n"))return String.fromCharCode(34)+sv.replace(/"/g,String.fromCharCode(34)+String.fromCharCode(34))+String.fromCharCode(34);return sv});csvRows.push(row.join(","))}let csv=csvRows.join("\\r\\n");let bom=new Uint8Array([239,187,191]);let csvBytes=new TextEncoder().encode(csv);let allBytes=new Uint8Array(bom.length+csvBytes.length);allBytes.set(bom);allBytes.set(csvBytes,bom.length);return{ok:!0,file:{base64:Ui(allBytes),filename:fname.replace(".xlsx",".csv"),mime:"text/csv",count:count}}}'
    ),
    # v2.3.5 finances export: ur() (маппер переименован Oi → Ii)
    (
        "ur() v2.3.5 — finances export → client-side",
        "async function ur(",
        "/finances/export",
        'async function ur(e,n,r,t,o){let txs=t.map(Ii);let count=txs.length;let fname="funpaylitebot-finances-export."+e;if(e==="json"){let json=JSON.stringify(txs,null,2);let bytes=new TextEncoder().encode(json);return{ok:!0,file:{base64:Ui(bytes),filename:fname,mime:"application/json",count:count}}}let header=["id","dateMs","txType","status","title","signed","currency","refOrderId"];let csvRows=[header.join(",")];for(let tx of txs){let row=header.map(h=>{let v=tx[h];if(v===null||v===undefined)return"";let sv=String(v);if(sv.includes(",")||sv.includes(String.fromCharCode(34))||sv.includes("\\n"))return String.fromCharCode(34)+sv.replace(/"/g,String.fromCharCode(34)+String.fromCharCode(34))+String.fromCharCode(34);return sv});csvRows.push(row.join(","))}let csv=csvRows.join("\\r\\n");let bom=new Uint8Array([239,187,191]);let csvBytes=new TextEncoder().encode(csv);let allBytes=new Uint8Array(bom.length+csvBytes.length);allBytes.set(bom);allBytes.set(csvBytes,bom.length);return{ok:!0,file:{base64:Ui(allBytes),filename:fname.replace(".xlsx",".csv"),mime:"text/csv",count:count}}}'
    ),
    # v2.0.x finances export: lt()
    (
        "lt() v2.0.x — finances export → client-side",
        "async function lt(",
        "/finances/export",
        'async function lt(e,r,t,n,o){let txs=n.map(Po);let count=txs.length;let fname="funpaylitebot-finances-export."+e;if(e==="json"){let json=JSON.stringify(txs,null,2);let bytes=new TextEncoder().encode(json);let b64="";for(let i=0;i<bytes.length;i+=32768)b64+=String.fromCharCode.apply(null,Array.from(bytes.subarray(i,i+32768)));return{ok:!0,file:{base64:btoa(b64),filename:fname,mime:"application/json",count:count}}}let header=["id","dateMs","txType","status","title","signed","currency","refOrderId"];let csvRows=[header.join(",")];for(let tx of txs){let row=header.map(h=>{let v=tx[h];if(v===null||v===undefined)return"";let sv=String(v);if(sv.includes(",")||sv.includes(String.fromCharCode(34))||sv.includes("\\n"))return String.fromCharCode(34)+sv.replace(/"/g,String.fromCharCode(34)+String.fromCharCode(34))+String.fromCharCode(34);return sv});csvRows.push(row.join(","))}let csv=csvRows.join("\\r\\n");let bom=new Uint8Array([239,187,191]);let csvBytes=new TextEncoder().encode(csv);let allBytes=new Uint8Array(bom.length+csvBytes.length);allBytes.set(bom);allBytes.set(csvBytes,bom.length);let b64="";for(let i=0;i<allBytes.length;i+=32768)b64+=String.fromCharCode.apply(null,Array.from(allBytes.subarray(i,i+32768)));return{ok:!0,file:{base64:btoa(b64),filename:fname.replace(".xlsx",".csv"),mime:"text/csv",count:count}}}'
    ),
    # Unconfirmed orders filter: v2.3.4 = vo(), v2.0.x = Ir()
    (
        "vo() v2.3.4 — unconfirmed filter → client-side",
        "async function vo(",
        "/orders/unconfirmed/filter",
        'async function vo(e,r){let t=[];try{await e.db.iterateByDate(null,null,o=>{o.orderStatus==="paid"&&t.push({orderId:o.orderId,orderDate:o.orderDate})})}catch(o){return S(`listUnconfirmedOrders: IDB iterate failed: ${o.message}`),{ok:!1,code:"IDB_ERROR",message:o.message}}if(t.length===0)return{ok:!0,results:r.thresholdsHours.map(o=>({thresholdHours:o,ids:[]}))};let now=Date.now();let results=r.thresholdsHours.map(h=>{let cutoff=now-h*3600000;let ids=t.filter(o=>o.orderDate<=cutoff).map(o=>o.orderId);return{thresholdHours:h,ids:ids}});return{ok:!0,results:results}}'
    ),
    # v2.3.5 unconfirmed filter: Oo()
    (
        "Oo() v2.3.5 — unconfirmed filter → client-side",
        "async function Oo(",
        "/orders/unconfirmed/filter",
        'async function Oo(e,r){let t=[];try{await e.db.iterateByDate(null,null,o=>{o.orderStatus==="paid"&&t.push({orderId:o.orderId,orderDate:o.orderDate})})}catch(o){return S(`listUnconfirmedOrders: IDB iterate failed: ${o.message}`),{ok:!1,code:"IDB_ERROR",message:o.message}}if(t.length===0)return{ok:!0,results:r.thresholdsHours.map(o=>({thresholdHours:o,ids:[]}))};let now=Date.now();let results=r.thresholdsHours.map(h=>{let cutoff=now-h*3600000;let ids=t.filter(o=>o.orderDate<=cutoff).map(o=>o.orderId);return{thresholdHours:h,ids:ids}});return{ok:!0,results:results}}'
    ),
    (
        "Ir() v2.0.x — unconfirmed filter → client-side",
        "async function Ir(",
        "/orders/unconfirmed/filter",
        'async function Ir(e,r){let t=[];try{await e.db.iterateByDate(null,null,o=>{o.orderStatus==="paid"&&t.push({orderId:o.orderId,orderDate:o.orderDate})})}catch(o){return k(`listUnconfirmedOrders: IDB iterate failed: ${o.message}`),{ok:!1,code:"IDB_ERROR",message:o.message}}if(t.length===0)return{ok:!0,results:r.thresholdsHours.map(o=>({thresholdHours:o,ids:[]}))};let now=Date.now();let results=r.thresholdsHours.map(h=>{let cutoff=now-h*3600000;let ids=t.filter(o=>o.orderDate<=cutoff).map(o=>o.orderId);return{thresholdHours:h,ids:ids}});return{ok:!0,results:results}}'
    ),
    # Translate prepare: v2.3.4 = _r(), v2.0.x = Et()
    (
        "_r() v2.3.4 — translate prepare → client-side",
        "async function _r(",
        "/api/v1/translate/lot/prepare",
        'async function _r(e){try{let src=e.source||{};let requests=[];let fields=["title","description"];for(let f of fields){let text=src[f];if(!text||!text.trim())continue;let encoded=encodeURIComponent(text.trim());let url="https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=en&dt=t&q="+encoded;requests.push({field:f,url:url})}if(requests.length===0)return{ok:!1,code:"EMPTY_SOURCE",message:"No text to translate"};return{ok:!0,requests:requests}}catch(t){return S("prepareTranslate: local generation failed: "+t.message),{ok:!1,code:"LOCAL_ERROR",message:t.message}}}'
    ),
    # v2.3.5 translate prepare: Lr()
    (
        "Lr() v2.3.5 — translate prepare → client-side",
        "async function Lr(",
        "/api/v1/translate/lot/prepare",
        'async function Lr(e){try{let src=e.source||{};let requests=[];let fields=["title","description"];for(let f of fields){let text=src[f];if(!text||!text.trim())continue;let encoded=encodeURIComponent(text.trim());let url="https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=en&dt=t&q="+encoded;requests.push({field:f,url:url})}if(requests.length===0)return{ok:!1,code:"EMPTY_SOURCE",message:"No text to translate"};return{ok:!0,requests:requests}}catch(t){return S("prepareTranslate: local generation failed: "+t.message),{ok:!1,code:"LOCAL_ERROR",message:t.message}}}'
    ),
    (
        "Et() v2.0.x — translate prepare → client-side",
        "async function Et(",
        "/api/v1/translate/lot/prepare",
        'async function Et(e){try{let src=e.source||{};let requests=[];let fields=["title","description"];for(let f of fields){let text=src[f];if(!text||!text.trim())continue;let encoded=encodeURIComponent(text.trim());let url="https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=en&dt=t&q="+encoded;requests.push({field:f,url:url})}if(requests.length===0)return{ok:!1,code:"EMPTY_SOURCE",message:"No text to translate"};return{ok:!0,requests:requests}}catch(t){return k("prepareTranslate: local generation failed: "+t.message),{ok:!1,code:"LOCAL_ERROR",message:t.message}}}'
    ),
    # Telemetry / lifecycle / install / uninstall / funnel events
    (
        "za() v2.3.4 — telemetry/report → blocked",
        "async function za(",
        "/api/v1/r",
        'async function za(){return null}'
    ),
    (
        "Ct() v2.3.4 — install tracking → blocked",
        "async function Ct(",
        "/api/v1/extension/installed",
        'async function Ct(e){}'
    ),
    (
        "fn() v2.3.4 — lifecycle install/update event → blocked",
        "function fn(",
        "Ct({installId",
        'function fn(e){}'
    ),
    (
        "ze() v2.3.4 — uninstall URL tracking → blocked",
        "async function ze(",
        "setUninstallURL",
        'async function ze(){}'
    ),
    (
        "$r() v2.3.4 — funnel events → blocked",
        "async function $r(",
        "/api/v1/extension/event",
        'async function $r(e){}'
    ),
    (
        "Lc() v2.3.4 — settings snapshot → blocked",
        "async function Lc(",
        "/api/v1/settings",
        'async function Lc(e){return{ok:!0,nextIntervalMs:null,status:null}}'
    ),
    (
        "er() v2.3.4 — server version check → blocked",
        "async function er(",
        "/api/v1/extension/version",
        'async function er(){return null}'
    ),
    (
        "rr() v2.3.4 — changelog fetch → disabled",
        "async function rr(",
        "/api/v1/extension/changelog",
        'async function rr(){return[]}'
    ),
    (
        "os() v2.3.4 — auto extension reload → disabled",
        "function os(",
        "chrome.runtime.reload",
        'function os(){}'
    ),
    # Nickname color submit: делаем локальным, чтобы не упираться в серверную проверку.
    # Без аккаунта сохраняем выбор в отдельный ключ f7ckNickSelection,
    # чтобы content-модуль F7CK_OWN_NICK_MODULE мог показать стиль на страницах.
    (
        "Rt() v2.3.4 — nickname color → local no-fail",
        "async function Rt(",
        "/me/funpay/nickname-color",
        'async function Rt(e){let t=e?.selection??{color:null,font:null,effect:null};try{let n=await V();n?await _({...n,nicknameColor:e?.styleKey??null,nicknameSelection:t}):await chrome.storage.local.set({f7ckNickSelection:t})}catch{}return{ok:!0,selection:t}}'
    ),
    # ─── v2.3.5 telemetry / lifecycle (функции переименованы) ───
    (
        "Za() v2.3.5 — telemetry/report → blocked",
        "async function Za(",
        "/api/v1/r",
        'async function Za(){return null}'
    ),
    (
        "mn() v2.3.5 — lifecycle install/update event → blocked",
        "function mn(",
        "Ct({installId",
        'function mn(e){}'
    ),
    (
        "Br() v2.3.5 — funnel events → blocked",
        "async function Br(",
        "/api/v1/extension/event",
        'async function Br(e){}'
    ),
    (
        "Nc() v2.3.5 — settings snapshot → blocked",
        "async function Nc(",
        "/api/v1/settings",
        'async function Nc(e){return{ok:!0,nextIntervalMs:null,status:null}}'
    ),
    (
        "tr() v2.3.5 — server version check → blocked",
        "async function tr(",
        "/api/v1/extension/version",
        'async function tr(){return null}'
    ),
    (
        "nr() v2.3.5 — changelog fetch → disabled",
        "async function nr(",
        "/api/v1/extension/changelog",
        'async function nr(){return[]}'
    ),
    (
        "as() v2.3.5 — auto extension reload → disabled",
        "function as(",
        "chrome.runtime.reload",
        'function as(){}'
    ),
]

# Модуль, дописываемый в конец content/c.js.
# Проблема: оригинальный Rt() после сохранения стиля писал его в кэш nicknameColors
# (через ya()), откуда content-скрипт красит ники на всех страницах. Локальный патч
# этого не делает — стиль не отображается. Модуль собирает CSS из выбранных
# color/font/effect по локальному каталогу nicknameStyles и подмешивает свой ник
# в кэш nicknameColors (ключ-стиль "__own__"), а также чистит его при сбросе.
CONTENT_APPEND_MODULE = r'''
/* === F7CK: own nickname style — local display injection === */
(function(){"use strict";try{
var F7CK_SEL_KEY="f7ckNickSelection";
function f7ckOwnNick(){try{var e=document.querySelector(".user-link-name");var t=e&&e.textContent?e.textContent.trim():"";return t||null}catch(err){return null}}
async function f7ckSyncOwnNick(){
try{
var st=await chrome.storage.local.get(["authUser",F7CK_SEL_KEY,"nicknameStyles","nicknameColors"]);
var colors=st.nicknameColors;if(!colors||typeof colors!="object")return;
var nick=f7ckOwnNick();if(!nick)return;
var sel=(st.authUser&&st.authUser.nicknameSelection&&typeof st.authUser.nicknameSelection=="object")?st.authUser.nicknameSelection:st[F7CK_SEL_KEY];
var has=!!(sel&&typeof sel=="object"&&(sel.color||sel.font||sel.effect));
var cat=st.nicknameStyles;var arr=Array.isArray(cat)?cat:(cat&&cat.styles);
var css="";
if(has&&Array.isArray(arr)){
var parts=[];
for(var gi=0;gi<3;gi++){var k=sel[["color","font","effect"][gi]];if(!k)continue;
for(var si=0;si<arr.length;si++){var s=arr[si];if(s&&s.key===k&&typeof s.css=="string"&&s.css){parts.push(s.css);break}}
}
css=parts.join(";");
}
var styles=Object.assign({},colors.styles),users=Object.assign({},colors.users),dirty=false;
if(css){
if(users[nick]!=="__own__"||styles["__own__"]!==css){styles["__own__"]=css;users[nick]="__own__";dirty=true;}
}else if(users[nick]==="__own__"){
delete users[nick];delete styles["__own__"];dirty=true;
}
if(dirty)await chrome.storage.local.set({nicknameColors:Object.assign({},colors,{styles:styles,users:users})});
}catch(err){}
}
chrome.storage.onChanged.addListener(function(ch,area){
if(area!=="local")return;
if("authUser"in ch||F7CK_SEL_KEY in ch||"nicknameStyles"in ch||"nicknameColors"in ch)f7ckSyncOwnNick();
});
f7ckSyncOwnNick();
}catch(err){}})();
/* === /F7CK own nickname style === */
'''


# ─── Утилиты поиска/замены функций ───────────────────────────
def find_function(content: str, func_start: str):
    """Находит полную функцию по её началу."""
    idx = content.find(func_start)
    if idx == -1:
        return None, None, None

    depth = 0
    end = idx
    for i in range(idx, len(content)):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    return idx, end, content[idx:end]


def apply_simple_patches(content: str, patches: list, label: str):
    """Применяет простые патчи (строка→строка)."""
    applied = 0
    failed = 0
    for desc, old, new in patches:
        if old in content:
            content = content.replace(old, new, 1)
            ok(f"  {desc}")
            applied += 1
        else:
            warn(f"  {desc} — не найдено (возможно уже применён)")
            failed += 1
    return content, applied, failed


def apply_function_patches(content: str, patches: list):
    """
    Применяет патчи функций.
    patches: (desc, search_start, required_marker|None, new_code)
    required_marker защищает от замены одноимённой функции из другой версии.
    """
    applied = 0
    failed = 0

    for desc, search_start, marker, new_code in patches:
        candidates = [search_start]
        if search_start.startswith("async function "):
            candidates.append(search_start.replace("async function ", "function "))
        elif search_start.startswith("function "):
            candidates.append("async " + search_start)

        idx = end = old_func = None
        used_start = None
        for start in candidates:
            idx, end, old_func = find_function(content, start)
            if idx is None:
                continue
            if marker and marker not in old_func:
                idx = None
                continue
            used_start = start
            break

        if idx is None:
            warn(f"  {desc} — функция не найдена или маркер не совпал")
            failed += 1
            continue

        content = content[:idx] + new_code + content[end:]
        ok(f"  {desc}")
        applied += 1

    return content, applied, failed


def patch_content_c(ext_dir: str):
    """Патчит content/c.js"""
    path = os.path.join(ext_dir, "content", "c.js")
    if not os.path.exists(path):
        err(f"Файл не найден: {path}")
        return 0, 0

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content, a1, f1 = apply_function_patches(content, CONTENT_FUNCTION_PATCHES)
    content, a2, f2 = apply_simple_patches(content, CONTENT_SIMPLE_PATCHES, "c.js")

    # Дописываем модуль отображения своего стиля ника (идемпотентно)
    marker = "F7CK: own nickname style"
    if marker in content:
        warn("  Own nickname style module — уже есть")
    else:
        content += CONTENT_APPEND_MODULE
        ok("  Own nickname style module — добавлен")
        a2 += 1

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return a1 + a2, f1 + f2


def patch_background_b(ext_dir: str):
    """Патчит background/b.js"""
    path = os.path.join(ext_dir, "background", "b.js")
    if not os.path.exists(path):
        err(f"Файл не найден: {path}")
        return 0, 0

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content, a1, f1 = apply_function_patches(content, BACKGROUND_FUNCTION_PATCHES)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return a1, f1


def patch_manifest(ext_dir: str):
    """Патчит manifest.json — удаляет update_url"""
    path = os.path.join(ext_dir, "manifest.json")
    if not os.path.exists(path):
        err(f"Файл не найден: {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    patched = re.sub(r'\n?\s*"update_url"\s*:\s*"https://clients2\.google\.com/service/update2/crx",?', "", content)
    if patched != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(patched)
        ok("  update_url удалён из manifest.json")
    else:
        warn("  update_url уже удалён")
    return True


# ─── Основной процесс ────────────────────────────────────────
def main():
    print(f"""
{C.BOLD}╔══════════════════════════════════════════════════╗
║     FunPay Lite Bot Patcher v2.3.5              ║
║     Pro фичи + экспорт + анонимность            ║
╚══════════════════════════════════════════════════╝{C.END}
""")

    crx_data = download_crx()

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    extract_crx(crx_data, OUTPUT_DIR)

    header("Применение патчей")

    total_ok = 0
    total_fail = 0

    print(f"\n{C.BOLD}manifest.json:{C.END}")
    patch_manifest(OUTPUT_DIR)

    print(f"\n{C.BOLD}content/c.js:{C.END}")
    a, f = patch_content_c(OUTPUT_DIR)
    total_ok += a
    total_fail += f

    print(f"\n{C.BOLD}background/b.js:{C.END}")
    a, f = patch_background_b(OUTPUT_DIR)
    total_ok += a
    total_fail += f

    header("Готово!")
    print(f"""
  {C.OK}Применено патчей: {total_ok}{C.END}
  {C.WARN}Не найдено (ожидаемо для других версий): {total_fail}{C.END}

  {C.BOLD}Расширение готово: {OUTPUT_DIR}/{C.END}

  {C.BOLD}Как установить:{C.END}
  1. Открой chrome://extensions/
  2. Включи "Режим разработчика" (Developer mode)
  3. Нажми "Загрузить распакованное расширение" (Load unpacked)
  4. Выбери папку {OUTPUT_DIR}
  5. Отключи оригинальное расширение (если установлено)
  6. Перезагрузи FunPay

  {C.BOLD}Что разблокировано:{C.END}
  ✓ Pro/Premium-фичи и feature gates
  ✓ Экспорт продаж/покупок/финансов локально в CSV/JSON
  ✓ Перевод лотов через Google Translate
  ✓ Скрытие цветов без логина
  ✓ Анонимность: report/install/uninstall/funnel events заблокированы
""")


if __name__ == "__main__":
    main()
