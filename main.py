import os
import json
import time
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import discord

# --- EN SIMPEL WEBSERVER TIL RENDER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("MivBot er i live!".encode('utf-8'))

def run_webserver():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Webserver startede på port {port}")
    server.serve_forever()

# Start webserveren i en separat baggrundstråd
threading.Thread(target=run_webserver, daemon=True).start()
# -------------------------------------

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Hvis du har tilføjet en 'Persistent Disk' på Render på stien /data, 
# så ændr denne variabel til: "/data/miv_stats.json"
DATA_FILE = "miv_stats.json"
miv_history = {}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Kunne ikke gemme data: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    stats = load_data()
    user_id = str(message.author.id)
    username = message.author.name
    
    if user_id not in stats:
        stats[user_id] = {"name": username, "count": 0}
    
    stats[user_id]["name"] = username
    message_lower = message.content.lower().strip()

    if message_lower == "!mivnulstil":
        if username.lower() == "limpkinlee":
            stats = {}
            save_data(stats)
            await message.channel.send("**Fred i verden, alle miv-scorer er nu blevet nulstillet af LimpkinLee!**")
        else:
            await message.channel.send("Alas, kun **LimpkinLee** har magten til at nulstille pointen. Whomp^2")
        return

    if message_lower == "!værsteboard":
        if not stats:
            await message.channel.send("So no miv? Good. Fred i verden.")
            return
            
        sorted_users = sorted(stats.items(), key=lambda item: item[1]["count"], reverse=True)
        
        leaderboard_text = "**🏆 DU ER DEN VÆRSTE 🏆**\n"
        for i, (uid, info) in enumerate(sorted_users[:10], start=1):
            leaderboard_text += f"{i}. {info['name']}: {info['count']} gang(e)\n"
        
        await message.channel.send(leaderboard_text)
        return

    if "aldrig miv" in message_lower:
        current_count = stats[user_id]["count"]
        # RETTET: String-citationstegn her lavede fejl før
        await message.channel.send(f"Editor's Note: {username} har, in fact, sagt miv {current_count} gang(e).")
        return

    # Finder kun bogstaverne m, i, v i rækkefølge
    cleaned_message = re.sub(r'[^a-z]', '', message_lower)
    miv_count = cleaned_message.count('miv')

    if miv_count > 0:
        current_time = time.time()
        
        if user_id not in miv_history:
            miv_history[user_id] = []
            
        for _ in range(miv_count):
            miv_history[user_id].append(current_time)
            
        miv_history[user_id] = [t for t in miv_history[user_id] if current_time - t <= 5]
        
        if len(miv_history[user_id]) > 3:
            await message.channel.send(f'{username} er en attention whore')
            return

        stats[user_id]["count"] += miv_count
        save_data(stats)
        
        total_count = stats[user_id]["count"]
        await message.channel.send(f'{username} har nu sagt miv {total_count} gang(e).')

# Hent token sikkert fra Renders indstillinger
TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    client.run(TOKEN)
else:
    print("FEJL: DISCORD_TOKEN miljøvariablen mangler på Render!")
