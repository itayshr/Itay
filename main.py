import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
import asyncio

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    
ROLE_REMOVE_ID = 1449424721862201414 
WELCOME_CHANNEL_ID = 1449406834032250931 
TICKET_CATEGORY_ID = 1449406834032250931 # וודא שזה ID של קטגוריה!
STAFF_ROLE_ID = 1449415392425410662      # וודא שזה ID של רול הצוות

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="סגור טיקט 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket_final")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("הערוץ יימחק בעוד 5 שניות...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="❓"),
            discord.SelectOption(label="תרומה", emoji="💰"),
            discord.SelectOption(label="דיווח על שחקן", emoji="🤷‍♂️"),
            discord.SelectOption(label="דיווח על חבר צוות", emoji="💂‍♂️"),
            discord.SelectOption(label="ערעור על ענישה", emoji="❌")
        ]
        super().__init__(placeholder="בחר קטגוריה לטיקט...", custom_id="ticket_select_persistent")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        # הרשאות לערוץ
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        try:
            channel = await guild.create_text_channel(
                name=f"{self.values[0]}-{interaction.user.name}",
                category=category if isinstance(category, discord.CategoryChannel) else None,
                overwrites=overwrites
            )
            await interaction.response.send_message(f"נפתח טיקט ב {channel.mention}", ephemeral=True)
            await channel.send(f"שלום {interaction.user.mention}, צוות השרת יתפנה אליך בקרוב.", view=CloseTicketView())
        except Exception as e:
            print(f"Error creating channel: {e}")
            await interaction.response.send_message(f"שגיאה: {e}", ephemeral=True)

class MainView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_persistent")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role_add = interaction.guild.get_role(ROLE_ADD_ID)
        try:
            await interaction.user.add_roles(role_add)
            await interaction.response.send_message("אומתת!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"שגיאת הרשאות: {e}", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        self.add_view(MainView())
        self.add_view(VerifyView())
        self.add_view(CloseTicketView())

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.send("מערכת אימות:", view=VerifyView())
    await ctx.send("מערכת טיקטים:", view=MainView())

bot.run("YOUR_TOKEN_HERE")
