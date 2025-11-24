from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()

# API KEY
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "AGXEZ2RJDVU2FAGABN96USWWVBPNC4UCFH")

# CHAIN PADRÃO (Ethereum Mainnet = 1)
CHAIN_ID = "1"

# TEMPLATES
templates = Jinja2Templates(directory="static")

# STATIC FILES
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------------------------------------------
# HOME PAGE
# -------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------------------------------------------------------
# CONSULTA WALLET — API v2
# -------------------------------------------------------------------
def consultar_wallet(endereco: str):
    url = "https://api.etherscan.io/v2/api"

    params_balance = {
        "module": "account",
        "action": "balance",
        "address": endereco,
        "chainid": CHAIN_ID,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url, params=params_balance)
    data = response.json()

    # API v2 Formato:
    #   {"status":"1","message":"OK","result":{"balance":"123..."}}

    result = data.get("result", {})

    if not isinstance(result, dict):
        return {"erro": True, "mensagem": f"Erro inesperado da API: {data}"}

    balance_raw = result.get("balance", "0")

    if not balance_raw.isdigit():
        return {"erro": True, "mensagem": f"Balance inválido retornado: {balance_raw}"}

    balance_wei = int(balance_raw)
    balance_eth = balance_wei / 10**18

    # ----------------------------------------------------------------
    # PEGAR TRANSACTION COUNT — API v2
    # ----------------------------------------------------------------

    params_txcount = {
        "module": "account",
        "action": "txlist",
        "address": endereco,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 1,   # só para pegar quickly
        "sort": "desc",
        "chainid": CHAIN_ID,
        "apikey": ETHERSCAN_API_KEY
    }

    response_tx = requests.get(url, params=params_txcount)
    data_tx = response_tx.json()

    # txlist agora retorna um LIST
    tx_list = data_tx.get("result", [])

    if isinstance(tx_list, list):
        tx_count = len(tx_list)
    else:
        tx_count = 0

    return {
        "erro": False,
        "balance_eth": balance_eth,
        "tx_count": tx_count
    }


# -------------------------------------------------------------------
# CONSULTA TRANSAÇÃO — API v2
# -------------------------------------------------------------------
def consultar_txid(txid: str):

    url = "https://api.etherscan.io/v2/api"

    params = {
        "module": "transaction",
        "action": "gettxinfo",
        "txhash": txid,
        "chainid": CHAIN_ID,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    # API v2 formato:
    # {"status":"1","message":"OK","result":{"hash": "...", "from": "..."}}

    tx = data.get("result", {})

    if not isinstance(tx, dict):
        return {"erro": True, "mensagem": f"Formato inesperado da API: {tx}"}

    from_addr = tx.get("from", "desconhecido")
    to_addr = tx.get("to", "desconhecido")
    value_raw = tx.get("value", "0")

    try:
        value_eth = int(value_raw) / 10**18
    except:
        value_eth = 0

    # ----------------------------------------------------------------
    # STATUS
    # ----------------------------------------------------------------
    status = tx.get("txreceipt_status", "0")
    tx_status = "Sucesso" if status == "1" else "Falha"

    return {
        "erro": False,
        "tx_status": tx_status,
        "from": from_addr,
        "to": to_addr,
        "value_eth": value_eth
    }


# -------------------------------------------------------------------
# ROTA /VERIFICAR
# -------------------------------------------------------------------
@app.post("/verificar")
async def verificar(tipo: str = Form(...), valor: str = Form(...)):
    try:
        if tipo == "wallet":
            resultado = consultar_wallet(valor)

        elif tipo == "txid":
            resultado = consultar_txid(valor)

        else:
            return JSONResponse({"erro": True, "mensagem": "Tipo inválido."})

        return JSONResponse(resultado)

    except Exception as e:
        return JSONResponse({
            "erro": True,
            "mensagem": f"Erro interno: {str(e)}"
        })
