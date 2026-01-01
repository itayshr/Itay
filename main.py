import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# --- הגדרות - שנה רק את ה-ID כאן! ---
ROLE_ADD_ID = 1449415392425410662    # ID של רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # ID של רול Unverified
WELCOME_CHANNEL_ID = 1234567890      # <--- שים כאן את ה-ID של ערוץ הברוכים הבאים שלך!

# הגדרת הרשאות (Intents)
intents = discord.Intents.default()
intents.members = True          # חובה בשביל ברוכים הבאים ורולים
intents.message_content = True  # חובה בשביל פקודת !setup

# --- מחלקת הכפתור לאימות ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None) # גורם לכפתור לעבוד תמיד

    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role_to_add = interaction.guild.get_role(ROLE_ADD_ID)
        role_to_remove = interaction.guild.get_role(ROLE_REMOVE_ID)
        
        try:
            await interaction.user.add_roles(role_to_add)
            if role_to_remove and role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
            await interaction.response.send_message("אומתת בהצלחה! תהנה בשרת.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("שגיאה: לבוט אין הרשאה. וודא שהרול שלו מעל כולם!", ephemeral=True)
        except Exception:
            await interaction.response.send_message("קרתה שגיאה לא צפויה בתהליך האימות.", ephemeral=True)

# --- הגדרת הבוט ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # מחבר מחדש את הכפתור בזיכרון בכל הפעלה
        self.add_view(VerifyView())

    async def on_ready(self):
        print(f'Logged in as {self.user.name} | Systems: Verify & Welcome Active')

bot = MyBot()

# --- אירוע ברוכים הבאים ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        count = len(member.guild.members)
        embed = discord.Embed(
            title=f"{member.name} - Welcome",
            description=f"Hey {member.mention}, Welcome to **{member.guild.name}**! We're **{count}** members now.",
            color=0x7289da # צבע כחול
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Dev: {bot.user.name} • Today at {discord.utils.utcnow().strftime('%H:%M')}")
        await channel.send(embed=embed)

# --- פקודת Setup לאימות ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="אימות שרת", 
        description="ברוכים הבאים לשרת! \nכדי לקבל גישה לערוצים, לחצו על הכפתור הירוק למטה.", 
        color=0x00ff00
    )
    await ctx.send(embed=embed, view=VerifyView())

# הרצת הבוט עם הטוקן מ-Railway
bot.run(os.environ.get('DISCORD_TOKEN'))
