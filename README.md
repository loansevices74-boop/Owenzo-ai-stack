# Owenzo AI Stack ⚡🚛⚽
Production automation & analytics systems by *Owens Ugiagbe Oriaikhi* —
COREN-registered engineer (R72198) • MSc IT • 8+ yrs cross-border ops
(Nigeria, India, South Sudan).

## Live Products
| App | What it does | Live |
|---|---|---|
| ⚡ WireSafe | BS 7671 cable sizing, breaker selection, V-drop checks, BOQ + PDF design reports | https://owenzo-ai-stack-e6fevjq9lvypyak9zsqz5q.streamlit.app |
| 🚛 OpsRecon | PO-vs-invoice matching, discrepancy flags, overcharge-risk quantification | [paste opsrecon URL] |
| ⚽ Soccer AI | Dixon-Coles + Glicko prediction engine, Telegram distribution, ~100% uptime | [paste soccer URL] |

## Architecture
- ai_router.py — $0 multi-provider AI failover router (Gemini → Groq → OpenRouter) with usage logging
- wiresafe.py — deterministic BS 7671 engine + fpdf2 reporting (Streamlit)
- opsrecon.py — pandas reconciliation dashboard (Streamlit)
- telegram_bot.py — pyTelegramBotAPI analyst bot
- test_router.py — router smoke test

## Stack
Python • Streamlit • pandas • fpdf2 • requests • pyTelegramBotAPI • Streamlit Cloud

## Contact
owen1877@yahoo.com • +234 816 681 9427 • linkedin.com/in/owensoriaikhi
