from tinydb import TinyDB, Query

class Database(object):
    def __init__(self, name):
        """
        Initializes the Database object with a TinyDB instance.
        :param name: The name of the database file (without extension).
        """
        self.name = name
        self.data = TinyDB(name + ".json")

    def save_guild(self, guild_id):
        """
        Saves a new guild entry with default values.
        :param guild_id: The ID of the guild to save.
        """
        self.data.insert({"guild_id": guild_id, "prefix": "!", "roles": {}, "rickroll_members": "", "rickroll_roles": "", "members": {}})

    def get_guild(self, guild_id):
        """
        Retrieves guild data by ID. If not found, creates a new entry.
        :param guild_id: The ID of the guild to retrieve.
        :return: The guild data.
        """
        data = self.data.search(Query().guild_id == guild_id)
        if len(data) == 0:
            self.save_guild(guild_id)
            data = self.data.search(Query().guild_id == guild_id)
        return data[0]

    def update_guild(self, guild_id, update):
        """
        Updates an existing guild entry with new data.
        :param guild_id: The ID of the guild to update.
        :param update: The data to update in the guild entry.
        """
        self.data.update(update, Query().guild_id == guild_id)

    def change_in_guild(self, guild_id, key, value):
        """
        Changes a specific key-value pair in a guild entry.
        :param guild_id: The ID of the guild.
        :param key: The key to update.
        :param value: The new value for the key.
        """
        guild = self.get_guild(guild_id)
        guild.update({key: value})
        self.update_guild(guild_id, guild)

    def get_from_guild(self, guild_id, key):
        """
        Retrieves a specific value from a guild by key.
        :param guild_id: The ID of the guild.
        :param key: The key to retrieve the value for.
        :return: The value associated with the key.
        """
        guild = self.get_guild(guild_id)
        return guild[key]

    def save_member(self, member):
        """
        Saves a new member entry with default values.
        :param member: The member object to save.
        """
        members = self.get_from_guild(member.guild.id, "members")
        members.update({str(member.id): {"xp": 0, "last_counted_message_time": 0, "last_voice_checkpoint": None}})
        self.change_in_guild(member.guild.id, "members", members)

    def get_from_member(self, member, key):
        """
        Retrieves a specific value from a member by key.
        If the member does not exist, creates a new entry.
        :param member: The member object to retrieve data for.
        :param key: The key to retrieve the value for.
        :return: The value associated with the key for the member.
        """
        members = self.get_from_guild(member.guild.id, "members")
        if str(member.id) not in members.keys():
            self.save_member(member)
            members = self.get_from_guild(member.guild.id, "members")
        member = members[str(member.id)]
        return member[key]

    def change_in_member(self, member, key, value):
        """
        Changes a specific key-value pair in a member entry.
        If the member does not exist, creates a new entry.
        :param member: The member object to update.
        :param key: The key to update.
        :param value: The new value for the key.
        """
        members = self.get_from_guild(member.guild.id, "members")
        if str(member.id) not in members.keys():
            self.save_member(member)
            members = self.get_from_guild(member.guild.id, "members")
        member_obj = members[str(member.id)]
        member_obj.update({key: value})
        self.change_in_guild(member.guild.id, "members", members)
