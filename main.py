import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# --- הגדרות ה-ID שלך (תמלא את ה-ID החסר) ---
ROLE_ADD_ID = 1449415392425410662    
ROLE_REMOVE_ID = 1449424721862201414 
WELCOME_CHANNEL_ID = 1449406834032250931 
TICKET_CATEGORY_ID = 123456789012345678  # <--- חשוב: תחליף ב-ID של הקטגוריה שבה ייפתחו הטיקטים
STAFF_ROLE_ID = 123456789012345678       # <--- חשוב: תחליף ב-ID של רול המנהלים/צוות

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

# --- כפתור לסגירת טיקט ---
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="סגור טיקט 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("הערוץ יימחק בעוד 5 שניות...", ephemeral=False)
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- מערכת פתיחת טיקט ---
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="פתח פנייה לצוות 📩", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        
        # בדיקה אם יש כבר טיקט פתוח
        channel_name = f"ticket-{user.name.lower()}".replace(" ", "-")
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        
        if existing_channel:
            return await interaction.response.send_message(f"כבר יש לך טיקט פתוח: {existing_channel.mention}", ephemeral=True)

        # הרשאות לטיקט
        staff_role = guild.get_role(STAFF_ROLE_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # יצירת הערוץ
        category = guild.get_channel(TICKET_CATEGORY_ID)
        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category
            )
            
            await interaction.response.send_message(f"הטיקט נפתח! {channel.mention}", ephemeral=True)
            
            embed = discord.Embed(
                title="פנייה חדשה",
                description=f"שלום {user.mention}, צוות השרת יתפנה אליך בהקדם.\nלסגירת הטיקט לחץ על הכפתור למטה.",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed, view=CloseTicketView())
            
        except Exception as e:
            print(e)
            await interaction.response.send_message("שגיאה ביצירת הטיקט. וודא שלבוט יש הרשאות 'Manage Channels'.", ephemeral=True)

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
            await interaction.response.send_message("שגיאה במתן רול. וודא שהרול של הבוט נמצא מעל הרולים האחרים.", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())
        self.add_view(TicketView())
        self.add_view(CloseTicketView())

    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    # שליחת הודעת אימות
    v_embed = discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל גישה לשרת", color=0x00ff00)
    await ctx.send(embed=v_embed, view=VerifyView())
    
    # שליחת הודעת טיקטים
    t_embed = discord.Embed(title="מערכת תמיכה", description="זקוקים לעזרה? פתחו טיקט וצוות השרת יעזור לכם.", color=discord.Color.blue())
    await ctx.send(embed=t_embed, view=TicketView())

bot.run(os.environ.get('DISCORD_TOKEN'))
