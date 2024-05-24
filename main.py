import discord
import datetime
from discord.ext import commands, tasks
import yaml

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

token = cfg.get("token",False)
if not token:
    print("plz fill config.yaml file")
    exit()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

utc = datetime.timezone.utc

# If no tzinfo is given then UTC is assumed.
time = datetime.time(hour=18, minute=25, tzinfo=utc)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    @tasks.loop(time=time)
    async def my_task(self):
        print("My task is running!")

client.run(token)
