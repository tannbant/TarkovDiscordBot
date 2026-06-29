import os
import discord
from discord.ext import commands, tasks
import aiohttp
import logging
import random
from datetime import datetime, timezone
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ALERTS_CHANNEL_ID = int(os.getenv("ALERTS_CHANNEL_ID", 0))

GAME_MODE = "pvp"                        # use "pvp" or "pve"
MIN_PROFIT_MARGIN = 40000               

class TarkovRadarBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.api_url = "https://api.tarkov.dev/graphql"
        self.sent_events = set() 

    async def setup_hook(self):
        logging.info("Bot engine pre-hooked. Connecting to global websocket...")

    async def on_ready(self):
        logging.info(f"Successfully logged in as {self.user.name}")
        await self.change_presence(activity=discord.Game(name="Monitoring Tarkov API Pipeline..."))
        
        if not self.market_sniper_loop.is_running():
            self.market_sniper_loop.start()
            logging.info("Automated Flea Market task loop deployed.")
            
        if not self.event_tracker_loop.is_running():
            self.event_tracker_loop.start()
            logging.info("Automated Live Event data pipeline deployed and clean.")

    async def on_message(self, message):
        """Enforces channel cleanliness: automatically purges non-command text from #tarkov-help."""
        
        if message.author.bot:
            return

        channel_name = getattr(message.channel, "name", "").lower().strip()

        # target the specific #tarkov-help text channel context
        if channel_name == "tarkov-help":
            if not message.content.startswith("!"):
                try:
                    await message.delete()
                    logging.info(f"[MODERATION] Deleted non-command message from {message.author}: '{message.content}'")
                    return  # terminate processing immediately so it won't trigger standard command errors
                except discord.Forbidden:
                    logging.warning(f"[WARNING] Missing 'Manage Messages' permission to clean up channel #{message.channel.name}")
                except discord.NotFound:
                    pass

        # allow valid prefix commands to execute smoothly
        await self.process_commands(message)

    @tasks.loop(minutes=5)
    async def market_sniper_loop(self):
        """Periodically scans the Flea Market for under-priced item dips."""
        query = f"""
        {{
          items(gameMode: {GAME_MODE}) {{
            name
            lastLowPrice
            avg24hPrice
            wikiLink
            iconLink
          }}
        }}
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, json={'query': query}) as response:
                    if response.status == 200:
                        payload = await response.json()
                        items = payload.get('data', {}).get('items', [])
                        await self.process_market_data(items)
            except Exception as e:
                logging.error(f"Flea market loop processing failed: {e}")

    async def process_market_data(self, items):
        channel = self.get_channel(ALERTS_CHANNEL_ID)
        if not channel: return

        for item in items:
            low_price = item.get('lastLowPrice')
            avg_price = item.get('avg24hPrice')
            name = item.get('name')

            if not low_price or not avg_price or low_price <= 0 or avg_price <= 0:
                continue

            if low_price < (avg_price * 0.60):
                estimated_profit = int(avg_price - low_price - (avg_price * 0.15))
                if estimated_profit >= MIN_PROFIT_MARGIN:
                    embed = self.create_deal_embed(name, low_price, avg_price, estimated_profit, item.get('wikiLink'), item.get('iconLink'))
                    await channel.send(embed=embed)

    @tasks.loop(minutes=3)
    async def event_tracker_loop(self):
        """Queries Tarkov backend notices directly to alert on patches, outages, and dynamic global events."""
        query = "{ status { name message status statusCode } }"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, json={'query': query}) as response:
                    if response.status == 200:
                        payload = await response.json()
                        statuses = payload.get('data', {}).get('status', [])
                        channel = self.get_channel(ALERTS_CHANNEL_ID)
                        if not channel or not statuses: return

                        for report in statuses:
                            event_id = f"{report.get('name')}-{report.get('message')}"
                            if event_id in self.sent_events: continue
                                
                            embed = discord.Embed(
                                title="📢 BSG OFFICIAL SYSTEM NOTICE / EVENT UPDATE",
                                description=f"**System Track:** {report.get('name')}\n\n**Details:** {report.get('message')}",
                                color=discord.Color.gold(),
                                timestamp=datetime.now(timezone.utc)
                            )
                            embed.set_footer(text="Source: Escape from Tarkov Official Backend")
                            await channel.send(embed=embed)
                            self.sent_events.add(event_id)
            except Exception as e:
                logging.error(f"Server event loop processing failed: {e}")

    def create_deal_embed(self, name, low, avg, profit, wiki, icon):
        embed = discord.Embed(
            title="🚨 FLEA MARKET PRICE DROP ALERT 🚨",
            description=f"**[{name}]({wiki})** has dropped significantly below market average!",
            color=discord.Color.green()
        )
        if icon: embed.set_thumbnail(url=icon)
        embed.add_field(name="Snipe Price", value=f"{low:,} ₽", inline=True)
        embed.add_field(name="24h Average", value=f"{avg:,} ₽", inline=True)
        embed.add_field(name="Est. Resell Profit", value=f"~{profit:,} ₽", inline=False)
        embed.set_footer(text=f"Mode: {GAME_MODE.upper()}")
        return embed

bot = TarkovRadarBot()

#commands

@bot.command(name="random")
async def random_kit(ctx):
    """Generates a massive, fully randomized tactical deployment profile configuration."""
    weapons = [
        "M4A1 (Meta Laser Beam M855A1)", "Mosin Infantry (LPS Ghillie Run)", "AK-74N (5.45x39mm PP)", 
        "UMP .45 (Match FMJ Laser)", "Hunter 101 (7.62x51mm M80)", "Kedr-B (Leg Meta SP7)", 
        "P90 (SS190 Submachine)", "MP-153 Shotgun (Flechette/Magnum Buck)", "SR-25 (Marksman DMR)", 
        "VSS Vintorez (SP-6 CQC)", "RD-704 (7.62x39mm PS)", "AXMC (.338 Lapua Bolt-Action)", 
        "SA-58 (Juice Cannon)", "MP7A2 (Subsonic/FMJ Shredder)", "STM-9 (9mm Carbine Meme)",
        "AS VAL (Quiet Shredder)", "TX-15 DML", "SAG AK-545", "MCX (.300 Blackout AP)",
        "MDR 7.62x51 (Desert Powerhouse)", "Double Barrel Shotgun (Akimbo Buckshot)"
    ]
    
    armor = [
        "PACA Body Armor (Class 2)", "6B23-1 Flora (Class 3)", "Highcom Trooper (Class 4)", 
        "Korund-VM (Class 5 Heavy)", "Hexgrid / Slick (Class 6 Matrix)", "Naked (No Armor Run)",
        "NPP KlASS Bagariy (Class 5 Rig)", "6B3TM armored rig (Class 3 Ragman Starter)",
        "Crye Precision AVS (Class 4 Rig)", "Thor Integrated Armor (Class 4)",
        "Defender-2 Body Armor (Class 5)", "Zabralo-Sh (Class 6 Juggernaut)"
    ]
    
    helmets = [
        "Ssh-68 Penis Helmet", "LZSh Light Helmet", "Ulach Tan/Black (Class 4 Ear Pro)", 
        "Altyn (No Hearing, Faceshield Down)", "No Helmet / Balaclava Only", "Exfil Helmet (Ear covers + Shield)",
        "Maska 1Sch (Killa Helmet Style)", "Galvion Caiman (Lightweight Class 3)",
        "Fast MT (Fully Upgraded Deck)", "Kiver-M with Visor", "Bear/Usec Baseball Cap"
    ]
    
    backpacks = [
        "T-Bag (The Ultimate Shame)", "Scav Vest Backpack Equivalent", "Berkut / Daypack (Standard)",
        "Beta 2 Backpack", "Attack 2 (Massive Footprint)", "Raid Backpack (The Couch)",
        "Pilgrim (Big Bright Purple Target)", "Mechanism Backpack", "F4 Terminator"
    ]
    
    maps = [
        "Customs", "Factory", "Woods", "Reserve", "Shoreline", 
        "Lighthouse", "Streets of Tarkov", "Ground Zero", "The Lab (Keycard Mandatory)"
    ]
    
    objectives = [
        "Eliminate any Scav using only melee attacks or grenades.",
        "Secure 1 piece of high-tier streamer loot and immediately extract.",
        "Sprint straight to the nearest boss spawn footprint area and challenge them.",
        "Wipe a PMC squad or die trying. Zero stealth allowed.",
        "Extract within the first 10 minutes of deployment (Run through accepted).",
        "Loot every container in the resort/dorm building you encounter.",
        "You cannot heal any heavy bleeds. Bring a tourniquet or suffer.",
        "Zero to Hero style: Drop your primary weapon instantly if you find a dead body's gun.",
        "VoIP chat with the first person you hear. Try to secure a Co-op extract."
    ]

    embed = discord.Embed(
        title="🎲 TARKOV RANDOMIZER ENGINE OPERATIONAL",
        description="Your deployment gear matrix has been pulled from database systems. Good luck, PMCs.",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(name="🔫 Primary Weaponry", value=f"`{random.choice(weapons)}`", inline=True)
    embed.add_field(name="🛡️ Armor Chassis", value=f"`{random.choice(armor)}`", inline=True)
    embed.add_field(name="🪖 Head Protection", value=f"`{random.choice(helmets)}`", inline=True)
    embed.add_field(name="🎒 Tactical Backpack", value=f"`{random.choice(backpacks)}`", inline=True)
    embed.add_field(name="🗺️ Target Vector (Map)", value=f"**{random.choice(maps)}**", inline=True)
    embed.add_field(name="🎯 Mandatory Raid Objective", value=f"*{random.choice(objectives)}*", inline=False)
    
    embed.set_footer(text="Developed by Taj | Tactical Random Operations")
    await ctx.reply(embed=embed)

@bot.command(name="escape")
async def escape(ctx):
    """The harsh reality check command."""
    embed = discord.Embed(
        title="🛑 ERROR: ESCAPE IS A MYTH",
        description="You've typed `!escape`. How cute. Let's look at your actual deployment files:",
        color=discord.Color.from_rgb(139, 0, 0), 
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="⚠️ Current Status", 
        value="You claim you're uninstalling, yet you're literally using a Discord bot to track Flea Market prices right now. You aren't leaving.", 
        inline=False
    )
    embed.add_field(
        name="📉 Symptoms of the Cycle", 
        value="• Getting head-eyes'd by a Scav through three bushes.\n• Declaring the game is garbage and Alt-F4ing.\n• Opening the launcher again 4 minutes later because your hideout water collector finished.", 
        inline=False
    )
    embed.add_field(
        name="☎️ Tactical Intervention Resources", 
        value="If you or a squadmate can no longer distinguish between real life and a Headwear/Stash grid calculation, please seek immediate help:\n\n**Substance Abuse & Mental Health Services Hotline:**\n📞 `1-800-662-4357` *(Free, confidential, 24/7 support)*", 
        inline=False
    )
    embed.set_thumbnail(url="https://i.imgur.com/vHkWw5g.png") 
    embed.set_footer(text="Nikita knows where your stash lives. There is no escape.")
    await ctx.reply(embed=embed)

@bot.command(name="promo")
async def promo(ctx):
    """Displays active Escape from Tarkov promotional codes and reward manifests."""
    embed = discord.Embed(
        title="📦 ESCAPE FROM TARKOV ACTIVE PROMO CODES",
        description="Redeem these codes via the BSG Launcher or the official Escape from Tarkov website profile page.",
        color=discord.Color.from_rgb(209, 161, 44), 
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="🚢 `BOATTRIP` (High Value)", 
        value="• 400,000 Roubles\n• 2,500 Euros\n• Vaseline\n• Green Flare", 
        inline=False
    )
    embed.add_field(
        name="📦 `SPECIALDEAL` (Gear Pack)", 
        value="• Weapons, ammunition caches, and dynamic medical configurations.", 
        inline=False
    )
    embed.add_field(
        name="🧔 `SCAVYBOI` (Hideout Cache)", 
        value="• 50,000 Roubles\n• Whiskey & Alyonka Chocolate\n• 2x Bolts & 2x Nuts\n• Cord, CALOK-B, Blue Fuel Can", 
        inline=False
    )
    embed.add_field(
        name="🐛 `SBEUKOMAR` (Supplies)", 
        value="• 50,000 Roubles\n• ISKRA Ration Pack & Condensed Milk\n• Slickers Bar & CALOK-B\n• 2x Corrugated Hoses & Exp. Fuel Tank", 
        inline=False
    )
    embed.add_field(
        name="🛡️ `GOONSQUAD` (Crafting)", 
        value="• 50,000 Roubles\n• 2x KEK Tape & 2x Bolts\n• Pack of Sugar, CALOK-B, Fuel", 
        inline=False
    )
    embed.add_field(name="💡 `LIGHTSOUT`", value="• 6x Energy-Saving Lamps", inline=True)
    embed.add_field(name="🔫 `PAY2WIN`", value="• Blicky Pistol & TOZ-106\n• Ammo & T-Bag", inline=True)

    embed.set_footer(text="Developed by Taj | Codes are strictly case-sensitive.")
    await ctx.reply(embed=embed)

@bot.command(name="checkupdates")
async def checkupdates(ctx):
    """Pulls current operational status and patch logs straight from the official API."""
    await ctx.send("📡 Gathering active developer timelines and system patch logs...")
    query = "{ status { name message status statusCode } }"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(bot.api_url, json={'query': query}) as response:
                if response.status != 200: 
                    return await ctx.send("❌ Error communicating with the game data network.")
                
                payload = await response.json()
                statuses = payload.get('data', {}).get('status', [])
                
                if not statuses:
                    return await ctx.send("📭 No operational logs reported by the global api timeline.")

                for report in statuses:
                    embed = discord.Embed(
                        title=f"📋 Official Status Entry: {report.get('name')}",
                        description=report.get('message', 'No details specified.'),
                        color=discord.Color.dark_gray(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="Status Code", value=f"`{report.get('statusCode')}`", inline=True)
                    embed.add_field(name="Current State", value=f"`{report.get('status')}`", inline=True)
                    embed.set_footer(text="Live Core Infrastructure Status")
                    await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to fetch structural telemetry logs: {e}")

@bot.command(name="help")
async def help(ctx):
    """Displays a customized multi-tier tactical manifest dashboard."""
    embed = discord.Embed(
        title="⚡ SARFTARKOVBOT MANIFEST SYSTEM",
        description="Advanced raid-companion intelligence hub querying flea market matrices, item mechanics, and hideout logic frameworks.",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="📊 ECONOMY & UTILITY INTERFACES",
        value=(
            "`!itemprice <name>` (or `!ip`) ↳ Check rolling flea averages and baseline lows.\n"
            "`!slot <name>` ↳ Calculates market value efficiency ratios per grid block.\n"
            "`!promo` ↳ Displays all active gift and bundle codes.\n"
            "`!random` ↳ Generates a fully randomized raid kit profile setup.\n"
            "`!clearmsg` ↳ Purges up to 100 recent channel text logs instantly."
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚔️ COMBAT & PROGRESSION RECON",
        value=(
            "`!ammo <caliber/name>` ↳ Live ballistics chart checking penetration depth.\n"
            "`!need <name>` ↳ Cross-checks progression requirements (Hideout/Quests).\n"
            "`!map <name>` ↳ Extracts maps, tactical spawn sectors, and boss coordinates.\n"
            "`!checkupdates` ↳ Pulls Nikita/BSG live platform notices.\n"
            "`!escape` ↳ Initiates emergency sanity breakdown telemetry.\n"
            "`!events` ↳ Forces immediate parsing on dynamic sever changes."
        ),
        inline=False
    )
    
    embed.add_field(name="⚙️ DATA VECTOR", value=f"`{GAME_MODE.upper()}` Server Core", inline=True)
    embed.add_field(name="📈 ARBITRAGE MARGIN", value=f"≥ `{MIN_PROFIT_MARGIN:,} ₽` Alerts", inline=True)
    
    embed.set_footer(text="Developed by Taj | System Terminal Input")
    await ctx.send(embed=embed)

@bot.command(name="slot")
async def slot(ctx, *, item_name: str):
    """Calculates an item's efficiency footprint based on how much it's worth per slot."""
    search_keyword = item_name.strip().rstrip('.')
    await ctx.send(f"🎒 Calculating slot density value ratios for `{search_keyword}`...")

    query = """
    query GetItemSlots($nameString: String!) {
      itemsByName(name: $nameString) {
        name
        width
        height
        avg24hPrice
        iconLink
      }
    }
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(bot.api_url, json={'query': query, 'variables': {"nameString": search_keyword}}) as response:
                if response.status != 200: 
                    return await ctx.send("❌ Error contacting the core database.")
                
                payload = await response.json()
                items = payload.get('data', {}).get('itemsByName', [])

                if not items: 
                    return await ctx.send("❌ Inventory footprint check failed. Check item name string.")

                matched = items[0]
                width = matched.get('width', 1)
                height = matched.get('height', 1)
                avg_price = matched.get('avg24hPrice') or 0
                total_slots = width * height

                val_per_slot = int(avg_price / total_slots) if total_slots > 0 and avg_price > 0 else 0

                embed = discord.Embed(title=f"🎒 Stash Optimizer: {matched.get('name')}", color=discord.Color.green())
                if matched.get('iconLink'): embed.set_thumbnail(url=matched.get('iconLink'))

                embed.add_field(name="Grid Footprint", value=f"📏 `{width}x{height}` ({total_slots} slot{'s' if total_slots > 1 else ''})", inline=True)
                embed.add_field(name="24h Market Avg", value=f"💰 `{avg_price:,} ₽`", inline=True)
                embed.add_field(name="Value Density Ratio", value=f"📈 **{val_per_slot:,} ₽ per single slot**", inline=False)

                if val_per_slot >= 20000:
                    advice = "🔥 High efficiency loot. Prioritize this over standard components."
                elif val_per_slot >= 10000:
                    advice = "🟡 Standard value loop. Keep if backpack has dead spaces left."
                else:
                    advice = "🗑️ Low value-per-slot footprint. Drop this first for better options."

                embed.add_field(name="📋 Stash Execution Order", value=advice, inline=False)
                embed.set_footer(text="Developed by Taj")
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed processing value weight layouts: {e}")

@bot.command(name="need")
async def need(ctx, *, item_name: str):
    """Checks whether an item is needed for quests or hideout upgrades."""
    search_keyword = item_name.strip().rstrip('.')
    await ctx.send(f"🔍 Analyzing progression value data for `{search_keyword}`...")

    query = """
    query GetItemProgression($nameString: String!) {
      itemsByName(name: $nameString) {
        name
        wikiLink
        iconLink
        usedInTasks {
          name
          minPlayerLevel
        }
      }
    }
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(bot.api_url, json={'query': query, 'variables': {"nameString": search_keyword}}) as response:
                if response.status != 200: return await ctx.send("❌ Error contacting the core database.")
                payload = await response.json()
                items = payload.get('data', {}).get('itemsByName', [])

                if not items: return await ctx.send(f"❌ No matching item profiles found.")
                
                matched = items[0]
                name = matched.get('name')
                tasks = matched.get('usedInTasks', [])

                embed = discord.Embed(title=f"📋 Progression Profile: {name}", color=discord.Color.dark_gold(), url=matched.get('wikiLink'))
                if matched.get('iconLink'): embed.set_thumbnail(url=matched.get('iconLink'))

                if tasks:
                    task_list = "\n".join([f"• **{t['name']}** (Req Lvl: {t['minPlayerLevel'] or 'N/A'})" for t in tasks[:5]])
                    if len(tasks) > 5: task_list += f"\n*...and {len(tasks)-5} more tasks.*"
                    embed.add_field(name="🎯 Required For Quests (FiR Needed)", value=task_list, inline=False)
                else:
                    embed.add_field(name="🎯 Required For Quests", value="❌ Not required for any main-line trader quests.", inline=False)
                
                embed.add_field(name="🏠 Hideout Logistics Advice", value=f"Keep if looking to secure early crafting rotations or structural requirements. Verify block limits.", inline=False)
                embed.set_footer(text="Developed by Taj")
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error compiling item ledger: {e}")

@bot.command(name="ammo")
async def ammo(ctx, *, ammo_name: str):
    """Returns precise live ballistics statistics for a weapon projectile profile."""
    search_keyword = ammo_name.strip().rstrip('.')
    await ctx.send(f"⚔️ Calibrating target ballistic damage algorithms for `{search_keyword}`...")

    query = """
    query GetAmmoData($nameString: String!) {
      itemsByName(name: $nameString) {
        name
        iconLink
        properties {
          ... on ItemPropertiesAmmo {
            damage
            penetrationPower
            armorDamage
          }
        }
      }
    }
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(bot.api_url, json={'query': query, 'variables': {"nameString": search_keyword}}) as response:
                if response.status != 200: return
                payload = await response.json()
                items = payload.get('data', {}).get('itemsByName', [])

                if not items: return await ctx.send("❌ Ballistics profile matches 0 items.")
                
                matched = items[0]
                props = matched.get('properties', {})
                if not props: return await ctx.send("❌ This item has no registered combat mechanics.")

                pen = props.get('penetrationPower', 0)
                dmg = props.get('damage', 0)
                arm_dmg = props.get('armorDamage', 0)

                if pen >= 50: effectiveness = "🟢 Melts Class 5 & 6 instantly"
                elif pen >= 40: effectiveness = "🟡 Shreds Class 4, struggles on Class 6"
                elif pen >= 30: effectiveness = "🟠 Deflects on heavy armor, wipes Class 3"
                else: effectiveness = "🔴 Pure flesh round. Focus limb vectors."

                embed = discord.Embed(title=f"💥 Ballistics Breakdown: {matched.get('name')}", color=discord.Color.red())
                if matched.get('iconLink'): embed.set_thumbnail(url=matched.get('iconLink'))
                
                embed.add_field(name="Flesh Damage", value=f"🩸 `{dmg}`", inline=True)
                embed.add_field(name="Penetration Value", value=f"🛡️ `{pen}`", inline=True)
                embed.add_field(name="Armor Damage %", value=f"⚙️ `{arm_dmg}%`", inline=True)
                embed.add_field(name="🎯 Combat Armor Class Effectiveness", value=effectiveness, inline=False)
                embed.set_footer(text="Developed by Taj")
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to parse data points: {e}")

@bot.command(name="map")
async def map(ctx, *, map_name: str):
    """Returns extraction vectors and boss presence information for a specified area."""
    search_term = map_name.strip().lower()
    
    maps_db = {
        "customs": {"title": "Customs Combat Array", "url": "https://tarkov.dev/map/customs", "boss": "Reshala (30% Spawn Chance at Dorms/Gas Station)"},
        "factory": {"title": "Factory CQC Killzone", "url": "https://tarkov.dev/map/factory", "boss": "Tagilla (30% Spawn Chance with Sledgehammer)"},
        "interchange": {"title": "Interchange Mall Matrix", "url": "https://tarkov.dev/map/interchange", "boss": "Killa (Roaming across corridors)"},
        "reserve": {"title": "Reserve Military Depot", "url": "https://tarkov.dev/map/reserve", "boss": "Glukhar (Trainyard / Bunker Command)"},
        "shoreline": {"title": "Shoreline Health Resort", "url": "https://tarkov.dev/map/shoreline", "boss": "Sanitar (Resort / Cottages / Pier)"},
        "woods": {"title": "Woods Tactical Forest Arena", "url": "https://tarkov.dev/map/woods", "boss": "Shturman (Logging Camp Center)"},
        "lighthouse": {"title": "Lighthouse Rogue Outpost", "url": "https://tarkov.dev/map/lighthouse", "boss": "Zryachiy (Bridge) & Rogue Commanders"},
        "streets": {"title": "Streets of Tarkov Urban Sector", "url": "https://tarkov.dev/map/streets-of-tarkov", "boss": "Kaban (Car Dealer) & LexOs Sweepers"},
        "ground zero": {"title": "Ground Zero Starter Sector", "url": "https://tarkov.dev/map/ground-zero", "boss": "Kollontay (Terragroup building sectors)"}
    }

    matched_map = None
    for k, v in maps_db.items():
        if k in search_term:
            matched_map = v
            break

    if not matched_map:
        return await ctx.send("❌ Map footprint not recognized. Use: `customs`, `factory`, `woods`, `reserve`, `streets`, etc.")

    embed = discord.Embed(title=f"🗺️ Tactical Deployment: {matched_map['title']}", color=discord.Color.blue())
    embed.add_field(name="⚡ Confirmed Boss Hostiles", value=matched_map['boss'], inline=False)
    embed.add_field(name="🗺️ Navigation Link", value=f"[Click to Open Interactive 3D Map Grid]({matched_map['url']})", inline=False)
    embed.set_footer(text="Developed by Taj | Keep eyes up on approach vectors.")
    await ctx.send(embed=embed)

@bot.command(name="itemprice", aliases=["ip"])
async def itemprice(ctx, *, item_name: str):
    search_keyword = item_name.strip().rstrip('.')
    await ctx.send(f"🔍 Searching the flea market for `{search_keyword}`...")
    query = """
    query GetItemDetails($nameString: String!) {
      itemsByName(name: $nameString) {
        name
        lastLowPrice
        avg24hPrice
        wikiLink
        iconLink
      }
    }
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(bot.api_url, json={'query': query, 'variables': {"nameString": search_keyword}}) as response:
                if response.status != 200: return await ctx.send("❌ Error connecting to database.")
                payload = await response.json()
                items = payload.get('data', {}).get('itemsByName', [])
                if not items: return await ctx.send(f"❌ Could not find item matching `{search_keyword}`.")

                matched_item = items[0]
                avg_price = matched_item.get('avg24hPrice')
                low_price = matched_item.get('lastLowPrice')

                embed = discord.Embed(title=f"📊 Market Report: {matched_item.get('name')}", color=discord.Color.blue(), url=matched_item.get('wikiLink'))
                if matched_item.get('iconLink'): embed.set_thumbnail(url=matched_item.get('iconLink'))

                embed.add_field(name="24h Rolling Average", value=f"{avg_price:,} ₽" if avg_price else "N/A", inline=False)
                embed.add_field(name="Current Low Price", value=f"{low_price:,} ₽" if low_price else "N/A", inline=True)
                embed.set_footer(text="Developed by Taj")
                await ctx.send(embed=embed)
        except Exception as e: await ctx.send(f"❌ Execution error: {e}")

@bot.command(name="events")
async def events(ctx):
    await ctx.send("🔍 Scanning active live servers for gameplay modifiers and active events...")
    query = "{ status { name message status statusCode } }"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(bot.api_url, json={'query': query}) as response:
                if response.status != 200: return await ctx.send("❌ Error fetching notices.")
                payload = await response.json()
                statuses = payload.get('data', {}).get('status', [])
                events_found = 0
                for report in statuses:
                    embed = discord.Embed(title="📢 ACTIVE TARKOV GAME EVENT DETECTED", description=f"**System Track:** {report.get('name')}\n\n**Details:** {report.get('message')}", color=discord.Color.orange())
                    await ctx.send(embed=embed)
                    events_found += 1
                if events_found == 0: await ctx.send("📝 No specialized modifiers or active dynamic events are running right now.")
        except Exception as e: await ctx.send(f"❌ Malfunction pulling layout: {e}")

@bot.command(name="clearmsg")
@commands.has_permissions(manage_messages=True)
async def clearmsg(ctx):
    try:
        deleted = await ctx.channel.purge(limit=100)
        await ctx.send(f"🗑️ Successfully deleted {len(deleted)} messages.", delete_after=3)
    except discord.Forbidden: await ctx.send("❌ Missing `Manage Messages` server permission.")
    except Exception as e: await ctx.send(f"❌ Error clearing history: {e}")

@bot.command(name="testprices")
async def testprices(ctx):
    await ctx.send("🔍 Fetching target metrics directly from live Tarkov API pipeline...")
    query = f"{{ items(gameMode: {GAME_MODE}) {{ name lastLowPrice avg24hPrice wikiLink iconLink }} }}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(bot.api_url, json={'query': query}) as response:
                if response.status != 200: return await ctx.send("❌ Server API data grab failure.")
                payload = await response.json()
                items = payload.get('data', {}).get('items', [])
                deals_found = 0
                for item in items:
                    low_price = item.get('lastLowPrice')
                    avg_price = item.get('avg24hPrice')
                    if not low_price or not avg_price or low_price <= 0 or avg_price <= 0: continue
                    if low_price < (avg_price * 0.85):
                        estimated_profit = int(avg_price - low_price - (avg_price * 0.15))
                        if estimated_profit > 10000:
                            embed = bot.create_deal_embed(item.get('name'), low_price, avg_price, estimated_profit, item.get('wikiLink'), item.get('iconLink'))
                            await ctx.send(embed=embed)
                            deals_found += 1
                            if deals_found >= 3: break
                if deals_found == 0: await ctx.send("✅ Network stream operating flawlessly, market stable.")
        except Exception as e: await ctx.send(f"❌ Core script exception: {e}")

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        logging.critical("❌ Bot engine crash: 'DISCORD_BOT_TOKEN' environment flag missing from configurations.")
    else:
        bot.run(DISCORD_BOT_TOKEN)