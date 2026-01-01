import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    
ROLE_REMOVE_ID = 1449424721862201414 
WELCOME_CHANNEL_ID = 1449406834032250931 
TICKET_CATEGORY_ID = 1456352365295829133 # הקטגוריה ששלחת

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="❓"),
            discord.SelectOption(label="תרומה", emoji="💰"),
            discord.SelectOption(label="דיווח על שחקן", emoji="👤"),
            discord.SelectOption(label="דיווח על חבר צוות", emoji="💂"),
            discord.SelectOption(label="ערעור על ענישה", emoji="❌")
        ]
        super().__init__(placeholder="בחר קטגוריה...", options=options, custom_id="ticket_select_v3")

    async def callback(self, interaction: discord.Interaction):
        # אישור קבלת הפקודה כדי למנוע Failed
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        if not category:
            return await interaction.followup.send("שגיאה: לא הצלחתי למצוא את הקטגוריה בשרת.", ephemeral=True)

        try:
            # יצירת חדר הטיקט
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=category,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True),
                    guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
                }
            )
            
            embed = discord.Embed(
                title="טיקט חדש נפתח",
                description=f"שלום {interaction.user.mention},\nפתחת פנייה בנושא: **{self.values[0]}**.\nצוות השרת יתפנה אלייך בהקדם.",
                color=0x5865f2
            )
            embed.set_footer(text="ליצירת קשר עם ההנהלה")
            
            await ticket_channel.send(content=f"{interaction.user.mention} | @here", embed=embed)
            await interaction.followup.send(f"הטיקט שלך נוצר בהצלחה: {ticket_channel.mention}", ephemeral=True)
            
        except Exception as e:
            print(f"Error creating ticket: {e}")
            await interaction.followup.send(f"שגיאה ביצירת החדר: וודא שלבוט יש הרשאת Manage Channels.", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="פתח טיקט 🎫", style=discord.ButtonStyle.blurple, custom_id="open_ticket_final")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        view = View()
        view.add_item(TicketDropdown())
        await interaction.response.send_message("אנא בחר את סיבת הפנייה מתוך הרשימה:", view=view, ephemeral=True)

# --- שאר המערכות (אימות וברוכים הבאים) ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_main")
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
async def setup_ticket(ctx):
    embed = discord.Embed(title="פתיחת טיקט", description="לחצו על הכפתור למטה כדי לפתוח פנייה לצוות השרת.", color=0x5865f2)
    await ctx.send(embed=embed, view=TicketView())

bot.run(os.environ.get('DISCORD_TOKEN'))
