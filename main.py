import discord
from discord.ext import commands
from discord.ui import Button, View
import os

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    
ROLE_REMOVE_ID = 1449424721862201414 
WELCOME_CHANNEL_ID = 1449406834032250931  

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

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

# --- פקודה חדשה: יצירת סטטוס כמו בתמונה ---
@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx):
    # יצירת ה-Embed הראשי
    embed = discord.Embed(
        title="Phantom-Israel | Serious\nRoleplay V2 | RolePlay - V3",
        color=0xa435f0 # צבע סגול שתואם לתמונה
    )

    # הוספת השדות עם האייקונים מהתמונה
    embed.add_field(name="", value="🐌 **Status:** `ONLINE`", inline=False)
    embed.add_field(name="", value="👤 **Players:** `2/4`", inline=False)
    embed.add_field(name="", value="🌟 **Space:** `50%`", inline=False)
    embed.add_field(name="", value="💼 **IP:** `connect 88.214.55.68`", inline=False)

    # שמות השחקנים (כפי שמופיע בתמונה)
    embed.description = "**[ID: 1] ben14583' @undefined**\n**[ID: 2] papoch @undefined**"

    # תמונה ראשית (הלוגו הגדול עם המסכה)
    embed.set_image(url="https://i.imgur.com/uG9Xl9Y.png") # כאן כדאי להעלות את התמונה שלך לקישור ישיר
    
    # תמונה קטנה בצד (Thumbnail)
    embed.set_thumbnail(url="https://i.imgur.com/uG9Xl9Y.png")

    # פוטר (Footer)
    embed.set_footer(text=f"Dev:Frozen • Today at {discord.utils.utcnow().strftime('%H:%M %p')}")

    # הוספת הכפתור הקטן למטה (כמו ב-Reaction בתמונה)
    view = View()
    status_button = Button(label="2/4", emoji="🐌", style=discord.ButtonStyle.blurple, disabled=True)
    view.add_item(status_button)

    await ctx.send(embed=embed, view=view)

# --- שאר הפונקציות הקיימות שלך (on_member_join, setup) ---
@bot.event
async def on_member_join(member):
    initial_role = member.guild.get_role(ROLE_REMOVE_ID)
    if initial_role:
        try: await member.add_roles(initial_role)
        except: pass

    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=f"{member.name} - Welcome", description=f"Hey {member.mention}, Welcome!", color=0x7289da)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל גישה לשרת", color=0x00ff00)
    await ctx.send(embed=embed, view=VerifyView())

bot.run(os.environ.get('DISCORD_TOKEN'))
