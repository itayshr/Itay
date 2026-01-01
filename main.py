import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
import asyncio

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    
ROLE_REMOVE_ID = 1449424721862201414 
WELCOME_CHANNEL_ID = 1449406834032250931 
TICKET_CATEGORY_ID = 1449393406529769533  # החלף ב-ID של הקטגוריה לטיקטים
STAFF_ROLE_ID = 1449226054022594560       # החלף ב-ID של רול הצוות

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

# --- כפתור לסגירת טיקט ---
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="סגור טיקט 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("הערוץ יימחק בעוד 5 שניות...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- תפריט בחירת קטגוריה לטיקט ---
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="❓", description="פתיחת פנייה לשאלה כללית"),
            discord.SelectOption(label="תרומה", emoji="💰", description="פתיחת פנייה בנושא תרומות"),
            discord.SelectOption(label="דיווח על שחקן", emoji="🤷‍♂️", description="דיווח על שחקן שעבר על החוקים"),
            discord.SelectOption(label="דיווח על חבר צוות", emoji="💂‍♂️", description="דיווח על התנהלות צוות"),
            discord.SelectOption(label="ערעור על ענישה", emoji="❌", description="ערעור על באן או קיק")
        ]
        super().__init__(placeholder="בחר קטגוריה לטיקט...", min_values=1, max_values=1, options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category_name = self.values[0]

        # יצירת שם ערוץ תקין
        channel_name = f"{category_name}-{user.name}".lower().replace(" ", "-")
        
        # הרשאות
        staff_role = guild.get_role(STAFF_ROLE_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category)

        await interaction.response.send_message(f"הטיקט שלך נפתח ב- {channel.mention}", ephemeral=True)

        embed = discord.Embed(
            title=f"טיקט בנושא: {category_name}",
            description=f"שלום {user.mention},\nצוות השרת יתפנה אליך בהקדם.\nלסגירת הטיקט לחץ על הכפתור למטה.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=CloseTicketView())

# --- View שמכיל את התפריט ---
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

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
            await interaction.response.send_message("שגיאה במתן רול.", ephemeral=True)

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
    # הודעת אימות
    v_embed = discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל גישה לשרת", color=0x00ff00)
    await ctx.send(embed=v_embed, view=VerifyView())
    
    # הודעת טיקטים עם התפריט
    t_embed = discord.Embed(
        title="מערכת תמיכה",
        description="זקוקים לעזרה? בחרו את הקטגוריה המתאימה מהתפריט למטה.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=t_embed, view=TicketView())

bot.run(os.environ.get('DISCORD_TOKEN'))
