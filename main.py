import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # רול Unverified
WELCOME_CHANNEL_ID = 1449406834032250931 # ה-ID החדש ששלחת

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

# --- מערכת כפתור האימות ---
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

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        self.add_view(VerifyView())
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

# --- מערכת הודעת ברוכים הבאים (Embed) ---
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

# --- פקודה ליצירת הודעת האימות ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל גישה לשרת", color=0x00ff00)
    await ctx.send(embed=embed, view=VerifyView())

bot.run(os.environ.get('DISCORD_TOKEN'))
