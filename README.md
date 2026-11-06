# Crypto Alerts — Bot de señales por Telegram + GitHub Actions (gratis)

Este proyecto revisa cada 15 minutos las señales de criptomonedas en Binance y te manda un mensaje por Telegram cuando aparece una nueva señal de **COMPRA** o **VENTA**. Funciona en la nube (GitHub Actions), así que **no necesitas tener la PC encendida**.

## Paso 1 — Crear tu bot de Telegram

1. Abre Telegram y busca **@BotFather**.
2. Envía `/newbot` y sigue las instrucciones (nombre y usuario terminado en `bot`).
3. Te dará un **TOKEN** (algo como `123456:ABC-DEF...`). Guárdalo.
4. Busca tu bot y envíale un mensaje (ej. "hola").
5. Abre en tu navegador: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
6. Busca `"chat":{"id": 123456789}` — ese número es tu **CHAT_ID**.

## Paso 2 — Subir el proyecto a GitHub

1. Crea una cuenta en https://github.com (si no tienes).
2. Crea un repositorio nuevo (ej. `crypto-alerts`), público o privado.
3. Sube todos los archivos de esta carpeta (`crypto-alerts/`) al repositorio.
   - Puedes usar la web de GitHub: "Add file → Upload files" y arrastrar todo.
   - O con git: `git init && git add . && git commit -m "init" && git remote add origin ... && git push`.

## Paso 3 — Agregar los secretos

En tu repositorio de GitHub:
1. Ve a **Settings → Secrets and variables → Actions → New repository secret**.
2. Crea `TELEGRAM_BOT_TOKEN` con tu token.
3. Crea `TELEGRAM_CHAT_ID` con tu chat id.

## Paso 4 — Activar el workflow

1. Ve a la pestaña **Actions** del repositorio.
2. Si te pide habilitar workflows, acéptalo.
3. El workflow "Crypto Alerts" correrá cada 15 minutos automáticamente.
4. Para probar ya: abre el workflow → **Run workflow** (botón derecho) → Run.

Recibirás un mensaje en Telegram cuando haya una nueva señal.

## Personalizar

- **Monedas**: edita `SYMBOLS` en `render.yaml` o la variable de entorno `SYMBOLS` en el workflow (agrega `SYMBOLS: "BTCUSDT,ETHUSDT,..."` en el bloque `env`).
- **Intervalo de velas**: variable `INTERVAL` (ej. `1h`).
- **Frecuencia de revisión**: cambia el cron en `.github/workflows/alerts.yml` (ej. `*/5 * * * *` cada 5 min; cuidado con rate limits).
- **Intervalo mínimo recomendado**: 15 min para no saturar Binance ni GitHub Actions.

## Opción alternativa — Render (servidor 24/7)

Si prefieres un servidor siempre encendido en lugar de cron:
1. Crea cuenta en https://render.com
2. New → Background Worker → conecta tu repo de GitHub.
3. Render detectará `render.yaml`. Agrega las variables `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
4. Deploy. El bot correrá en loop revisando cada `INTERVAL_MINUTES`.

> Nota: el plan gratuito de Render duerme los servicios web inactivos, pero los Background Workers gratuitos tienen 750h/mes — suficiente para un bot.

## Cómo funciona el monitoreo

- El script descarga velas (klines) de Binance para cada moneda.
- Calcula RSI(14), EMA(9/21/50) y MACD(12,26,9).
- Combina los indicadores: ≥2 alcistas → COMPRA, ≥2 bajistas → VENTA, si no → MANTENER.
- Solo avisa cuando la señal **cambia** respecto a la última revisión (evita spam).
- Guarda el estado en `state.json` para recordar la última señal.

## Disclaimer

Las señales son orientativas, no asesoría financiera. Crypto es volátil. Opera con dinero que puedas perder y usa stop-loss.
