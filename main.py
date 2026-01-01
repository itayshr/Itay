import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # רול Unverified (שהוספנו עכשיו)
WELCOME_CHANNEL_ID = 1449406834032250931 
TICKET_CATEGORY_ID = 1456352365295829133 # הקטגוריה שבה ייפתח הטיקט

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

# --- מערכת טיקט פשוטה ---
class SimpleTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="פתח טיקט 🎫", style=discord.ButtonStyle.blurple, custom_id="just_open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        
        if not category:
            return await interaction.followup.send("שגיאה: קטגוריית הטיקטים לא נמצאה.", ephemeral=True)

        try:
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
                title="טיקט חדש",
                description=f"שלום {interaction.user.mention},\nתודה שפנית לצוות השרת. נא לכתוב את פנייתך כאן.",
                color=0x5865f2
            )
            await ticket_channel.send(content=f"{interaction.user.mention} | @here", embed=embed)
            await interaction.followup.send(f"הטיקט נפתח כאן: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send("שגיאה ביצירת הטיקט. וודא שלבוט יש הרשאות ניהול.", ephemeral=True)

# --- מערכת אימות (כולל הסרת רול) ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_with_remove")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role_to_add = interaction.guild.get_role(ROLE_ADD_ID)
        role_to_remove = interaction.guild.get_role(ROLE_REMOVE_ID)
        
        try:
            # הוספת רול אזרח
            if role_to_add:
                await interaction.user.add_roles(role_to_add)
            
            # הסרת רול Unverified (אם הוא קיים אצל המשתמש)
            if role_to_remove and role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
                
            await interaction.response.send_message("אומתת בהצלחה! הרול הישן הוסר.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("שגיאה: וודא שהרול של הבוט נמצא מעל הרולים שהוא מנהל.", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        self.add_view(VerifyView())
        self.add_view(SimpleTicketView())
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        count = len(member.guild.members)
        embed = discord.Embed(
            title=f"{member.name} - Welcome",
            description=f"Hey {member.mention}, Welcome to **{member.guild.name}**! We're **{count}** members now.",
            color=0x7289da
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(title="פתיחת טיקט", description="לחצו למטה לפתיחת פנייה", color=0x5865f2)
    await ctx.send(embed=embed, view=SimpleTicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(title="אימות שרת", description="לחצו על הכפתור למטה כדי לקבל גישה", color=0x00ff00)
    await ctx.send(embed=embed, view=VerifyView())

bot.run(os.environ.get('DISCORD_TOKEN'))
