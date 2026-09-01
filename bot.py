import os
import discord
from discord.ext import commands
from discord import app_commands
import base64

class ObfBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        await self.tree.sync()
        print("Commandes slash synchronisées avec succès !")

bot = ObfBot()

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user.name}")

@bot.tree.command(name="obf", description="Obfusque un script Lua (par texte ou par fichier)")
@app_commands.describe(
    code="Écris ton code Lua directement ici (optionnel)",
    file="Envoie ton fichier .lua ou .txt (optionnel)"
)
async def obf(interaction: discord.Interaction, code: str = None, file: discord.Attachment = None):
    script_content = None

    # Vérifie si l'utilisateur a attaché un fichier
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

    # Simulation / Exemple de protection du script
    encoded_bytes = base64.b64encode(script_content.encode("utf-8"))
    encoded_str = encoded_bytes.decode("utf-8")
    
    protected_script = f"""--[[\n    Protégé par KobyBot\n]]--\nlocal _script_data = "{encoded_str}";\nprint("Script chargé en sécurité !");\n"""

    file_name = "protected.lua"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(protected_script)

    # Envoi du fichier protégé en message privé / éphémère (visible par lui seul)
    await interaction.response.send_message("Ton script a été protégé avec succès :", file=discord.File(file_name), ephemeral=True)

    if os.path.exists(file_name):
        os.remove(file_name)

if __name__ == "__main__":
    TOKEN = os.environ.get("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Erreur : Aucun Token trouvé dans les variables d'environnement !")
        
