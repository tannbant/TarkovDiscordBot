# TarkovDiscordBot

An advanced companion intelligence utility built for Discord. It seamlessly queries flea market matrices, item mechanics, loadout randomizers, and hideout logic frameworks directly into your server.

---

## Getting Started

You can either invite the pre-made bot directly to your server or host your own custom instance using the source code.

### Option A: Direct Invite (Easiest)
If you don't want to host the bot yourself, you can instantly add the pre-configured instance to your Discord server using the link below:

**[Invite TarkovDiscordBot to your Server](https://discord.com/oauth2/authorize?client_id=1520545719360950302)**

---

### Option B: Self-Hosting & Custom Bot Setup

If you prefer to host the bot locally or on a server, follow this seamless setup guide.

#### 1. Create a Discord Application
To run your own instance, you need to register a bot application:
1. Go to the Discord Developer Portal (https://discord.com/developers/applications).
2. Click "New Application" in the top right and give it a name.
3. Navigate to the "Bot" tab on the left menu, click "Add Bot", and confirm.
4. Under the "Token" section, click "Reset Token" and copy the secret string. (Keep this private!)
5. Scroll down to "Privileged Gateway Intents" and enable "Message Content Intent" so the bot can read commands like `!random`.

#### 2. Clone the Repository
Open your terminal/command prompt and run:
```bash
git clone [https://github.com/tannbant/TarkovDiscordBot.git](https://github.com/tannbant/TarkovDiscordBot.git)
cd TarkovDiscordBot
