# SARFTarkovRadar

A custom companion bot built for Discord that queries flea market prices, item stats, ballistics records, and map data directly into your server.

---

## Getting Started and Configuration

To run this bot, you must host your own instance using the source code below. Because the bot relies on specific automated tracking functions, it requires your individual server channel configurations to run properly.

### 1. Create a Discord Application
To register your own instance of the bot:
1. Go to the Discord Developer Portal (https://discord.com/developers/applications).
2. Click "New Application" in the top right and give it a name.
3. Navigate to the "Bot" tab on the left menu, click "Add Bot", and confirm.
4. Under the "Token" section, click "Reset Token" and copy the secret string. (Keep this private!)
5. Scroll down to "Privileged Gateway Intents" and enable "Message Content Intent" so the bot can read commands like `!random`.
6. Then setup the .env with the discord bot token in the developer app of discord. After go to the text channel where bot will send, then right click the channel and copy the ID. 

### 2. Clone the Repository
Open your terminal/command prompt and run:
```bash
git clone [https://github.com/tannbant/TarkovDiscordBot.git](https://github.com/tannbant/TarkovDiscordBot.git)
cd TarkovDiscordBot



