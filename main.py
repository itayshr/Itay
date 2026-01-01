import discord
from discord.ext import commands, tasks
import requests
import os
from datetime import datetime

# --- הגדרות ה-ID שלך (וודא שהם נכונים) ---
ROLE_ADD_ID = 1449415392425410662    # רול אזרח
ROLE_REMOVE_ID = 1449424721862201414 # רול Unverified
WELCOME_CHANNEL_ID = 1449406834032250931
STATUS_CHANNEL_ID = 1449406834032250931 # ה-ID של הערוץ שבו יופיע הסטטוס החי

# --- הגדרות שרת FiveM ---
FIVE_M_IP = "26.91.191.60"
FIVE_M_PORT = "30120"
SERVER_URL = f"http://{FIVE_M_IP}:{FIVE_M_PORT}"

intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

# --- מערכת כפתור האימות ---
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
        self.status_message_id = None # שומר את ה-ID כדי לערוך את אותה הודעה

    async def setup_hook(self):
        self.add_view(VerifyView())
        self.live_status.start() # מתחיל את הלופ של הסטטוס החי
        
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

# --- לופ עדכון סטטוס שרת (כל 30 שניות) ---
@tasks.loop(seconds=30)
async def live_status():
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not channel:
        return

    try:
        # משיכת נתונים מה-API של FiveM
        players = requests.get(f"{SERVER_URL}/players.json", timeout=5).json()
        info = requests.get(f"{SERVER_URL}/info.json", timeout=5).json()
        
        online_count = len(players)
        max_clients = info['vars'].get('sv_maxclients', '64')
        
        # בניית רשימת השחקנים כמו בתמונה
        player_list = ""
        for p in players[:10]: # מציג עד 10 שחקנים
            player_list += f"**[ID: {p['id']}] {p['name']}** @undefined\n"
        
        if not player_list:
            player_list = "*אין שחקנים מחוברים כרגע*"

        embed = discord.Embed(
            title="Phantom-Israel | Serious Roleplay V2",
            description=player_list,
            color=0xa435f0 # סגול
        )
        embed.add_field(name="", value=f"🐌 **Status:** `ONLINE`", inline=False)
        embed.add_field(name="", value=f"👤 **Players:** `{online_count}/{max_clients}`", inline=False)
        embed.add_field(name="", value=f"🌟 **Space:** `{int((online_count/int(max_clients))*100)}%`", inline=False)
        embed.add_field(name="", value=f"💼 **IP:** `connect {FIVE_M_IP}`", inline=False)
        
        # כאן תחליף לקישור של הלוגו הסגול שלך
        embed.set_image(url="https://i.imgur.com/uG9Xl9Y.png") 
        embed.set_footer(text=f"Dev:Frozen • Today at {datetime.now().strftime('%H:%M %p')}")

        # יצירת כפתור קטן למטה (כמו בתמונה)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=f"{online_count}/{max_clients}", emoji="🐌", disabled=True))

        # שליחה או עריכה של ההודעה
        async for message in channel.history(limit=10):
            if message.author == bot.user and "Phantom-Israel" in message.embeds[0].title if message.embeds else False:
                await message.edit(embed=embed, view=view)
                return
        
        await channel.send(embed=embed, view=view)

    except Exception as e:
        # אם השרת סגור
        offline_embed = discord.Embed(title="Phantom-Israel | Status", description="🔴 השרת כרגע לא זמין", color=0xff0000)
        async for message in channel.history(limit=5):
            if message.author == bot.user and "Phantom-Israel" in message.embeds[0].title if message.embeds else False:
                await message.edit(embed=offline_embed, view=None)
                return

# --- אירועים ופקודות קיימות ---
@bot.event
async def on_member_join(member):
    initial_role = member.guild.get_role(ROLE_REMOVE_ID)
    if initial_role:
        try: await member.add_roles(initial_role)
        except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(title="אימות שרת", description="לחצו למטה כדי לקבל גישה לשרת", color=0x00ff00)
    await ctx.send(embed=embed, view=VerifyView())

bot.run(os.environ.get('DISCORD_TOKEN'))
