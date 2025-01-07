from os import getcwd

def working_directory():
    """
    Returns the current working directory in a format compatible with file paths.
    :return: The working directory with forward slashes.
    """
    cwd = getcwd()
    working_directory = cwd.replace('\\', '/') + "/"
    return working_directory

class Rickroll(object):
    def __init__(self, discord, database):
        """
        Initializes the Rickroll class.
        :param discord: Discord API reference.
        :param database: Database instance to track rickroll targets.
        """
        self.discord = discord
        self.database = database

    def is_target(self, member):
        """
        Determines if a member is a target for a rickroll.
        :param member: The member to check.
        :return: True if the member is a target, False otherwise.
        """
        rickroll_member_ids = self.database.get_from_guild(member.guild.id, "rickroll_members").split()
        rickroll_role_ids = self.database.get_from_guild(member.guild.id, "rickroll_roles").split()
        return str(member.id) in rickroll_member_ids or any([str(role.id) in rickroll_role_ids for role in member.roles])

    async def run(self, client, member, before, after):
        """
        Triggers a rickroll by playing audio when a target joins a voice channel.
        :param client: The Discord client instance.
        :param member: The member whose voice state updated.
        :param before: The previous voice state.
        :param after: The new voice state.
        """
        if before.channel is None and after.channel is not None and self.is_target(member):
            if member.guild.get_member(client.user.id).voice is None:
                voicechannel = await after.channel.connect()
                print("Rickrolling " + member.name + " in " + after.channel.name)
                voicechannel.play(self.discord.FFmpegPCMAudio(working_directory() + 'nevergonnagiveyouup.mp3'))
