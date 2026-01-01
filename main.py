import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    
WELCOME_CHANNEL_ID = 1449406834032250931 
TICKET_CATEGORY_ID = 1456352365295829133 # הקטגוריה שבה ייפתח הטיקט

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

# --- מערכת טיקטים פשוטה (רק כפתור) ---
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="פתח טיקט 🎫", style=discord.ButtonStyle.blurple, custom_id="simple_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        # אישור ראשוני כדי למנוע Failed
        await interaction.response.defer(ephemeral=True)

        try:
            # יצירת חדר פרטי
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=category,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True),
                    guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
                }
            )
            
            embed = discord.Embed(
                title="טיקט חדש",
                description=f"שלום {interaction.user.mention},\nתודה שפנית לצוות השרת. נא לכתוב את פנייתך כאן.",
                color=0x5865f2
            )
            await ticket_channel.send(content=f"{interaction.user.mention} | @here", embed=embed)
            await interaction.followup.send(f"הטיקט נפתח כאן: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send("שגיאה: וודא שלבוט יש הרשאת 'Manage Channels'.", ephemeral=True)

# --- מערכת אימות ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_simple")
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
        embed = discord.Embed(title=f"ברוך הבא {member.name}", description="שמחים שהצטרפת!", color=0x7289da)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(title="פתיחת טיקט", description="לחצו על הכפתור למטה כדי לפתוח פנייה לצוות.", color=0x5865f2)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.send(embed=discord.Embed(title="אימות", description="לחצו לאימות", color=0x00ff00), view=VerifyView())

bot.run(os.environ.get('DISCORD_TOKEN'))
