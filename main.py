from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()

# API KEY
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "AGXEZ2RJDVU2FAGABN96USWWVBPNC4UCFH")

# TEMPLATES
templates = Jinja2Templates(directory="static")

# STATIC FILES
app.mount("/static", StaticFiles(directory="static"), name="static")

ETHERSCAN_URL = "https://api.etherscan.io/v2/api"


# ----------------------------------------------------------
# HOME PAGE
# ----------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ----------------------------------------------------------
# FUNÇÃO: CONSULTAR BALANÇO + TX COUNT
# ----------------------------------------------------------
def consultar_wallet(address: str, chainid: str):
    # Balance
    params_balance = {
        "module": "account",
        "action": "balance",
        "address": address,
        "chainid": chainid,
        "apikey": ETHERSCAN_API_KEY
    }

    r = requests.get(ETHERSCAN_URL, params=params_balance).json()

    if "result" not in r or not r["result"].isdigit():
        return {"erro": True, "mensagem": f"Erro ao consultar saldo: {r}"}

    balance_wei = int(r["result"])
    balance_eth = balance_wei / 10**18

    # TX Count
    params_txcount = {
        "module": "proxy",
        "action": "eth_getTransactionCount",
        "address": address,
        "tag": "latest",
        "chainid": chainid,
        "apikey": ETHERSCAN_API_KEY
    }

    r2 = requests.get(ETHERSCAN_URL, params=params_txcount).json()
    result = r2.get("result", "0x0")

    try:
        tx_count = int(result, 16)
    except:
        tx_count = 0

    return {
        "erro": False,
        "balance_eth": balance_eth,
        "tx_count": tx_count,
        "chain_id": chainid
    }


# ----------------------------------------------------------
# FUNÇÃO: CONSULTAR TRANSAÇÃO POR HASH
# ----------------------------------------------------------
def consultar_txid(txid: str, chainid: str):
    params_tx = {
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": txid,
        "chainid": chainid,
        "apikey": ETHERSCAN_API_KEY
    }

    r = requests.get(ETHERSCAN_URL, params=params_tx).json()
    tx = r.get("result")

    if not isinstance(tx, dict):
        return {"erro": True, "mensagem": f"Erro ao consultar TX: {tx}"}

    from_addr = tx.get("from", "N/A")
    to_addr = tx.get("to", "N/A")
    value_hex = tx.get("value", "0x0")

    try:
        value_eth = int(value_hex, 16) / 10**18
    except:
        value_eth = 0

    # Consultar status
    params_receipt = {
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": txid,
        "chainid": chainid,
        "apikey": ETHERSCAN_API_KEY
    }

    r2 = requests.get(ETHERSCAN_URL, params=params_receipt).json()
    status_hex = r2.get("result", {}).get("status", "0x0")
    status = "Sucesso" if status_hex == "0x1" else "Falha"

    return {
        "erro": False,
        "tx_status": status,
        "from": from_addr,
        "to": to_addr,
        "value_eth": value_eth,
        "chain_id": chainid
    }


# ----------------------------------------------------------
# FUNÇÃO: HISTÓRICO DE TRANSAÇÕES
# ----------------------------------------------------------
def consultar_historico(address: str, chainid: str):
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 50,
        "sort": "desc",
        "chainid": chainid,
        "apikey": ETHERSCAN_API_KEY
    }

    r = requests.get(ETHERSCAN_URL, params=params).json()

    if "result" not in r:
        return {"erro": True, "mensagem": f"Erro ao consultar histórico: {r}"}

    return {
        "erro": False,
        "transactions": r["result"]
    }


# ----------------------------------------------------------
# ROTA PRINCIPAL /verificar
# ----------------------------------------------------------
@app.post("/verificar")
async def verificar(
    tipo: str = Form(...),
    valor: str = Form(...),
    chainid: str = Form("1")  # default Ethereum mainnet
):
    try:
        if tipo == "wallet":
            result = consultar_wallet(valor, chainid)

        elif tipo == "txid":
            result = consultar_txid(valor, chainid)

        elif tipo == "historico":
            result = consultar_historico(valor, chainid)

        else:
            return JSONResponse({"erro": True, "mensagem": "Tipo inválido."})

        return JSONResponse(result)

    except Exception as e:
        return JSONResponse({
            "erro": True,
            "mensagem": f"Erro interno: {str(e)}"
        })
