import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import asyncio
from datetime import datetime

# --- הגדרות ה-ID שלך (תחליף ב-ID האמיתי שלך) ---
ROLE_ADD_ID = 1449415392425410662  # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414  # רול Unverified
WELCOME_CHANNEL_ID = 1449406834032250931
LOG_CHANNEL_ID = 1456694146583498792  # ערוץ לוגים של טיקטים

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
            await interaction.user.add_roles(role_to_add)
            if role_to_remove and role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
            await interaction.response.send_message("אומתת בהצלחה!", ephemeral=True)
        except:
            await interaction.response.send_message("שגיאה: וודא שהרול של הבוט מעל כולם בהגדרות השרת.", ephemeral=True)


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
        super().__init__(placeholder="בחר קטגוריה...", min_values=1, max_values=1, options=options,
                         custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category_value = self.values[0]

        clean_user_name = user.name.lower().replace(" ", "-")
        ticket_name = f"{category_value}-{clean_user_name}"

        # בדיקה אם כבר יש טיקט פתוח
        for ch in guild.text_channels:
            if clean_user_name in ch.name and "-" in ch.name:
                return await interaction.response.send_message(f"כבר יש לך פנייה פתוחה: {ch.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(ticket_name, overwrites=overwrites)

        embed = discord.Embed(
            title=f"פנייה חדשה: {category_value}",
            description=f"שלום {user.mention}, צוות התמיכה יעזור לך בהקדם.\n\n**למנהלים:** לסגירת הטיקט הקלידו `!close`.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)

        # איפוס התפריט ושליחת אישור
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
        # טעינה של כל ה-Views כדי שיעבדו אחרי ריסטארט
        self.add_view(VerifyView())
        self.add_view(TicketSystemView())

    async def on_ready(self):
        print(f'Logged in as {self.user.name} - System Integrated')


bot = MyBot()


# --- 4. אירוע כניסת משתמש ---
@bot.event
async def on_member_join(member):
    initial_role = member.guild.get_role(ROLE_REMOVE_ID)
    if initial_role:
        try:
            await member.add_roles(initial_role)
        except:
            pass

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


# --- 5. פקודת סגירת טיקט (כולל לוגים) ---
@bot.command()
async def close(ctx):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("רק אדמין יכול לסגור טיקטים!", delete_after=5)

    if "-" not in ctx.channel.name:  # בדיקה בסיסית שזה ערוץ טיקט
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


# --- 6. פקודות Setup ---
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


