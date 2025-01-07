class XpManager(object):
    def __init__(self, discord, database, time):
        """
        Initializes the XP Manager.
        :param discord: Discord API reference.
        :param database: Database instance to manage guild and member data.
        :param time: Time module to track XP gain intervals.
        """
        self.discord = discord
        self.database = database
        self.time = time

    def get_roles(self, member) -> dict:
        """
        Retrieves the roles associated with XP thresholds for a guild.
        :param member: The member whose guild roles are being fetched.
        :return: A dictionary mapping XP thresholds to roles.
        """
        role_ids = self.database.get_from_guild(member.guild.id, "roles")
        roles = {int(min_xp): member.guild.get_role(role_ids[min_xp]) for min_xp in role_ids}
        return roles

    def calculate_xp(self, member) -> int:
        """
        Calculates the total XP for a member.
        :param member: The member whose XP is being calculated.
        :return: The member's XP as an integer.
        """
        xp = self.database.get_from_member(member, "xp")
        xp = int(round(xp))
        return xp

    async def update(self, member):
        """
        Updates the roles of a member based on their XP.
        :param member: The member whose roles need to be updated.
        """
        roles = self.get_roles(member)
        xp = self.calculate_xp(member)
        possible = [min_xp for min_xp in roles.keys() if min_xp <= xp]
        if possible:
            key = max(possible)
            current_role = roles[key]
            to_remove = [role for role in member.roles if role in roles.values() and role != current_role]
            if to_remove:
                await member.remove_roles(*to_remove, reason="xp auto system")
            await member.add_roles(current_role, reason="xp auto system")

    async def update_all(self, guild):
        """
        Updates XP-based roles for all members in a guild.
        :param guild: The guild whose members' roles will be updated.
        """
        members = guild.members
        for member in members:
            await self.update(member)

    def add_xp(self, member, xp):
        """
        Adds XP to a member.
        :param member: The member to receive XP.
        :param xp: The amount of XP to add.
        """
        xp = self.database.get_from_member(member, "xp") + xp
        self.database.change_in_member(member, "xp", xp)

    async def message_xp(self, message):
        """
        Awards XP for sending messages if the cooldown has passed.
        :param message: The message that triggered the XP gain.
        """
        last_counted_message_time = self.database.get_from_member(message.author, "last_counted_message_time")
        difference = self.time() - last_counted_message_time
        if difference >= 60:
            self.database.change_in_member(message.author, "last_counted_message_time", self.time())
            self.add_xp(message.author, 1)
            await self.update(message.author)

    async def voice_xp(self, member, before, after):
        """
        Awards XP for time spent in voice channels.
        :param member: The member in the voice channel.
        :param before: The state of the member before the voice update.
        :param after: The state of the member after the voice update.
        """
        last_checkpoint = self.database.get_from_member(member, "last_voice_checkpoint")
        if last_checkpoint is not None:
            voice_time = self.time() - last_checkpoint
            if before.self_video:
                voice_time *= 3
            xp = voice_time / 60
            self.add_xp(member, xp)
            self.database.change_in_member(member, "last_voice_checkpoint", None)
            await self.update(member)
        if after.channel is not None:
            if not any([len([member for member in after.channel.members if not member.bot]) < 2, after.afk, after.deaf, after.mute, after.self_deaf, after.self_mute]):
                self.database.change_in_member(member, "last_voice_checkpoint", self.time())

    async def no_xp(self, guilds):
        """
        Resets the voice XP checkpoint for all members in all guilds.
        :param guilds: The list of guilds to reset XP for.
        """
        for guild in guilds:
            for member in guild.members:
                self.database.change_in_member(member, "last_voice_checkpoint", None)
