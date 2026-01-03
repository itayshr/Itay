import discord
from discord.ext import commands
from discord.ui import View, Select
import asyncio
import os
from datetime import datetime

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    # רול אזרח (יינתן אוטומטית בכניסה)
WELCOME_CHANNEL_ID = 1449406834032250931
LOG_CHANNEL_ID = 1456694146583498792  

# מילון רולי הצוות והקידומת שלהם
STAFF_ROLES = {
    1457032202071314674: "SA",
    1456711448284631253: "AD",
    1457036541254828065: "MOD",
    1457029203328368833: "HP"
}

STAFF_ROLES_IDS = list(STAFF_ROLES.keys())

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# --- פונקציה עזר לעדכון שם (לשימוש חוזר) ---
async def update_member_nickname(member):
    prefix = ""
    # עוברים על הרולים של המשתמש ובודקים אם אחד מהם נמצא במילון הצוות
    for role in member.roles:
        if role.id in STAFF_ROLES:
            prefix = f"{STAFF_ROLES[role.id]} | "
            break 
    
    new_nickname = f"{prefix}{member.name}"
    
    # משנה רק אם השם שונה מהנוכחי וזה לא ה-Owner
    if member.display_name != new_nickname:
        try:
            await member.edit(nick=new_nickname[:32])
        except discord.Forbidden:
            pass # אין הרשאה לשנות שם (למשל אדמין גבוה יותר)

# --- הגדרות הבוט ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(TicketSystemView())

    async def on_ready(self):
        print(f'Logged in as {self.user.name} - Auto Nickname Active')

bot = MyBot()

# --- אירועים (Events) ---

@bot.event
async def on_member_join(member):
    # 1. מתן רול אזרח אוטומטי (בלי אימות)
    role = member.guild.get_role(ROLE_ADD_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass

    # 2. עדכון שם ראשוני אם הוא איש צוות
    await update_member_nickname(member)
    
    # 3. הודעת ברוך הבא
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        count = len(member.guild.members)
        embed = discord.Embed(title=f"ברוכים הבאים!", description=f"היי {member.mention}, ברוך הבא לשרת! אתה החבר ה-{count}.", color=0x7289da)
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    # בכל פעם שמישהו כותב הודעה, הבוט מוודא שהשם שלו תקין לפי הרול
    if message.author.bot or not message.guild:
        return
    
    await update_member_nickname(message.author)
    await bot.process_commands(message)

# --- מערכת הטיקטים (Dropdown) ---
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
        clean_user_name = user.name.lower().replace(" ", "-")
        ticket_name = f"{self.values[0]}-{clean_user_name}"

        for ch in guild.text_channels:
            if clean_user_name in ch.name and "-" in ch.name:
                return await interaction.response.send_message(f"כבר יש לך פנייה פתוחה!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for r_id in STAFF_ROLES_IDS:
            role = guild.get_role(r_id)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(ticket_name, overwrites=overwrites)
        await channel.send(embed=discord.Embed(title="פנייה חדשה", description=f"שלום {user.mention}, הצוות יענה בהקדם.", color=discord.Color.blue()))
        await interaction.response.edit_message(view=TicketSystemView())

class TicketSystemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# --- פקודות ---
@bot.command()
async def close(ctx):
    user_roles_ids = [role.id for role in ctx.author.roles]
    is_staff = any(role_id in user_roles_ids for role_id in STAFF_ROLES_IDS)
    if not (ctx.author.guild_permissions.administrator or is_staff):
        return await ctx.send("אין לך הרשאה!")
    
    await ctx.send("הערוץ יימחק בעוד 5 שניות...")
    await asyncio.sleep(5)
    await ctx.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    await ctx.send(embed=discord.Embed(title="מערכת טיקטים", description="פתחו פנייה כאן", color=0x000000), view=TicketSystemView())

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
