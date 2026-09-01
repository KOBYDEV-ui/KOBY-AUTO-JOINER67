const {
  Client,
  GatewayIntentBits,
  REST,
  Routes,
  SlashCommandBuilder,
  PermissionFlagsBits,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  ModalBuilder,
  TextInputBuilder,
  TextInputStyle,
  EmbedBuilder
} = require("discord.js");

require("dotenv").config();
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const express = require("express");

const DATA_DIR = path.join(__dirname, "data");
const DB_FILE = path.join(DATA_DIR, "keys.json");
const SCRIPTS_DIR = path.join(__dirname, "scripts");

fs.mkdirSync(DATA_DIR, { recursive: true });
fs.mkdirSync(SCRIPTS_DIR, { recursive: true });
if (!fs.existsSync(DB_FILE)) fs.writeFileSync(DB_FILE, "[]");

function loadKeys() {
  try { return JSON.parse(fs.readFileSync(DB_FILE, "utf8")); }
  catch { return []; }
}
function saveKeys(keys) {
  fs.writeFileSync(DB_FILE, JSON.stringify(keys, null, 2));
}
function makeKey() {
  const raw = crypto.randomBytes(9).toString("base64url").toUpperCase();
  return `KOBY-${raw.slice(0,4)}-${raw.slice(4,8)}-${raw.slice(8,12)}`;
}
function durationMs(duration) {
  const map = { "1d": 86400000, "7d": 604800000, "30d": 2592000000, "365d": 31536000000, "life": null };
  return Object.prototype.hasOwnProperty.call(map, duration) ? map[duration] : undefined;
}
function isAdmin(interaction) {
  if (interaction.memberPermissions?.has(PermissionFlagsBits.Administrator)) return true;
  return !!process.env.ADMIN_ROLE_ID &&
    interaction.member?.roles?.cache?.has(process.env.ADMIN_ROLE_ID);
}
function publicKeyInfo(k) {
  return {
    key: k.key,
    script: k.script,
    duration: k.duration,
    createdAt: k.createdAt,
    redeemedAt: k.redeemedAt || null,
    expiresAt: k.expiresAt || null,
    discordUserId: k.discordUserId || null,
    hwid: k.hwid || null,
    status: k.status
  };
}

const commands = [
  new SlashCommandBuilder().setName("panel").setDescription("Ouvre le panneau KOBY Keys"),
  new SlashCommandBuilder().setName("generate").setDescription("Génère des clés")
    .addStringOption(o => o.setName("script").setDescription("Nom du script").setRequired(true))
    .addStringOption(o => o.setName("duration").setDescription("Durée: 1d, 7d, 30d, 365d, life").setRequired(true))
    .addIntegerOption(o => o.setName("quantity").setDescription("Quantité 1-20").setRequired(false).setMinValue(1).setMaxValue(20)),
  new SlashCommandBuilder().setName("keys").setDescription("Liste les clés récentes"),
  new SlashCommandBuilder().setName("reset-hwid").setDescription("Réinitialise le HWID d'une clé")
    .addStringOption(o => o.setName("key").setDescription("Clé").setRequired(true)),
  new SlashCommandBuilder().setName("redeem").setDescription("Associe une clé à ton compte Discord")
    .addStringOption(o => o.setName("key").setDescription("Clé").setRequired(true))
].map(c => c.toJSON());

async function registerCommands() {
  const rest = new REST({ version: "10" }).setToken(process.env.DISCORD_TOKEN);
  const route = process.env.GUILD_ID
    ? Routes.applicationGuildCommands(process.env.CLIENT_ID, process.env.GUILD_ID)
    : Routes.applicationCommands(process.env.CLIENT_ID);
  await rest.put(route, { body: commands });
}

function panelEmbed() {
  return new EmbedBuilder()
    .setTitle("🔐 KOBY Keys V1")
    .setDescription("Gestion des licences et des scripts.")
    .addFields(
      { name: "🔑 Générer", value: "Crée de nouvelles clés avec une durée.", inline: true },
      { name: "🎟️ Redeem", value: "Active une clé pour ton compte.", inline: true },
      { name: "👁️ Voir les clés", value: "Affiche les dernières clés.", inline: true },
      { name: "🔄 Reset HWID", value: "Réinitialise le HWID d'une clé.", inline: true }
    )
    .setFooter({ text: "KOBY Keys V1" });
}

function panelRows() {
  return [
    new ActionRowBuilder().addComponents(
      new ButtonBuilder().setCustomId("kk_generate").setLabel("Generate Keys").setEmoji("🔑").setStyle(ButtonStyle.Primary),
      new ButtonBuilder().setCustomId("kk_redeem").setLabel("Redeem Key").setEmoji("🎟️").setStyle(ButtonStyle.Success),
      new ButtonBuilder().setCustomId("kk_list").setLabel("View Keys").setEmoji("👁️").setStyle(ButtonStyle.Secondary)
    ),
    new ActionRowBuilder().addComponents(
      new ButtonBuilder().setCustomId("kk_reset").setLabel("Reset HWID").setEmoji("🔄").setStyle(ButtonStyle.Danger)
    )
  ];
}

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once("ready", () => {
  console.log(`✅ Connecté en tant que ${client.user.tag}`);
});

client.on("interactionCreate", async interaction => {
  try {
    if (interaction.isChatInputCommand()) {
      if (interaction.commandName === "panel") {
        return interaction.reply({ embeds: [panelEmbed()], components: panelRows() });
      }

      if (interaction.commandName === "generate") {
        if (!isAdmin(interaction)) return interaction.reply({ content: "❌ Admin uniquement.", ephemeral: true });
        const script = interaction.options.getString("script").trim();
        const duration = interaction.options.getString("duration").toLowerCase();
        const quantity = interaction.options.getInteger("quantity") || 1;
        if (durationMs(duration) === undefined) {
          return interaction.reply({ content: "❌ Durée invalide. Utilise `1d`, `7d`, `30d`, `365d` ou `life`.", ephemeral: true });
        }
        const keys = loadKeys();
        const created = [];
        for (let i = 0; i < quantity; i++) {
          let key;
          do { key = makeKey(); } while (keys.some(k => k.key === key));
          const item = {
            key, script, duration, createdAt: new Date().toISOString(),
            redeemedAt: null, expiresAt: null, discordUserId: null, hwid: null,
            status: "unused"
          };
          keys.push(item);
          created.push(key);
        }
        saveKeys(keys);
        return interaction.reply({
          content: `✅ **${created.length}** clé(s) créée(s) pour **${script}** — durée **${duration}**\n\`\`\`\n${created.join("\n")}\n\`\`\``,
          ephemeral: true
        });
      }

      if (interaction.commandName === "keys") {
        if (!isAdmin(interaction)) return interaction.reply({ content: "❌ Admin uniquement.", ephemeral: true });
        const keys = loadKeys().slice(-10).reverse();
        const text = keys.length
          ? keys.map(k => `\`${k.key}\` • ${k.script} • ${k.status} • ${k.expiresAt || "lifetime/non-redeemed"}`).join("\n")
          : "Aucune clé.";
        return interaction.reply({ embeds: [new EmbedBuilder().setTitle("🔑 Dernières clés").setDescription(text)], ephemeral: true });
      }

      if (interaction.commandName === "reset-hwid") {
        if (!isAdmin(interaction)) return interaction.reply({ content: "❌ Admin uniquement.", ephemeral: true });
        const keyValue = interaction.options.getString("key").trim().toUpperCase();
        const keys = loadKeys();
        const k = keys.find(x => x.key === keyValue);
        if (!k) return interaction.reply({ content: "❌ Clé introuvable.", ephemeral: true });
        k.hwid = null;
        saveKeys(keys);
        return interaction.reply({ content: `✅ HWID réinitialisé pour \`${k.key}\`.`, ephemeral: true });
      }

      if (interaction.commandName === "redeem") {
        const keyValue = interaction.options.getString("key").trim().toUpperCase();
        const keys = loadKeys();
        const k = keys.find(x => x.key === keyValue);
        if (!k) return interaction.reply({ content: "❌ Clé introuvable.", ephemeral: true });
        if (k.status !== "unused") return interaction.reply({ content: "❌ Cette clé a déjà été utilisée ou désactivée.", ephemeral: true });
        const ms = durationMs(k.duration);
        k.redeemedAt = new Date().toISOString();
        k.expiresAt = ms === null ? null : new Date(Date.now() + ms).toISOString();
        k.discordUserId = interaction.user.id;
        k.status = "active";
        saveKeys(keys);
        return interaction.reply({ content: `✅ Clé activée pour **${interaction.user.tag}**.\nScript: **${k.script}**\nExpiration: **${k.expiresAt || "Lifetime"}**`, ephemeral: true });
      }
    }

    if (interaction.isButton()) {
      if (interaction.customId === "kk_generate") {
        if (!isAdmin(interaction)) return interaction.reply({ content: "❌ Admin uniquement.", ephemeral: true });
        const modal = new ModalBuilder().setCustomId("kk_generate_modal").setTitle("Generate KOBY Key");
        const script = new TextInputBuilder().setCustomId("script").setLabel("Script").setStyle(TextInputStyle.Short).setPlaceholder("KOBY HUB").setRequired(true);
        const duration = new TextInputBuilder().setCustomId("duration").setLabel("Durée (1d / 7d / 30d / 365d / life)").setStyle(TextInputStyle.Short).setValue("30d").setRequired(true);
        const quantity = new TextInputBuilder().setCustomId("quantity").setLabel("Quantité (1-20)").setStyle(TextInputStyle.Short).setValue("1").setRequired(true);
        modal.addComponents(new ActionRowBuilder().addComponents(script), new ActionRowBuilder().addComponents(duration), new ActionRowBuilder().addComponents(quantity));
        return interaction.showModal(modal);
      }

      if (interaction.customId === "kk_redeem" || interaction.customId === "kk_reset") {
        const modal = new ModalBuilder().setCustomId(interaction.customId === "kk_redeem" ? "kk_redeem_modal" : "kk_reset_modal")
          .setTitle(interaction.customId === "kk_redeem" ? "Redeem Key" : "Reset HWID");
        const keyInput = new TextInputBuilder().setCustomId("key").setLabel("KOBY Key").setStyle(TextInputStyle.Short).setPlaceholder("KOBY-XXXX-XXXX-XXXX").setRequired(true);
        modal.addComponents(new ActionRowBuilder().addComponents(keyInput));
        return interaction.showModal(modal);
      }

      if (interaction.customId === "kk_list") {
        if (!isAdmin(interaction)) return interaction.reply({ content: "❌ Admin uniquement.", ephemeral: true });
        const keys = loadKeys().slice(-10).reverse();
        const text = keys.length ? keys.map(k => `\`${k.key}\` • ${k.script} • ${k.status}`).join("\n") : "Aucune clé.";
        return interaction.reply({ embeds: [new EmbedBuilder().setTitle("👁️ KOBY Keys").setDescription(text)], ephemeral: true });
      }
    }

    if (interaction.isModalSubmit()) {
      if (interaction.customId === "kk_generate_modal") {
        if (!isAdmin(interaction)) return interaction.reply({ content: "❌ Admin uniquement.", ephemeral: true });
        const script = interaction.fields.getTextInputValue("script").trim();
        const duration = interaction.fields.getTextInputValue("duration").trim().toLowerCase();
        const quantity = Math.max(1, Math.min(20, parseInt(interaction.fields.getTextInputValue("quantity"), 10) || 1));
        if (durationMs(duration) === undefined) return interaction.reply({ content: "❌ Durée invalide.", ephemeral: true });
        const keys = loadKeys(), created = [];
        for (let i = 0; i < quantity; i++) {
          let key;
          do { key = makeKey(); } while (keys.some(k => k.key === key));
          keys.push({ key, script, duration, createdAt: new Date().toISOString(), redeemedAt: null, expiresAt: null, discordUserId: null, hwid: null, status: "unused" });
          created.push(key);
        }
        saveKeys(keys);
        return interaction.reply({ content: `✅ Clés créées:\n\`\`\`\n${created.join("\n")}\n\`\`\``, ephemeral: true });
      }

      const keyValue = interaction.fields.getTextInputValue("key").trim().toUpperCase();
      const keys = loadKeys();
      const k = keys.find(x => x.key === keyValue);
      if (!k) return interaction.reply({ content: "❌ Clé introuvable.", ephemeral: true });

      if (interaction.customId === "kk_reset_modal") {
        if (!isAdmin(interaction)) return interaction.reply({ content: "❌ Admin uniquement.", ephemeral: true });
        k.hwid = null;
        saveKeys(keys);
        return interaction.reply({ content: `✅ HWID réinitialisé pour \`${k.key}\`.`, ephemeral: true });
      }

      if (interaction.customId === "kk_redeem_modal") {
        if (k.status !== "unused") return interaction.reply({ content: "❌ Cette clé n'est plus disponible.", ephemeral: true });
        const ms = durationMs(k.duration);
        k.redeemedAt = new Date().toISOString();
        k.expiresAt = ms === null ? null : new Date(Date.now() + ms).toISOString();
        k.discordUserId = interaction.user.id;
        k.status = "active";
        saveKeys(keys);
        return interaction.reply({ content: `✅ **Redeem réussi**\nScript: ${k.script}\nExpiration: ${k.expiresAt || "Lifetime"}`, ephemeral: true });
      }
    }
  } catch (err) {
    console.error(err);
    if (!interaction.replied && !interaction.deferred) {
      await interaction.reply({ content: "❌ Une erreur est survenue.", ephemeral: true }).catch(() => {});
    }
  }
});

const app = express();
app.use(express.json({ limit: "32kb" }));

function validApiSecret(req) {
  const provided = req.headers["x-api-secret"];
  return !!process.env.API_SECRET && provided === process.env.API_SECRET;
}

function findValidKey(keyValue, script, hwid) {
  const keys = loadKeys();
  const k = keys.find(x => x.key === String(keyValue || "").trim().toUpperCase());
  if (!k) return { ok: false, error: "invalid_key" };
  if (k.status === "banned" || k.status === "disabled") return { ok: false, error: "disabled_key" };
  if (k.script !== script) return { ok: false, error: "wrong_script" };
  if (k.status === "unused") return { ok: false, error: "not_redeemed" };
  if (k.expiresAt && Date.now() >= Date.parse(k.expiresAt)) {
    k.status = "expired";
    saveKeys(keys);
    return { ok: false, error: "expired" };
  }
  if (k.hwid && k.hwid !== hwid) return { ok: false, error: "hwid_mismatch" };
  if (!k.hwid && hwid) {
    k.hwid = hwid;
    saveKeys(keys);
  }
  return { ok: true, key: k };
}

app.get("/health", (_req, res) => res.json({ ok: true, service: "KOBY Keys V1" }));

app.post("/v1/validate", (req, res) => {
  const { key, script, hwid } = req.body || {};
  const result = findValidKey(key, script, hwid);
  if (!result.ok) return res.status(403).json({ ok: false, error: result.error });
  return res.json({
    ok: true,
    script: result.key.script,
    expiresAt: result.key.expiresAt,
    lifetime: !result.key.expiresAt
  });
});

app.post("/v1/redeem", (req, res) => {
  const { key, discordUserId } = req.body || {};
  const keys = loadKeys();
  const k = keys.find(x => x.key === String(key || "").trim().toUpperCase());
  if (!k) return res.status(404).json({ ok: false, error: "invalid_key" });
  if (k.status !== "unused") return res.status(409).json({ ok: false, error: "already_redeemed" });
  const ms = durationMs(k.duration);
  k.redeemedAt = new Date().toISOString();
  k.expiresAt = ms === null ? null : new Date(Date.now() + ms).toISOString();
  k.discordUserId = discordUserId || null;
  k.status = "active";
  saveKeys(keys);
  res.json({ ok: true, script: k.script, expiresAt: k.expiresAt });
});

app.post("/v1/reset-hwid", (req, res) => {
  if (!validApiSecret(req)) return res.status(401).json({ ok: false, error: "unauthorized" });
  const keys = loadKeys();
  const k = keys.find(x => x.key === String(req.body?.key || "").trim().toUpperCase());
  if (!k) return res.status(404).json({ ok: false, error: "invalid_key" });
  k.hwid = null;
  saveKeys(keys);
  res.json({ ok: true });
});

app.get("/v1/script/:script", (req, res) => {
  const key = req.query.key;
  const hwid = req.query.hwid || "";
  const scriptName = req.params.script;
  const result = findValidKey(key, scriptName, hwid);
  if (!result.ok) return res.status(403).send(`-- KOBY Keys: ${result.error}`);
  const safeName = path.basename(scriptName).replace(/[^a-zA-Z0-9._-]/g, "");
  const file = path.join(SCRIPTS_DIR, safeName.endsWith(".lua") ? safeName : `${safeName}.lua`);
  if (!fs.existsSync(file)) return res.status(404).send("-- KOBY Keys: script_not_found");
  res.type("text/plain").send(fs.readFileSync(file, "utf8"));
});

const port = Number(process.env.API_PORT || 3000);
app.listen(port, () => console.log(`🌐 API KOBY Keys sur le port ${port}`));

registerCommands()
  .then(() => client.login(process.env.DISCORD_TOKEN))
  .catch(err => {
    console.error("❌ Impossible de démarrer:", err);
    process.exit(1);
  });
