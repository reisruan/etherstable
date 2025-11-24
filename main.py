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


# ----------------------------------------------------------
#  HOME PAGE
# ----------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ----------------------------------------------------------
#  FUNÇÃO PARA CONSULTAR WALLET (V2)
# ----------------------------------------------------------
def consultar_wallet(endereco: str, chainid: str):
    url_balance = "https://api.etherscan.io/v2/api"

    params_balance = {
        "chainid": chainid,
        "module": "account",
        "action": "balance",
        "address": endereco,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url_balance, params=params_balance)
    data = response.json()

    result = data.get("result")

    # API v2 retorna result como string numérica ou mensagem de erro.
    if result is None or not isinstance(result, str) or not result.isdigit():
        return {"erro": True, "mensagem": f"Erro da API: {data}"}

    # Converter balance
    balance_wei = int(result)
    balance_eth = balance_wei / 10**18

    # ----------------------------------------------------
    # Pegando TX Count
    # ----------------------------------------------------
    params_tx = {
        "chainid": chainid,
        "module": "proxy",
        "action": "eth_getTransactionCount",
        "address": endereco,
        "tag": "latest",
        "apikey": ETHERSCAN_API_KEY
    }

    response_tx = requests.get(url_balance, params=params_tx)
    data_tx = response_tx.json()

    tx_raw = data_tx.get("result")

    try:
        tx_count = int(tx_raw, 16)
    except:
        tx_count = 0

    return {
        "erro": False,
        "balance_eth": balance_eth,
        "tx_count": tx_count,
        "chain_id": chainid
    }


# ----------------------------------------------------------
#  FUNÇÃO PARA CONSULTAR TXID (V2)
# ----------------------------------------------------------
def consultar_txid(txid: str, chainid: str):
    url = "https://api.etherscan.io/v2/api"

    params = {
        "chainid": chainid,
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": txid,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    tx = data.get("result")

    # API v2 retorna erro como string
    if not isinstance(tx, dict):
        return {"erro": True, "mensagem": f"Erro da API: {tx}"}

    # Campos da transação
    from_addr = tx.get("from", "desconhecido")
    to_addr = tx.get("to", "desconhecido")
    value_hex = tx.get("value", "0x0")

    # Converter valor
    try:
        value_wei = int(value_hex, 16)
        value_eth = value_wei / 10**18
    except:
        value_eth = 0

    # ----------------------------------------------------
    # Recebendo Transaction Receipt
    # ----------------------------------------------------
    params_status = {
        "chainid": chainid,
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": txid,
        "apikey": ETHERSCAN_API_KEY
    }

    resp_status = requests.get(url, params=params_status)
    data_status = resp_status.json()

    receipt = data_status.get("result", {})

    status_hex = receipt.get("status", "0x0")
    tx_status = "Sucesso" if status_hex == "0x1" else "Falha"

    return {
        "erro": False,
        "tx_status": tx_status,
        "from": from_addr,
        "to": to_addr,
        "value_eth": value_eth,
        "chain_id": chainid
    }


# ----------------------------------------------------------
#  ROTA /VERIFICAR (ATUALIZADA)
# ----------------------------------------------------------
@app.post("/verificar")
async def verificar(
    tipo: str = Form(...),
    valor: str = Form(...),
    chainid: str = Form(...)
):
    try:
        if tipo == "wallet":
            resultado = consultar_wallet(valor, chainid)

        elif tipo == "txid":
            resultado = consultar_txid(valor, chainid)

        else:
            return JSONResponse({"erro": True, "mensagem": "Tipo inválido."})

        return JSONResponse(resultado)

    except Exception as e:
        return JSONResponse({
            "erro": True,
            "mensagem": f"Erro interno: {str(e)}"
        })
