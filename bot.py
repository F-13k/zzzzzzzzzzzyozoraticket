import os
import discord
from discord.ext import commands
from discord.ui import Button, View
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

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer le ticket 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Fermeture du ticket dans 3 secondes...", ephemeral=True)
        # Supprime le salon du ticket
        await interaction.channel.delete()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ouvrir un ticket 🎫", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_callback(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user

        # Vérifie si un ticket existe déjà pour ce membre
        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"Tu as déjà un ticket ouvert ici : {existing_channel.mention}", ephemeral=True)
            return

        # Configuration des permissions du salon privé
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            # Le bot lui-même a accès
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Si tu as un rôle de modérateur, tu peux décommenter et remplacer par l'ID de ton rôle de modo :
        # mod_role_id = TON_ID_DE_ROLE_MODO
        # mod_role = guild.get_role(mod_role_id)
        # if mod_role:
        #     overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Crée le salon dans la catégorie ou le serveur
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{member.name}",
            overwrites=overwrites,
            topic=f"Ticket de support de {member.name}"
        )

        embed = discord.Embed(
            title=f"🎫 Support - {member.name}",
            description="Bonjour !\nExplique ton problème ou ta demande en détail ici. Un membre de l'équipe de **Yozora** te répondra dès que possible.\n\nClique sur le bouton ci-dessous pour fermer le ticket lorsque c'est réglé.",
            color=discord.Color.blue()
        )
        
        await ticket_channel.send(content=f"{member.mention}", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ton ticket a été créé avec succès : {ticket_channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def createticket(ctx):
    embed = discord.Embed(
        title="🎫 Besoin d'aide ?",
        description="Clique sur le bouton ci-dessous pour ouvrir un ticket privé avec l'équipe de **Yozora 🌸**.",
        color=discord.Color.purple()
    )
    view = TicketView()
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)