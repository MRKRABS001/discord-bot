import os
import threading
import nextcord
from nextcord.ext import commands
from fastapi import FastAPI
import uvicorn


TOKEN = os.getenv("DISCORD_TOKEN")
ROLE_NAME = "Pic Perms"
STATUS_KEYWORD = "RYZEN"

intents = nextcord.Intents.all()
intents.members = True
intents.presences = True  

bot = commands.Bot(command_prefix="!", intents=intents)


app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

def run_webserver():
    port = int(os.environ.get("PORT", 8080))  
    uvicorn.run(app, host="0.0.0.0", port=port)


threading.Thread(target=run_webserver, daemon=True).start()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    for guild in bot.guilds:
        await guild.chunk()  
    await sweep_members()


async def sweep_members():
    """Check all members and add/remove role based on status"""
    for guild in bot.guilds:
        roles = [r for r in guild.roles if r.name == ROLE_NAME]
        if not roles:
            print(f"Role '{ROLE_NAME}' not found in guild '{guild.name}'")
            continue
        role = roles[0]

        for member in guild.members:
            if member.bot:
                continue
            await update_member_role(member, role)


async def update_member_role(member, role):
    """Add or remove role based on member's custom status"""
    has_keyword = any(
        isinstance(activity, nextcord.CustomActivity)
        and STATUS_KEYWORD in (activity.name or "")
        for activity in member.activities
    )

    if has_keyword and role not in member.roles:
        try:
            await member.add_roles(role)
            print(f"[GAVE] {ROLE_NAME} to {member.name} in {member.guild.name}")
        except Exception as e:
            print(f"[ERROR ADD] Failed to add role to {member.name}: {e}")

    elif not has_keyword:
        roles_to_remove = [r for r in member.roles if r.name == ROLE_NAME]
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove)
                print(f"[TOOK] {ROLE_NAME} from {member.name} in {member.guild.name}")
            except Exception as e:
                print(f"[ERROR REMOVE] Failed to remove role from {member.name}: {e}")


@bot.event
async def on_presence_update(before, after):
    """Trigger role updates when a user's status/activity changes"""
    if after.bot:
        return
    roles = [r for r in after.guild.roles if r.name == ROLE_NAME]
    if not roles:
        return
    role = roles[0]
    await update_member_role(after, role)


@bot.event
async def on_member_join(member):
    """Trigger role update for new members"""
    if member.bot:
        return
    roles = [r for r in member.guild.roles if r.name == ROLE_NAME]
    if not roles:
        return
    role = roles[0]
    await update_member_role(member, role)


# --- Run Bot ---
if __name__ == "__main__":
    if TOKEN is None:
        print("❌ ERROR: DISCORD_TOKEN environment variable not set.")
    else:
        bot.run(TOKEN)

