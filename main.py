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

# --- 1. מערכת כפתור האימות ושינוי השם ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me")
    async def verify(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        guild = interaction.guild
        role_to_add = guild.get_role(ROLE_ADD_ID)
        role_to_remove = guild.get_role(ROLE_REMOVE_ID)
        
        try:
            # הוספת רול אזרח והסרת לא מאומת
            if role_to_add: await user.add_roles(role_to_add)
            if role_to_remove and role_to_remove in user.roles:
                await user.remove_roles(role_to_remove)

            # בדיקה אם למשתמש יש רול צוות וקביעת קידומת
            prefix = ""
            # עוברים על הרולים של המשתמש ובודקים אם אחד מהם נמצא במילון הצוות
            for role in user.roles:
                if role.id in STAFF_ROLES:
                    prefix = f"{STAFF_ROLES[role.id]} | "
                    break # מפסיק ברול הראשון שהוא מוצא (הגבוה ביותר)

            # שינוי הכינוי בשרת
            new_nickname = f"{prefix}{user.name}"
            
            # בדיקה אם הכינוי הנוכחי כבר תקין כדי לא להעמיס על ה-API
            if user.display_name != new_nickname:
                try:
                    await user.edit(nick=new_nickname[:32]) # הגבלה ל-32 תווים של דיסקורד
                except discord.Forbidden:
                    print(f"אין הרשאה לשנות שם ל-{user.name}")

            await interaction.response.send_message(f"אומתת בהצלחה! השם שלך עודכן ל: **{new_nickname}**", ephemeral=True)
            
        except Exception as e:
            print(f"Error in verify: {e}")
            await interaction.response.send_message("קרתה שגיאה בתהליך האימות.", ephemeral=True)

# --- 2. מערכת הטיקטים (נשאר ללא שינוי בשמות הערוצים) ---
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

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for role_id in STAFF_ROLES_IDS:
            role = guild.get_role(role_id)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(ticket_name, overwrites=overwrites)
        embed = discord.Embed(title=f"פנייה חדשה: {category_value}", description=f"שלום {user.mention}, צוות התמיכה יעזור לך בהקדם.", color=discord.Color.blue())
        await channel.send(embed=embed)
        await interaction.response.edit_message(view=TicketSystemView())

class TicketSystemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

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
    user_roles_ids = [role.id for role in ctx.author.roles]
    is_staff = any(role_id in user_roles_ids for role_id in STAFF_ROLES_IDS)
    if not (ctx.author.guild_permissions.administrator or is_staff):
        return await ctx.send("אין לך הרשאה!", delete_after=5)
    
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title="🎫 טיקט נסגר", color=discord.Color.red())
        embed.add_field(name="על ידי:", value=ctx.author.name)
        await log_channel.send(embed=embed)
    await ctx.send("הערוץ יימחק בעוד 5 שניות...")
    await asyncio.sleep(5)
    await ctx.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.send(embed=discord.Embed(title="אימות", description="לחצו למטה לאימות", color=0x00ff00), view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    await ctx.send(embed=discord.Embed(title="טיקטים", description="פתחו פנייה כאן", color=0x000000), view=TicketSystemView())

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
