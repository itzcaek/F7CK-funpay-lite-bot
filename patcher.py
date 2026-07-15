#!/usr/bin/env python3
"""
FunPay Lite Bot Patcher v2.0.6
Автоматически скачивает, распаковывает и патчит расширение.

Использование:
    python patcher.py

Результат:
    папка funpay-lite-bot-patched/ — готова к загрузке в Chrome
"""

import os
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
    
    # Проверяем заголовок
    magic = crx_data[:4]
    if magic == b"Cr24":
        # CRX2/CRX3 формат
        version = struct.unpack("<I", crx_data[4:8])[0]
        header_size = struct.unpack("<I", crx_data[8:12])[0]
        zip_start = 12 + header_size
        ok(f"CRX{version} формат, ZIP начинается с байта {zip_start}")
        zip_data = crx_data[zip_start:]
    elif magic == b"PK\x03\x04":
        # Уже ZIP
        ok("Файл уже ZIP")
        zip_data = crx_data
    else:
        err(f"Неизвестный формат: {magic}")
        sys.exit(1)
    
    # Сохраняем ZIP и распаковываем
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

CONTENT_PATCHES = [
    # v2.0.6 patterns
    (
        "ua() v2.0.6 — Community check → always true",
        'function ua(e){return!!e&&(e.subscriptions??[]).some(t=>t.planKey==="community"&&t.status==="active")}',
        'function ua(e){return true}'
    ),
    (
        "yu() v2.0.6 — Pro subscription check → always true",
        'function yu(){let{user:e}=Q();return e?(e.subscriptions??[]).some(t=>t.planKey==="pro"&&t.status==="active"):!1}',
        'function yu(){return true}'
    ),
    (
        "Fr() v2.0.6 — Tier display → always Pro",
        'function Fr(e){if(!e||!e.subscriptions||e.subscriptions.length===0)return{tier:"basic",label:we("basic")};let t="basic",n=Ir.basic;for(let s of e.subscriptions){if(s.status!=="active")continue;let o=Ir[s.planKey]??0;o>n&&(n=o,t=s.planKey)}return{tier:t,label:we(t)}}',
        'function Fr(e){return{tier:"pro",label:we("pro")}}'
    ),
    # v2.0.7 patterns (renamed functions)
    (
        "pa() v2.0.7 — Community check → always true",
        'function pa(e){return!!e&&(e.subscriptions??[]).some(t=>t.planKey==="community"&&t.status==="active")}',
        'function pa(e){return true}'
    ),
    (
        "wu() v2.0.7 — Pro subscription check → always true",
        'function wu(){let{user:e}=j();return e?(e.subscriptions??[]).some(t=>t.planKey==="pro"&&t.status==="active"):!1}',
        'function wu(){return true}'
    ),
    (
        "Ur() v2.0.7 — Tier display → always Pro",
        'function Ur(e){if(!e||!e.subscriptions||e.subscriptions.length===0)return{tier:"basic",label:we("basic")};let t="basic",n=Hr.basic;for(let s of e.subscriptions){if(s.status!=="active")continue;let o=Hr[s.planKey]??0;o>n&&(n=o,t=s.planKey)}return{tier:t,label:we(t)}}',
        'function Ur(e){return{tier:"pro",label:we("pro")}}'
    ),
    # Common patterns (both versions)
    (
        "A() — Feature gate → always true",
        'function A(e,t){return!!e&&(e.features??[]).includes(t)}',
        'function A(e,t){return true}'
    ),
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
    # v2.0.6 lr()
    (
        "lr() — reset nickname color → no-fail",
        'function lr(){chrome.runtime.sendMessage({target:"background",method:"setNicknameColor",payload:{styleKey:null}}).catch(()=>{})}',
        'function lr(){try{localStorage.removeItem("LBNicknameColor")}catch{}chrome.runtime.sendMessage({target:"background",method:"setNicknameColor",payload:{styleKey:null}}).catch(()=>{})}'
    ),
    # v2.0.7 ur()
    (
        "ur() — reset nickname color → no-fail",
        'function ur(){chrome.runtime.sendMessage({target:"background",method:"setNicknameColor",payload:{styleKey:null}}).catch(()=>{})}',
        'function ur(){try{localStorage.removeItem("LBNicknameColor")}catch{}chrome.runtime.sendMessage({target:"background",method:"setNicknameColor",payload:{styleKey:null}}).catch(()=>{})}'
    ),
]

BACKGROUND_EXPORT_PATCHES = [
    # pt() — orders export → client-side CSV/JSON
    # v2.0.6: function pt(...) | v2.0.7: async function pt(...)
    # replacement must NOT have async — applyBgPatch preserves the original async keyword
    (
        "pt() — orders export → client-side",
        None,  # ищем по началу функции
        'function pt(e,r,t,n,o,s,a){let orders=o.map(g=>Ro(g,a?.get(g.orderId)??null));let count=orders.length;let fname="funpaylitebot-"+e+"-export."+r;if(r==="json"){let json=JSON.stringify(orders,null,2);let bytes=new TextEncoder().encode(json);let b64="";for(let i=0;i<bytes.length;i+=32768)b64+=String.fromCharCode.apply(null,Array.from(bytes.subarray(i,i+32768)));return{ok:!0,file:{base64:btoa(b64),filename:fname,mime:"application/json",count:count}}}let header=["orderId","description","subcategory","price","currency","counterUsername","counterId","status","orderDateMs","orderDateText","costPrice","costCurrency"];let csvRows=[header.join(",")];for(let ord of orders){let row=header.map(h=>{let v=ord[h];if(v===null||v===undefined)return"";let sv=String(v);if(sv.includes(",")||sv.includes(String.fromCharCode(34))||sv.includes("\\n"))return String.fromCharCode(34)+sv.replace(/"/g,String.fromCharCode(34)+String.fromCharCode(34))+String.fromCharCode(34);return sv});csvRows.push(row.join(","))}let csv=csvRows.join("\\r\\n");let bom=new Uint8Array([239,187,191]);let csvBytes=new TextEncoder().encode(csv);let allBytes=new Uint8Array(bom.length+csvBytes.length);allBytes.set(bom);allBytes.set(csvBytes,bom.length);let b64="";for(let i=0;i<allBytes.length;i+=32768)b64+=String.fromCharCode.apply(null,Array.from(allBytes.subarray(i,i+32768)));return{ok:!0,file:{base64:btoa(b64),filename:fname.replace(".xlsx",".csv"),mime:"text/csv",count:count}}}'
    ),
    # lt() — finances export → client-side
    (
        "lt() — finances export → client-side",
        None,
        'async function lt(e,r,t,n,o){let txs=n.map(Po);let count=txs.length;let fname="funpaylitebot-finances-export."+e;if(e==="json"){let json=JSON.stringify(txs,null,2);let bytes=new TextEncoder().encode(json);let b64="";for(let i=0;i<bytes.length;i+=32768)b64+=String.fromCharCode.apply(null,Array.from(bytes.subarray(i,i+32768)));return{ok:!0,file:{base64:btoa(b64),filename:fname,mime:"application/json",count:count}}}let header=["id","dateMs","txType","status","title","signed","currency","refOrderId"];let csvRows=[header.join(",")];for(let tx of txs){let row=header.map(h=>{let v=tx[h];if(v===null||v===undefined)return"";let sv=String(v);if(sv.includes(",")||sv.includes(String.fromCharCode(34))||sv.includes("\\n"))return String.fromCharCode(34)+sv.replace(/"/g,String.fromCharCode(34)+String.fromCharCode(34))+String.fromCharCode(34);return sv});csvRows.push(row.join(","))}let csv=csvRows.join("\\r\\n");let bom=new Uint8Array([239,187,191]);let csvBytes=new TextEncoder().encode(csv);let allBytes=new Uint8Array(bom.length+csvBytes.length);allBytes.set(bom);allBytes.set(csvBytes,bom.length);let b64="";for(let i=0;i<allBytes.length;i+=32768)b64+=String.fromCharCode.apply(null,Array.from(allBytes.subarray(i,i+32768)));return{ok:!0,file:{base64:btoa(b64),filename:fname.replace(".xlsx",".csv"),mime:"text/csv",count:count}}}'
    ),
    # Ir() — unconfirmed orders → client-side filter
    (
        "Ir() — unconfirmed filter → client-side",
        None,
        'async function Ir(e,r){let t=[];try{await e.db.iterateByDate(null,null,o=>{o.orderStatus==="paid"&&t.push({orderId:o.orderId,orderDate:o.orderDate})})}catch(o){return k(`listUnconfirmedOrders: IDB iterate failed: ${o.message}`),{ok:!1,code:"IDB_ERROR",message:o.message}}if(t.length===0)return{ok:!0,results:r.thresholdsHours.map(o=>({thresholdHours:o,ids:[]}))};let now=Date.now();let results=r.thresholdsHours.map(h=>{let cutoff=now-h*3600000;let ids=t.filter(o=>o.orderDate<=cutoff).map(o=>o.orderId);return{thresholdHours:h,ids:ids}});return{ok:!0,results:results}}'
    ),
    # Et() — translate prepare → client-side Google Translate URLs
    (
        "Et() — translate prepare → client-side",
        None,
        'async function Et(e){try{let src=e.source||{};let requests=[];let fields=["title","description"];for(let f of fields){let text=src[f];if(!text||!text.trim())continue;let encoded=encodeURIComponent(text.trim());let url="https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=en&dt=t&q="+encoded;requests.push({field:f,url:url})}if(requests.length===0)return{ok:!1,code:"EMPTY_SOURCE",message:"No text to translate"};return{ok:!0,requests:requests}}catch(t){return k("prepareTranslate: local generation failed: "+t.message),{ok:!1,code:"LOCAL_ERROR",message:t.message}}}'
    ),
    # In() — heartbeat → blocked
    (
        "In() — heartbeat → blocked",
        None,
        'async function In(){return null}'
    ),
    # ta() — settings sync → blocked
    (
        "ta() — settings sync → blocked",
        None,
        'async function ta(e){return{ok:!0,nextIntervalMs:null,status:null}}'
    ),
    # ze() — install tracking → blocked
    (
        "ze() — install tracking → blocked",
        None,
        'async function ze(e){}'
    ),
    # Ye() — uninstall tracking → blocked
    (
        "Ye() — uninstall tracking → blocked",
        None,
        'async function Ye(){return}'
    ),
    # Ot() — nickname color → no-fail on error
    (
        "Ot() — nickname color → no-fail",
        None,
        None  # ищем по паттерну catch
    ),
]


def find_function(content: str, func_start: str):
    """Находит полную функцию по её началу."""
    idx = content.find(func_start)
    if idx == -1:
        return None, None, None
    
    # Ищем конец функции по балансу скобок
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
    """Применяет патчи функций (поиск по началу, замена тела)."""
    applied = 0
    failed = 0
    
    for desc, old_code, new_code in patches:
        # Для Ot() — особый паттерн
        if "Ot()" in desc:
            idx = content.find("function Ot(")
            if idx == -1:
                warn(f"  {desc} — функция не найдена")
                failed += 1
                continue
            _, end, old_func = find_function(content, "function Ot(")
            if old_func and "catch(r){return{ok:!1" in old_func:
                new_func = old_func.replace(
                    "catch(r){return{ok:!1,code:\"NETWORK_ERROR\",message:r.message}}",
                    "catch(r){return{ok:!0,styleKey:e}}"
                )
                content = content[:idx] + new_func + content[end:]
                ok(f"  {desc}")
                applied += 1
            else:
                warn(f"  {desc} — паттерн не найден")
                failed += 1
            continue
        
        # Для остальных — ищем функцию по характерному началу
        # Определяем начало функции из new_code
        if new_code.startswith("async function"):
            func_name = new_code.split("(")[0].replace("async function ", "").strip()
            search_start = f"async function {func_name}("
        elif new_code.startswith("function"):
            func_name = new_code.split("(")[0].replace("function ", "").strip()
            search_start = f"function {func_name}("
        else:
            warn(f"  {desc} — не удалось определить начало функции")
            failed += 1
            continue
        
        idx, end, old_func = find_function(content, search_start)
        
        # Если не нашли с async, пробуем без async (для v2.0.7 где async уже есть)
        if idx is None and search_start.startswith("async"):
            alt_start = search_start.replace("async function ", "function ")
            idx, end, old_func = find_function(content, alt_start)
            if idx is not None:
                search_start = alt_start
        
        idx, end, old_func = find_function(content, search_start)
        if idx is None:
            warn(f"  {desc} — функция {func_name}() не найдена")
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
    
    content, a, f1 = apply_simple_patches(content, CONTENT_PATCHES, "c.js")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return a, f1


def patch_background_b(ext_dir: str):
    """Патчит background/b.js"""
    path = os.path.join(ext_dir, "background", "b.js")
    if not os.path.exists(path):
        err(f"Файл не найден: {path}")
        return 0, 0
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Патчи функций (export, heartbeat, и т.д.)
    content, a1, f1 = apply_function_patches(content, BACKGROUND_EXPORT_PATCHES)
    
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
    
    # Удаляем update_url строку
    old = '"update_url": "https://clients2.google.com/service/update2/crx",\n'
    if old in content:
        content = content.replace(old, "")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        ok("  update_url удалён из manifest.json")
        return True
    else:
        warn("  update_url уже удалён")
        return True


# ─── Основной процесс ────────────────────────────────────────
def main():
    print(f"""
{C.BOLD}╔══════════════════════════════════════════════════╗
║     FunPay Lite Bot Patcher v2.0.6              ║
║     Pro фичи + экспорт + анонимность            ║
╚══════════════════════════════════════════════════╝{C.END}
""")
    
    # 1. Скачиваем
    crx_data = download_crx()
    
    # 2. Распаковываем
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    
    extract_crx(crx_data, OUTPUT_DIR)
    
    # 3. Патчим
    header("Применение патчей")
    
    total_ok = 0
    total_fail = 0
    
    # manifest.json
    print(f"\n{C.BOLD}manifest.json:{C.END}")
    patch_manifest(OUTPUT_DIR)
    
    # content/c.js
    print(f"\n{C.BOLD}content/c.js:{C.END}")
    a, f = patch_content_c(OUTPUT_DIR)
    total_ok += a
    total_fail += f
    
    # background/b.js
    print(f"\n{C.BOLD}background/b.js:{C.END}")
    a, f = patch_background_b(OUTPUT_DIR)
    total_ok += a
    total_fail += f
    
    # 4. Итог
    header("Готово!")
    print(f"""
  {C.OK}Применено патчей: {total_ok}{C.END}
  {C.WARN}Не найдено (возможно уже применены): {total_fail}{C.END}
  
  {C.BOLD}Расширение готово: {OUTPUT_DIR}/{C.END}
  
  {C.BOLD}Как установить:{C.END}
  1. Открой chrome://extensions/
  2. Включи "Режим разработчика" (Developer mode)
  3. Нажми "Загрузить распакованное расширение" (Load unpacked)
  4. Выбери папку {OUTPUT_DIR}
  5. Отключи оригинальное расширение (если установлено)
  6. Перезагрузи FunPay
  
  {C.BOLD}Что разблокировано:{C.END}
  ✓ Все Pro-фичи (экспорт, графики, перевод, темы)
  ✓ Экспорт продаж/покупок в CSV (без сервера)
  ✓ Перевод лотов через Google (без сервера)
  ✓ Скрытие цветов без логина
  ✓ Анонимность — heartbeat заблокирован
""")


if __name__ == "__main__":
    main()
