import os
import threading
import traceback
import sys
import discord
from discord.ext import commands
from discord import app_commands
import base64
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot Discord et API actifs !"}

def run_web():
    try:
        import uvicorn
        port = int(os.environ.get("PORT", 10000))
        print(f"Lancement du serveur web sur le port {port}...", flush=True)
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Erreur Web Server: {e}", flush=True)

class ObfBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        try:
            print("Synchronisation des commandes slash...", flush=True)
            await self.tree.sync()
            print("Commandes slash synchronisées avec succès !", flush=True)
        except Exception as e:
            print(f"Erreur sync tree: {e}", flush=True)

bot = ObfBot()

@bot.event
async def on_ready():
    print(f"Bot connecté avec succès : {bot.user.name}", flush=True)

@bot.tree.command(name="obf", description="Obfusque un script Lua (par texte ou par fichier)")
@app_commands.describe(
    code="Écris ton code Lua directement ici (optionnel)",
    file="Envoie ton fichier .lua ou .txt (optionnel)"
)
async def obf(interaction: discord.Interaction, code: str = None, file: discord.Attachment = None):
    try:
        script_content = None

        if file:
            if file.filename.endswith((".lua", ".txt")):
                file_bytes = await file.read()
                script_content = file_bytes.decode("utf-8", errors="ignore")
            else:
                await interaction.response.send_message("Le fichier doit obligatoirement être au format `.lua` ou `.txt`.", ephemeral=True)
                return
        elif code:
            script_content = code
        else:
            await interaction.response.send_message("Tu dois soit écrire du code dans le paramètre `code`, soit joindre un fichier `file` !", ephemeral=True)
            return

        encoded_bytes = base64.b64encode(script_content.encode("utf-8"))
        encoded_str = encoded_bytes.decode("utf-8")
        
        protected_script = f"""--[[\n    Protégé par KobyBot\n]]--\nlocal _script_data = "{encoded_str}";\nprint("Script chargé en sécurité !");\n"""

        file_name = "protected.lua"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(protected_script)

        await interaction.response.send_message("Ton script a été protégé avec succès :", file=discord.File(file_name), ephemeral=True)

        if os.path.exists(file_name):
            os.remove(file_name)
    except Exception as e:
        print(f"Erreur dans la commande obf: {e}", flush=True)

if __name__ == "__main__":
    try:
        print("Démarrage du thread web...", flush=True)
        threading.Thread(target=run_web, daemon=True).start()
        
        TOKEN = os.environ.get("TOKEN")
        if TOKEN:
            print("Token trouvé, lancement du bot Discord...", flush=True)
            bot.run(TOKEN)
        else:
            print("Erreur critique : Aucun Token trouvé dans les variables d'environnement !", flush=True)
    except Exception as e:
        print("Erreur fatale au lancement :", flush=True)
        traceback.print_exc()
        sys.exit(1)
        
