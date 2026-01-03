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

# --- פונקציית עזר לעדכון שם צוות ---
async def update_staff_nickname(member):
    prefix = ""
    # בודק אם למשתמש יש אחד מרולי הצוות
    for role in member.roles:
        if role.id in STAFF_ROLES:
            prefix = f"{STAFF_ROLES[role.id]} | "
            break 
    
    if prefix:
        new_nickname = f"{prefix}{member.name}"
        # משנה רק אם הכינוי הנוכחי לא תואם וזה לא הבעלים (Owner)
        if member.display_name != new_nickname:
            try:
                await member.edit(nick=new_nickname[:32])
            except discord.Forbidden:
                pass # אין הרשאה (הבוט נמוך יותר בהיררכיה או שזה ה-Owner)

# --- 1. מערכת כפתור האימות (רק נותן רול אזרח) ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me")
    async def verify(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        role_to_add = interaction.guild.get_role(ROLE_ADD_ID)
        role_to_remove = interaction.guild.get_role(ROLE_REMOVE_ID)
        
        try:
            if role_to_add: await user.add_roles(role_to_add)
            if role_to_remove and role_to_remove in user.roles:
                await user.remove_roles(role_to_remove)
            await interaction.response.send_message("אומתת בהצלחה וקיבלת רול אזרח!", ephemeral=True)
        except:
            await interaction.response.send_message("שגיאה במתן הרול.", ephemeral=True)

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

# --- הגדרות הבוט ואירועים ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())
        self.add_view(TicketSystemView())

    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    
    # ברגע שאיש צוות כותב הודעה, הבוט בודק ומתקן לו את השם אם צריך
    await update_staff_nickname(message.author)
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    # רול התחלתי
    initial_role = member.guild.get_role(ROLE_REMOVE_ID)
    if initial_role:
        try: await member.add_roles(initial_role)
        except: pass

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
async def setup_verify(ctx):
    await ctx.send(embed=discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל רול אזרח", color=0x00ff00), view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    await ctx.send(embed=discord.Embed(title="מערכת טיקטים", description="פתחו פנייה כאן", color=0x000000), view=TicketSystemView())

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
