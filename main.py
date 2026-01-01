import discord
from discord.ext import commands, tasks
import requests
import os
from datetime import datetime

# --- הגדרות ה-ID שלך ---
ROLE_ADD_ID = 1449415392425410662    
ROLE_REMOVE_ID = 1449424721862201414 
STATUS_CHANNEL_ID = 1455594347990089912 # הערוץ שבו הסטטוס יופיע

# --- הגדרות שרת FiveM ---
FIVE_M_IP = "26.91.191.60"
FIVE_M_PORT = "30120"
SERVER_URL = f"http://{FIVE_M_IP}:{FIVE_M_PORT}"

intents = discord.Intents.all()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.update_live_status.start() # מפעיל את הלופ האוטומטי
        
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')

bot = MyBot()

# פונקציה ליצירת ה-Embed (כדי שלא נשכפל קוד)
async def create_status_embed():
    try:
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
        
        # תמונה מהתמונה ששלחת (תחליף לקישור שלך אם יש לך)
        embed.set_image(url="https://i.imgur.com/uG9Xl9Y.png") 
        embed.set_footer(text=f"Dev:Frozen • Today at {datetime.now().strftime('%H:%M %p')}")
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=f"{online_count}/{max_clients}", emoji="🐌", disabled=True))
        
        return embed, view
    except:
        embed = discord.Embed(title="Phantom-Israel | Status", description="🔴 השרת כרגע לא זמין (OFFLINE)", color=0xff0000)
        return embed, None

# לופ שמעדכן את ההודעה כל 30 שניות
@tasks.loop(seconds=30)
async def update_live_status():
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not channel: return

    embed, view = await create_status_embed()

    async for message in channel.history(limit=20):
        if message.author == bot.user and message.embeds and "Phantom-Israel" in message.embeds[0].title:
            await message.edit(embed=embed, view=view)
            return

# פקודה ידנית לשליחת ההודעה בפעם הראשונה
@bot.command()
@commands.has_permissions(administrator=True)
async def sendstatus(ctx):
    embed, view = await create_status_embed()
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete() # מוחק את הפקודה שלך כדי שהערוץ יהיה נקי

# פקודת ה-Setup לאימות (Verify)
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    # כאן הקוד של ה-VerifyView שכתבנו קודם
    pass

bot.run(os.environ.get('DISCORD_TOKEN'))
