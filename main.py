import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os

# --- הגדרות ID - חובה למלא נכון! ---
ROLE_ADD_ID = 1449415392425410662    
ROLE_REMOVE_ID = 1449424721862201414 
WELCOME_CHANNEL_ID = 1449406834032250931 
TICKET_CATEGORY_ID = 123456789012345678 # <--- תחליף למספר שהעתקת מהקטגוריה!

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# --- תפריט בחירת סיבת טיקט ---
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="❓"),
            discord.SelectOption(label="תרומה", emoji="💰"),
            discord.SelectOption(label="דיווח על שחקן", emoji="👤"),
            discord.SelectOption(label="דיווח על חבר צוות", emoji="💂"),
            discord.SelectOption(label="ערעור על ענישה", emoji="❌")
        ]
        super().__init__(placeholder="בחר קטגוריה...", options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) # מונע את השגיאה של Failed
        
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        if not category:
            return await interaction.followup.send("שגיאה: קטגוריית הטיקטים לא נמצאה. וודא שה-ID נכון.", ephemeral=True)

        # יצירת הערוץ עם הרשאות פרטיות
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
        )
        
        embed = discord.Embed(
            title="טיקט חדש",
            description=f"היי {interaction.user.mention}, פתחת פנייה בנושא: **{self.values[0]}**.\nנא להמתין למענה מהצוות.",
            color=0x5865f2
        )
        await ticket_channel.send(content="@here", embed=embed)
        await interaction.followup.send(f"הטיקט שלך נפתח כאן: {ticket_channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="פתח טיקט 🎫", style=discord.ButtonStyle.blurple, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        # שולח את התפריט כהודעה שרק המשתמש רואה
        view = View()
        view.add_item(TicketDropdown())
        await interaction.response.send_message("אנא בחר את סיבת הפנייה:", view=view, ephemeral=True)

# --- מערכת אימות ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me_v2")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role = interaction.guild.get_role(ROLE_ADD_ID)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("אומתת בהצלחה!", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        self.add_view(VerifyView())
        self.add_view(TicketView())
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=f"{member.name} - Welcome", description=f"Hey {member.mention}, Welcome to **{member.guild.name}**!", color=0x7289da)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_all(ctx):
    # שולח את שתי המערכות בבת אחת או בנפרד
    await ctx.send(embed=discord.Embed(title="אימות שרת", description="לחצו לאימות", color=0x00ff00), view=VerifyView())
    await ctx.send(embed=discord.Embed(title="פתיחת טיקט", description="לחצו לפתיחת פנייה לצוות", color=0x5865f2), view=TicketView())

bot.run(os.environ.get('DISCORD_TOKEN'))
