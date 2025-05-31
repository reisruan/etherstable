from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

# Substitua pela sua API KEY
ETHERSCAN_API_KEY = "AGXEZ2RJDVU2FAGABN96USWWVBPNC4UCFH"

# Monta a pasta static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/verificar")
async def verificar(tipo: str = Form(...), valor: str = Form(...)):
    if tipo == "wallet":
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={valor}&tag=latest&apikey={ETHERSCAN_API_KEY}"
    elif tipo == "txid":
        url = f"https://api.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={valor}&apikey={ETHERSCAN_API_KEY}"
    else:
        return {"erro": "Tipo inválido"}

    response = requests.get(url)
    return response.json()
