<div align="center">

# F7CK — FunPay Lite Bot Patcher

**Разблокируй всё. Будь анонимен.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.6-purple)]()
[![Chrome](https://img.shields.io/badge/Chrome-Extension-orange)](https://chromewebstore.google.com/detail/funpay-lite-bot/amicfiagmpbgfiiopieeemlkblfeeeip)

---

Онлайн-патчер для расширения [FunPay Lite Bot](https://chromewebstore.google.com/detail/funpay-lite-bot/amicfiagmpbgfiiopieeemlkblfeeeip) — разблокирует Pro фичи, делает экспорт без сервера и блокирует телеметрию.

**Всё работает в браузере. Ничего не отправляется наружу.**

</div>

---

## Возможности

<table>
<tr>
<td>

### 🔓 Pro фичи бесплатно

- Экспорт продаж/покупок в CSV и JSON
- Графики продаж и покупок
- Автоперевод лотов на английский
- Реальные цены без комиссии
- Кастомные MP3 звуки уведомлений
- Отображение комиссий разделов

</td>
<td>

### 🛡️ Анонимность

- Heartbeat заблокирован
- Телеметрия отключена
- Install tracking отключён
- Данные не утекают наружу
- Никаких fingerprints

</td>
</tr>
<tr>
<td>

### 📊 Клиентский экспорт

- CSV/JSON генерируется в браузере
- Никаких серверных запросов
- UTF-8 с BOM для Excel
- Работает офлайн

</td>
<td>

### 🎨 Без логина

- Скрытие цветов ников
- Настройка цвета ника
- Все Community фичи
- Никакой авторизации

</td>
</tr>
</table>

---

## Быстрый старт

### Вариант 1: Онлайн-патчер

> **GitHub Pages** — открой, перетащи CRX, скачай готовое.

1. Открой [онлайн-патчер](https://itzcaek.github.io/F7CK-funpay-lite-bot/)
2. Скачай CRX с Chrome Web Store
3. Перетащи .crx файл на страницу
4. Скачай запатченный ZIP
5. Распакуй → `chrome://extensions` → Load unpacked

### Вариант 2: Python

```bash
git clone https://github.com/itzcaek/F7CK-funpay-lite-bot.git
cd F7CK-funpay-lite-bot
python patcher.py
```

---

## Установка

```
1. Открой chrome://extensions/
2. Включи "Developer mode" (справа вверху)
3. Нажми "Load unpacked" (слева вверху)
4. Выбери папку funpay-lite-bot-patched
5. Отключи оригинальное расширение FunPay Lite Bot
6. Перезагрузи https://funpay.com
7. Наслаждайся Pro-фичами бесплатно
```

---

---

## Что НЕ отправляется

После патчинга расширение полностью анонимно:

| Данные | Статус |
|--------|--------|
| FunPay User ID | 🔒 Заблокировано |
| FunPay Username | 🔒 Заблокировано |
| Golden Key | 🔒 Заблокировано |
| Версия расширения | 🔒 Заблокировано |
| Настройки | 🔒 Заблокировано |
| Время активности | 🔒 Заблокировано |
| Install ID | 🔒 Заблокировано |

---

## Архив

В папке `archive/v2.0.6/` хранятся резервные копии:

| Файл | Описание |
|------|----------|
| `funpay-lite-bot-v2.0.6-original.crx` | Оригинальное расширение из Chrome Web Store |
| `funpay-lite-bot-v2.0.6-patched.zip` | Уже запатченная версия — просто распакуй и загрузи |

> Если авторы обновят или удалят расширение из Chrome Web Store, ты всё равно сможешь использовать проверенную версию 2.0.6.

---

## Требования

- **Chrome** / Chromium браузер (Chrome, Edge, Brave, Opera)
- **Python 3** (только для `patcher.py`, не нужен для веб-версии)

---

## Обновление

Когда выйдет новая версия расширения — просто перетащи новый CRX на страницу патчера. Все 14 патчей применятся автоматически.

---

## Технологии

```
Веб-патчер:  HTML + JS + JSZip (0 зависимостей)
Python:      Python 3 + stdlib (0 зависимостей)
Патчи:       14 функций, чистый replacement
```

---

## Disclaimer

Этот проект создан исключительно в образовательных целях для изучения reverse engineering.browser extensions.

Автор не несёт ответственности за использование данного инструмента.

---

<div align="center">

**Сделано с ❤️ иcold coffee**

*не забудь ★ если помогло*

</div>
