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

# רשימת ה-ID של 4 הרולים של הצוות (תחליף ב-ID האמיתיים שלך)
STAFF_ROLES_IDS = [
    1457032202071314674, # רול צוות 1
    1456711448284631253, # רול צוות 2
    1457036541254828065, # רול צוות 3
    1457029203328368833  # רול צוות 4
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
            if role_to_add:
                await interaction.user.add_roles(role_to_add)
            if role_to_remove and role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
            await interaction.response.send_message("אומתת בהצלחה!", ephemeral=True)
        except:
            await interaction.response.send_message("שגיאה: וודא שהרול של הבוט מעל כולם.", ephemeral=True)

# --- 2. מערכת הטיקטים (Dropdown) ---
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="שאלה כללית", emoji="❓", value="שאלה"),
            discord.SelectOption(label="תרומה", emoji="💰", value="תרומה"),
            discord.SelectOption(label="דיווח על שחקן", emoji="👮", value="דיווח-שחקן"),
            discord.SelectOption(label="דיווח על חבר צוות", emoji="💂", value="דיווח-צוות"),
            discord.SelectOption(label="ערעור על ענישה", emoji="❌", value="ערעור"),
        ]
        super().__init__(placeholder="בחר קטגוריה...", min_values=1, max_values=1, options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category_value = self.values[0]
        clean_user_name = user.name.lower().replace(" ", "-")
        ticket_name = f"{category_value}-{clean_user_name}"

        for ch in guild.text_channels:
            if clean_user_name in ch.name and "-" in ch.name:
                return await interaction.response.send_message(f"כבר יש לך פנייה פתוחה: {ch.mention}", ephemeral=True)

        # הגדרת הרשאות בסיסיות (משתמש + הבוט עצמו)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # לולאה שמוסיפה את כל 4 רולי הצוות להרשאות הערוץ
        for role_id in STAFF_ROLES_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True)

        # הוספת אדמינים (ליתר ביטחון)
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(ticket_name, overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"פנייה חדשה: {category_value}",
            description=f"שלום {user.mention}, צוות התמיכה יעזור לך בהקדם.\n\n**לצוות:** לסגירת הטיקט הקלידו `!close`.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)
        await interaction.response.edit_message(view=TicketSystemView())

class TicketSystemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# --- 3. הגדרות הבוט הראשיות ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())
        self.add_view(TicketSystemView())

    async def on_ready(self):
        print(f'Logged in as {self.user.name} - System Integrated')

bot = MyBot()

@bot.command()
async def close(ctx):
    # בדיקה אם למשתמש יש את אחד מרולי הצוות או שהוא אדמין
    user_roles_ids = [role.id for role in ctx.author.roles]
    is_staff = any(role_id in user_roles_ids for role_id in STAFF_ROLES_IDS)
    is_admin = ctx.author.guild_permissions.administrator

    if not (is_admin or is_staff):
        return await ctx.send("רק צוות מורשה או אדמין יכולים לסגור טיקטים!", delete_after=5)
    
    if "-" not in ctx.channel.name:
        return await ctx.send("זהו אינו ערוץ טיקט!", delete_after=5)

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(title="🎫 טיקט נסגר", color=discord.Color.red(), timestamp=datetime.now())
        log_embed.add_field(name="נסגר על ידי:", value=ctx.author.mention)
        log_embed.add_field(name="שם הערוץ:", value=ctx.channel.name)
        await log_channel.send(embed=log_embed)

    await ctx.send(f"הטיקט נסגר על ידי {ctx.author.mention}. מוחק בעוד 5 שניות...")
    await asyncio.sleep(5)
    await ctx.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל גישה לשרת", color=0x00ff00)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(title="מערכת טיקטים", description="בחר קטגוריה לפתיחת פנייה", color=0x000000)
    await ctx.send(embed=embed, view=TicketSystemView())

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("ERROR: No token found!")