import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# הגדרות - תבדוק שה-ID האלה נכונים אצלך!
ROLE_ADD_ID = 1449415392425410662    # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # רול Unverified

intents = discord.Intents.default()
intents.members = True

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role_to_add = interaction.guild.get_role(ROLE_ADD_ID)
        role_to_remove = interaction.guild.get_role(ROLE_REMOVE_ID)
        
        try:
            await interaction.user.add_roles(role_to_add)
            if role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
            await interaction.response.send_message("אומתת בהצלחה!", ephemeral=True)
        except:
            await interaction.response.send_message("שגיאה: וודא שהרול של הבוט נמצא מעל האחרים בהגדרות השרת.", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        self.add_view(VerifyView())

bot = MyBot()

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="אימות שרת", description="לחצו למטה", color=0x00ff00)
    await ctx.send(embed=embed, view=VerifyView())

bot.run(os.environ.get('DISCORD_TOKEN'))
