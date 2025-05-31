import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static")

ETHERSCAN_API_KEY = "AGXEZ2RJDVU2FAGABN96USWWVBPNC4UCFH"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/verificar")
async def verificar(tipo: str = Form(...), valor: str = Form(...)):
    if tipo == "wallet":
        # Consulta saldo e número de transações
        url_balance = (
            f"https://api.etherscan.io/api?module=account&action=balance&address={valor}&tag=latest&apikey={ETHERSCAN_API_KEY}"
        )
        url_txcount = (
            f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionCount&address={valor}&tag=latest&apikey={ETHERSCAN_API_KEY}"
        )
        res_balance = requests.get(url_balance).json()
        res_txcount = requests.get(url_txcount).json()

        if res_balance.get("status") == "1" and "result" in res_balance and "result" in res_txcount:
            balance_wei = int(res_balance["result"])
            tx_count = int(res_txcount["result"], 16)  # hex to int
            return {
                "status": "1",
                "balance_wei": balance_wei,
                "balance_eth": balance_wei / 1e18,
                "tx_count": tx_count,
            }
        else:
            return {"status": "0", "message": "Erro ao consultar carteira."}

    elif tipo == "txid":
        # Consulta detalhes da transação
        url_tx = (
            f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={valor}&apikey={ETHERSCAN_API_KEY}"
        )
        url_receipt = (
            f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionReceipt&txhash={valor}&apikey={ETHERSCAN_API_KEY}"
        )
        res_tx = requests.get(url_tx).json()
        res_receipt = requests.get(url_receipt).json()

        if "result" in res_tx and res_tx["result"] and "result" in res_receipt and res_receipt["result"]:
            tx = res_tx["result"]
            receipt = res_receipt["result"]

            value_wei = int(tx["value"], 16)
            block_number = int(tx["blockNumber"], 16) if tx["blockNumber"] else None
            status = receipt["status"] if "status" in receipt else None

            return {
                "status": "1",
                "tx_hash": valor,
                "from": tx["from"],
                "to": tx["to"],
                "value_wei": value_wei,
                "value_eth": value_wei / 1e18,
                "block_number": block_number,
                "tx_status": "Success" if status == "0x1" else "Fail",
            }
        else:
            return {"status": "0", "message": "Transação não encontrada."}

    else:
        return {"status": "0", "message": "Tipo inválido."}
