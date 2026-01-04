import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import asyncio
import os
from datetime import datetime

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # רול Unverified
WELCOME_CHANNEL_ID = 1449406834032250931
LOG_CHANNEL_ID = 1456694146583498792  

STAFF_ROLES_IDS = [
    1457032202071314674,
    1456711448284631253,
    1457036541254828065,
    1457029203328368833
]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# --- 1. מערכת כפתור האימות ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role_to_add = interaction.guild.get_role(ROLE_ADD_ID)
        role_to_remove = interaction.guild.get_role(ROLE_REMOVE_ID)
        
        try:
            # בדיקה אם הרולים קיימים בשרת
            if not role_to_add:
                return await interaction.response.send_message("שגיאה: רול האימות לא נמצא בשרת.", ephemeral=True)

            # הוספת רול אזרח
            await interaction.user.add_roles(role_to_add)
            
            # הסרת רול Unverified אם קיים
            if role_to_remove and role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
            
            await interaction.response.send_message("אומתת בהצלחה! ברוך הבא לשרת. 🎉", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("שגיאה: אין לבוט הרשאות לנהל רולים. וודא שהרול של הבוט מעל הרולים שהוא מנסה לתת.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"קרתה שגיאה לא צפויה: {e}", ephemeral=True)

# --- 2. מערכת הטיקטים ---
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="❓", value="שאלה"),
            discord.SelectOption(label="תרומה", emoji="💰", value="תרומה"),
            discord.SelectOption(label="דיווח על שחקן", emoji="👮", value="דיווח-שחקן"),
            discord.SelectOption(label="דיווח על חבר צוות", emoji="💂", value="דיווח-צוות"),
            discord.SelectOption(label="ערעור על ענישה", emoji="❌", value="ערעור"),
        ]
        super().__init__(placeholder="בחר קטגוריה לפתיחת טיקט...", min_values=1, max_values=1, options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category_value = self.values[0]
        
        # בדיקה אם כבר יש למשתמש טיקט פתוח
        ticket_prefix = f"{category_value.lower()}-"
        existing_ticket = discord.utils.get(guild.text_channels, name=f"{ticket_prefix}{user.name.lower()}".replace(" ", "-"))
        
        if existing_ticket:
            return await interaction.response.send_message(f"כבר יש לך פנייה פתוחה בנושא זה: {existing_ticket.mention}", ephemeral=True)

        await interaction.response.defer(ephemeral=True) # מונע מהאינטראקציה לפוג בזמן יצירת הערוץ

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        for role_id in STAFF_ROLES_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True)

        ticket_channel = await guild.create_text_channel(
            name=f"{category_value}-{user.name}",
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title=f"טיקט חדש - {category_value}",
            description=f"שלום {user.mention},\nתודה שפנית אלינו. צוות התמיכה קיבל הודעה ויגיע בהקדם.\n\n**לסגירת הטיקט:** השתמשו בפקודה `!close`.",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="מערכת הטיקטים הרשמית")
        
        await ticket_channel.send(embed=embed)
        await interaction.followup.send(f"הטיקט שלך נוצר בהצלחה: {ticket_channel.mention}", ephemeral=True)

class TicketSystemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# --- 3. הגדרות הבוט ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())
        self.add_view(TicketSystemView())

    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

@bot.command()
async def close(ctx):
    is_staff = any(role.id in STAFF_ROLES_IDS for role in ctx.author.roles)
    is_admin = ctx.author.guild_permissions.administrator

    if not (is_admin or is_staff):
        return await ctx.send("רק צוות או מנהלים יכולים לסגור טיקטים.", delete_after=5)

    # לוג סגירה
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(title="🎫 טיקט נסגר", color=discord.Color.red(), timestamp=datetime.now())
        log_embed.add_field(name="ערוץ:", value=ctx.channel.name)
        log_embed.add_field(name="נסגר על ידי:", value=ctx.author.name)
        await log_channel.send(embed=log_embed)

    await ctx.send("הערוץ יימחק בעוד 5 שניות...")
    await asyncio.sleep(5)
    await ctx.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(title="אימות שחקנים", description="לחצו על הכפתור למטה כדי לקבל גישה לשרת.", color=discord.Color.green())
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(title="מרכז פניות ותמיכה", description="יש לכם בעיה? רוצים לדווח? בחרו את הקטגוריה המתאימה.", color=discord.Color.blue())
    await ctx.send(embed=embed, view=TicketSystemView())

if __name__ == "__main__":
    bot.run("YOUR_TOKEN_HERE")
