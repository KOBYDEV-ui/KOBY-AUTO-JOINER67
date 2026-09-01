import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Vérification du token Discord (si tu en as besoin)
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Attention : Le Token Discord n'est pas défini (mais l'API peut tourner).")
else:
    print("Token Discord détecté avec succès !")

# Structure des données pour ton script Roblox
class ServerData(BaseModel):
    job_id: str
    place_id: int

# Route d'accueil (pour vérifier que l'API est bien en ligne)
@app.get("/")
def home():
    return {"status": "Online", "message": "Backend Roblox Auto-Joiner actif sur Render !"}

# Route que ton script Lua (Roblox) va appeler pour récupérer les infos du serveur
@app.get("/get-server")
def get_server():
    # C'est ici que ton script Roblox viendra chercher le JobId
    return {
        "success": True,
        "jobId": "Mets_Ton_JobId_Ici", 
        "placeId": 000000000
    }

# Lancement du serveur web pour Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
  
