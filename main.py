import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os

# --- הגדרות ID ---
ROLE_ADD_ID = 1449415392425410662    # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # רול Unverified
WELCOME_CHANNEL_ID = 1449406834032250931 
TICKET_CATEGORY_ID = 123456789012345678 # <--- שים כאן ID של קטגוריה שבה ייפתחו הטיקטים

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# --- מערכת טיקטים ---
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="❓", description="פתיחת טיקט לשאלה כללית"),
            discord.SelectOption(label="תרומה", emoji="💰", description="פתיחת טיקט בנושא תרומות"),
            discord.SelectOption(label="דיווח על שחקן", emoji="👮", description="דיווח על שחקן שעבר על החוקים"),
            discord.SelectOption(label="דיווח על חבר צוות", emoji="💂", description="דיווח על התנהלות של איש צוות"),
            discord.SelectOption(label="ערעור על ענישה", emoji="❌", description="ערעור על באן או קיק")
        ]
        super().__init__(placeholder="בחר קטגוריה...", options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        # יצירת ערוץ פרטי לטיקט
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
        )
        await interaction.response.send_message(f"הטיקט שלך נפתח בכתובת: {ticket_channel.mention}", ephemeral=True)
        await ticket_channel.send(f"היי {interaction.user.mention}, פתחת טיקט בנושא: **{self.values[0]}**. המתן למענה מהצוות.")

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="פתח טיקט 🎫", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        view = View()
        view.add_item(TicketDropdown())
        await interaction.response.send_message("אנא בחר את סיבת הפנייה:", view=view, ephemeral=True)

# --- מערכת אימות ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role_to_add = interaction.guild.get_role(ROLE_ADD_ID)
        try:
            await interaction.user.add_roles(role_to_add)
            await interaction.response.send_message("אומתת בהצלחה!", ephemeral=True)
        except:
            await interaction.response.send_message("שגיאה בהענקת רול.", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        self.add_view(VerifyView())
        self.add_view(TicketView())
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

# --- אירוע ברוכים הבאים ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=f"{member.name} - Welcome", description=f"Hey {member.mention}, Welcome to **{member.guild.name}**!", color=0x7289da)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

# --- פקודות Setup ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.send(embed=discord.Embed(title="אימות", description="לחצו למטה", color=0x00ff00), view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(
        title="פתיחת טיקט", 
        description="לחץ על הכפתור למטה כדי לפתוח טיקט וליצור קשר עם הצוות.", 
        color=0x5865f2
    )
    await ctx.send(embed=embed, view=TicketView())

bot.run(os.environ.get('DISCORD_TOKEN'))
