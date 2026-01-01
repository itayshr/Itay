import discord
from discord.ext import commands, tasks
import requests
import os
from datetime import datetime

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    
ROLE_REMOVE_ID = 1449424721862201414 
STATUS_CHANNEL_ID = 1449406834032250931 

# --- הגדרות שרת FiveM ---
FIVE_M_IP = "93.172.237.169"
FIVE_M_PORT = "30120"
SERVER_URL = f"http://{FIVE_M_IP}:{FIVE_M_PORT}"

intents = discord.Intents.all()

# --- מערכת כפתור האימות (נשמר מהקוד הקודם) ---
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ לאימות ✅", style=discord.ButtonStyle.green, custom_id="verify_me")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_to_add = interaction.guild.get_role(ROLE_ADD_ID)
        role_to_remove = interaction.guild.get_role(ROLE_REMOVE_ID)
        try:
            await interaction.user.add_roles(role_to_add)
            if role_to_remove and role_to_remove in interaction.user.roles:
                await interaction.user.remove_roles(role_to_remove)
            await interaction.response.send_message("אומתת בהצלחה!", ephemeral=True)
        except:
            await interaction.response.send_message("שגיאה: וודא שהרול של הבוט מעל כולם.", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # הוספת כפתור האימות שיישאר פעיל גם אחרי ריסטארט
        self.add_view(VerifyView())
        # הפעלת הלופ של הסטטוס
        self.status_updater.start()
        
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

    # לופ שרץ כל 30 שניות ומעדכן את הסטטוס
    @tasks.loop(seconds=30)
    async def status_updater(self):
        channel = self.get_channel(STATUS_CHANNEL_ID)
        if not channel:
            return

        embed, view = await self.create_status_content()

        # מחפש הודעה קיימת של הבוט כדי לערוך אותה
        async for message in channel.history(limit=20):
            if message.author == self.user and message.embeds and "Phantom-Israel" in message.embeds[0].title:
                await message.edit(embed=embed, view=view)
                return

    async def create_status_content(self):
        try:
            # ניסיון משיכת נתונים משרת ה-FiveM
            players = requests.get(f"{SERVER_URL}/players.json", timeout=5).json()
            info = requests.get(f"{SERVER_URL}/info.json", timeout=5).json()
            
            online_count = len(players)
            max_clients = info['vars'].get('sv_maxclients', '64')
            
            player_list = ""
            for p in players[:10]:
                player_list += f"**[ID: {p['id']}] {p['name']}** @undefined\n"
            
            if not player_list:
                player_list = "*אין שחקנים מחוברים כרגע*"

            embed = discord.Embed(
                title="Phantom-Israel | Serious Roleplay V2",
                description=player_list,
                color=0xa435f0
            )
            embed.add_field(name="", value=f"🐌 **Status:** `ONLINE`", inline=False)
            embed.add_field(name="", value=f"👤 **Players:** `{online_count}/{max_clients}`", inline=False)
            embed.add_field(name="", value=f"🌟 **Space:** `{int((online_count/int(max_clients))*100)}%`", inline=False)
            embed.add_field(name="", value=f"💼 **IP:** `connect {FIVE_M_IP}`", inline=False)
            
            embed.set_image(url="https://i.imgur.com/uG9Xl9Y.png") 
            embed.set_footer(text=f"Dev:Frozen • Today at {datetime.now().strftime('%H:%M %p')}")
            
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label=f"{online_count}/{max_clients}", emoji="🐌", disabled=True))
            
            return embed, view
        except Exception as e:
            # אם השרת לא מגיב (Offline)
            embed = discord.Embed(
                title="Phantom-Israel | Status", 
                description="🔴 **השרת כרגע לא זמין (OFFLINE)**\nאנא נסו להתחבר מאוחר יותר.", 
                color=0xff0000
            )
            embed.set_footer(text=f"Last Check: {datetime.now().strftime('%H:%M %p')}")
            return embed, None

bot = MyBot()

# פקודה ידנית לשליחת ההודעה בפעם הראשונה
@bot.command()
@commands.has_permissions(administrator=True)
async def sendstatus(ctx):
    embed, view = await bot.create_status_content()
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

# פקודת Setup לאימות
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל גישה לשרת", color=0x00ff00)
    await ctx.send(embed=embed, view=VerifyView())

# רול אוטומטי בכניסה
@bot.event
async def on_member_join(member):
    initial_role = member.guild.get_role(ROLE_REMOVE_ID)
    if initial_role:
        try:
            await member.add_roles(initial_role)
        except:
            pass

bot.run(os.environ.get('DISCORD_TOKEN'))
