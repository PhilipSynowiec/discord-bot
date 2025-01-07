import discord
import os
from dotenv import load_dotenv
from database import Database
from xp_system import XpManager
from commands import Commands
from time import time
from rickroll import Rickroll

load_dotenv()
TOKEN = os.getenv('TOKEN')

database = Database("bot")
xp_manager = XpManager(discord, database, time)
commands = Commands(discord, xp_manager)
rickroll = Rickroll(discord, database)

class MyClient(discord.Client):
    def __init__(self):
        """
        Initializes the Discord client with all intents enabled.
        """
        super().__init__(intents = discord.Intents.all())

    async def on_connect(self):
        """
        Event triggered when the bot connects to Discord.
        """
        await xp_manager.no_xp(client.guilds)

    async def on_ready(self):
        """
        Event triggered when the bot is ready.
        Changes bot presence to 'watching Squid Game'.
        """
        print('successfully logged in')
        activity = discord.Activity(name = "Squid Game", type = discord.ActivityType.watching)
        await client.change_presence(status='online', activity = activity)

    async def on_disconnect(self):
        """
        Event triggered when the bot disconnects from Discord.
        Updates the bot's presence to 'offline'.
        """
        await client.change_presence(status='offline')

    async def on_message(self, message):
        """
        Event triggered when a message is sent in a text channel.
        Processes XP for the message and runs the command handler.
        :param message: The message object that was sent.
        """
        print("a message was sent")  # Debugging print

        if message.author != client:
            if type(message.channel) is discord.TextChannel:
                await xp_manager.message_xp(message)
                await commands.run(message)

    async def on_voice_state_update(self, member, before, after):
        """
        Event triggered when a user's voice state changes.
        Processes XP and checks for rickroll triggers.
        :param member: The member whose voice state updated.
        :param before: The previous voice state.
        :param after: The new voice state.
        """
        await xp_manager.voice_xp(member, before, after)
        await rickroll.run(client, member, before, after)

    async def on_member_update(self, before, after):
        """
        Event triggered when a member's information is updated.
        Updates the XP of the member.
        :param before: The member object before the update.
        :param after: The member object after the update.
        """
        await xp_manager.update(after)

client = MyClient()
client.run(TOKEN)
