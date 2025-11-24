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
#  FUNÇÃO PARA CONSULTAR WALLET
# ----------------------------------------------------------
def consultar_wallet(endereco: str):
    url_balance = "https://api.etherscan.io/v2/api"
    params_balance = {
        "module": "account",
        "action": "balance",
        "address": endereco,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url_balance, params=params_balance)
    data = response.json()

    # Verifica se o result é numérico
    if not isinstance(data.get("result"), str) or not data.get("result").isdigit():
        return {"erro": True, "mensagem": f"Erro da API: {data}"}

    balance_wei = int(data["result"])
    balance_eth = balance_wei / 10**18

    # PEGAR TOTAL DE TRANSAÇÕES
    url_txcount = "https://api.etherscan.io/v2/api"
    params_tx = {
        "module": "proxy",
        "action": "eth_getTransactionCount",
        "address": endereco,
        "tag": "latest",
        "apikey": ETHERSCAN_API_KEY
    }

    response_tx = requests.get(url_txcount, params=params_tx)
    data_tx = response_tx.json()

    if "result" not in data_tx:
        return {"erro": True, "mensagem": f"Erro da API ao buscar TX count: {data_tx}"}

    try:
        tx_count = int(data_tx["result"], 16)
    except:
        tx_count = 0

    return {
        "erro": False,
        "balance_eth": balance_eth,
        "tx_count": tx_count
    }


# ----------------------------------------------------------
#  FUNÇÃO PARA CONSULTAR TRANSAÇÃO
# ----------------------------------------------------------
def consultar_txid(txid: str):
    url = "https://api.etherscan.io/v2/api"
    params = {
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": txid,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    tx = data.get("result")

    # SE RESULTADO NÃO FOR DICIONÁRIO → ERRO DA API
    if not isinstance(tx, dict):
        return {"erro": True, "mensagem": f"Resposta inesperada da API: {tx}"}

    # CAMPOS DA TRANSAÇÃO
    from_addr = tx.get("from", "desconhecido")
    to_addr = tx.get("to", "desconhecido")
    value_hex = tx.get("value", "0x0")

    try:
        value_wei = int(value_hex, 16)
        value_eth = value_wei / 10**18
    except:
        value_eth = 0

    # PEGAR STATUS DA TRANSACTION RECEIPT
    params_status = {
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": txid,
        "apikey": ETHERSCAN_API_KEY
    }

    response_status = requests.get(url, params=params_status)
    data_status = response_status.json()
    receipt = data_status.get("result", {})

    status = receipt.get("status", "0x0")
    tx_status = "Sucesso" if status == "0x1" else "Falha"

    return {
        "erro": False,
        "tx_status": tx_status,
        "from": from_addr,
        "to": to_addr,
        "value_eth": value_eth
    }


# ----------------------------------------------------------
#  ROTA /VERIFICAR
# ----------------------------------------------------------
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
