import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Select
from flask import Flask
from threading import Thread

# --- SERVEUR WEB POUR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Le bot de tickets est en ligne !"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION DU BOT DISCORD ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Bouton pour fermer le ticket
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer le ticket 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Fermeture du ticket dans 3 secondes...", ephemeral=True)
        await interaction.channel.delete()

# Menu déroulant des tickets avec tes ID de catégories intégrés
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support / Aide", description="Une question ou besoin d'aide sur le serveur", emoji="🎫", value="support"),
            discord.SelectOption(label="Contacter les Fondateurs", description="Pour une affaire importante réservée aux fondateurs", emoji="👑", value="fondateurs"),
            discord.SelectOption(label="Signaler un abus", description="Signaler un abus de pouvoir ou un comportement grave", emoji="🛑", value="abus"),
            discord.SelectOption(label="Partenariat", description="Proposer ou demander un partenariat", emoji="🤝", value="partenariat"),
            discord.SelectOption(label="Signalement / Plainte", description="Signaler un membre ou un problème", emoji="⚠️", value="plainte"),
            discord.SelectOption(label="Autre", description="Pour toute autre demande", emoji="📌", value="autre")
        ]
        super().__init__(placeholder="Choisis le sujet de ton ticket...", min_values=1, max_values=1, options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        ticket_type = self.values[0]

        # Association des types avec tes ID de catégories
        category_ids = {
            "support": 1529687940312072385,
            "fondateurs": 1529688368747909313,
            "abus": 1529688444102643733,
            "partenariat": 1529688545172914176,
            "plainte": 1529688646192595114,
            "autre": 1529688715339894844
        }

        target_category_id = category_ids.get(ticket_type)
        category = guild.get_channel(target_category_id) if target_category_id else None

        channel_name = f"ticket-{ticket_type}-{member.name.lower()}"
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"Tu as déjà un ticket ouvert de ce type : {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket {ticket_type.upper()} de {member.name}"
        )

        embed = discord.Embed(
            title=f"🎫 Ticket : {ticket_type.capitalize()} - {member.name}",
            description=f"Bonjour {member.mention} !\nExplique ta demande concernant le sujet **{ticket_type.upper()}**. L'équipe concernée va te répondre.\n\nClique sur le bouton ci-dessous pour fermer le ticket une fois résolu.",
            color=discord.Color.pink()
        )
        
        await ticket_channel.send(content=f"{member.mention}", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ton ticket a été créé ici : {ticket_channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def createticket(ctx):
    embed = discord.Embed(
        title="🎫 Centre de Support - Yozora 🌸",
        description="Besoin d'aide, de contacter les fondateurs, de signaler un abus ou un partenariat ?\nSélectionne la catégorie correspondante dans le menu déroulant ci-dessous pour ouvrir un salon privé.",
        color=discord.Color.pink()
    )
    view = TicketView()
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
