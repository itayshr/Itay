import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# הגדרות - תבדוק שה-ID האלה נכונים אצלך!
ROLE_ADD_ID = 1449415392425410662    # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # רול Unverified

# כאן היה חסר התיקון!
intents = discord.Intents.default()
intents.members = True
intents.message_content = True # השורה הזו מאפשרת לבוט לקרוא את הפקודה !setup

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
                await interaction.response.send_message("שגיאה: רול אזרח לא נמצא. וודא שה-ID נכון.", ephemeral=True)
                return

            await interaction.user.add_roles(role_to_add)
            if role_to_remove and role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
            await interaction.response.send_message("אומתת בהצלחה!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("שגיאה: לבוט אין הרשאות לנהל רולים. גרור את הרול שלו לראש הרשימה!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"שגיאה לא צפויה: {e}", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        # הגדרת פקודת prefix
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self):
        # גורם לכפתור להמשיך לעבוד גם אחרי שהבוט עושה ריסטארט
        self.add_view(VerifyView())

    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True) # רק מנהל יכול להריץ את זה
async def setup(ctx):
    embed = discord.Embed(
        title="אימות שרת", 
        description="ברוכים הבאים! לחצו על הכפתור למטה כדי לקבל גישה לשרת.", 
        color=0x00ff00
    )
    await ctx.send(embed=embed, view=VerifyView())

bot.run(os.environ.get('DISCORD_TOKEN'))
