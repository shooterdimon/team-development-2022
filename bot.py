import config
from aiogram import Bot, Dispatcher


bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)
