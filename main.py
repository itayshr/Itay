import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # רול Unverified
WELCOME_CHANNEL_ID = 1449406834032250931 # ערוץ ברוכים הבאים
TICKET_CATEGORY_ID = 1449393406529769533 # (אופציונלי) ID של קטגוריה לטיקטים

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

# --- מערכת אימות ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role_to_add = interaction.guild.get_role(ROLE_ADD_ID)
        role_to_remove = interaction.guild.get_role(ROLE_REMOVE_ID)
        
        try:
            await interaction.user.add_roles(role_to_add)
            if role_to_remove and role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
            await interaction.response.send_message("אומתת בהצלחה!", ephemeral=True)
        except:
            await interaction.response.send_message("שגיאה: וודא שהרול של הבוט מעל כולם.", ephemeral=True)

# --- מערכת טיקטים ---
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="סגור טיקט 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("הערוץ ייסגר בעוד 5 שניות...")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=5))
        await interaction.channel.delete()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="פתח פנייה לצוות 📩", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        
        # בדיקה אם כבר יש למשתמש טיקט פתוח (למניעת ספאם)
        existing_channel = discord.utils.get(guild.channels, name=f"ticket-{user.name.lower()}")
        if existing_channel:
            return await interaction.response.send_message(f"כבר יש לך טיקט פתוח כאן: {existing_channel.mention}", ephemeral=True)

        # הגדרות הרשאות לערוץ הטיקט
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category=category
        )

        embed = discord.Embed(
            title="פנייה חדשה",
            description=f"שלום {user.mention},\nצוות השרת יתפנה אליך בהקדם.\nלחץ על הכפתור למטה כדי לסגור את הטיקט.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"הטיקט שלך נפתח ב- {channel.mention}", ephemeral=True)

# --- הגדרות הבוט ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # גורם לכפתורים לעבוד גם אחרי שהבוט עובר ריסטארט
        self.add_view(VerifyView())
        self.add_view(TicketView())
        self.add_view(CloseTicketView())

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
        embed.set_footer(text=f"Dev: {bot.user.name} • Today at {discord.utils.utcnow().strftime('%H:%M')}")
        await channel.send(embed=embed)

# --- פקודת Setup מאוחדת ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    # הודעת אימות
    verify_embed = discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל גישה לשרת", color=0x00ff00)
    await ctx.send(embed=verify_embed, view=VerifyView())

    # הודעת טיקטים
    ticket_embed = discord.Embed(
        title="מערכת תמיכה",
        description="זקוקים לעזרה? פתחו טיקט וצוות השרת יעזור לכם.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=ticket_embed, view=TicketView())

bot.run(os.environ.get('DISCORD_TOKEN'))
