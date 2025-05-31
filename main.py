from fastapi import FastAPI
import requests

app = FastAPI()

API_KEY = "AGXEZ2RJDVU2FAGABN96USWWVBPNC4UCFH"
BASE_URL = "https://api.etherscan.io/api"

@app.get("/wallet/{address}")
def consultar_wallet(address: str):
    url = f"{BASE_URL}?module=account&action=balance&address={address}&tag=latest&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "1":
        balance_wei = int(data["result"])
        balance_eth = balance_wei / 1e18
        return {
            "wallet": address,
            "balance_eth": balance_eth
        }
    else:
        return {
            "error": data.get("message", "Erro ao consultar wallet")
        }

@app.get("/tx/{txid}")
def consultar_tx(txid: str):
    url = f"{BASE_URL}?module=proxy&action=eth_getTransactionByHash&txhash={txid}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    tx = data.get("result")
    if tx:
        return {
            "from": tx["from"],
            "to": tx["to"],
            "value_wei": int(tx["value"], 16),
            "gas": int(tx["gas"], 16),
            "hash": tx["hash"]
        }
    else:
        return {
            "error": data.get("message", "Transação não encontrada")
        }
