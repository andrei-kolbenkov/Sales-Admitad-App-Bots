import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from message import get_coupons, get_advcampaigns_for_website2





scheduler = AsyncIOScheduler()

ADMIN_CHAT_ID = []
API_TOKEN = ''

bot = Bot(token=API_TOKEN)



async def periodic_loading():
    print('Начало парсинга')
    # await bot.send_message(, 'Парсинг начался')

    try:
        messages_for_delete, text, go_out_shops = get_coupons()
        # await bot.send_message(, text)
        # await bot.send_message(, text=f'Магазины, которые больше не с нами: {go_out_shops}')
        # await bot.send_message(, text=f'Магазины, которые больше не с нами: {go_out_shops}')
        for message in messages_for_delete.values():
            if (message[0] is not None) and (message[1] is not None):
                await bot.delete_message(message[0], message[1])
    except Exception as e:
        print('Нет сообщений для удаления:', e)

    try:
        products_for_delete, not_rub = get_advcampaigns_for_website2()
        for product in products_for_delete:
            await bot.delete_message(product[0], product[1])
        print(not_rub)
        # await bot.send_message(, f'Товары не доступны: {not_rub}')
        # await bot.send_message(, f'Товары не доступны: {not_rub}')
    except Exception as e:
        print('Нет постов с товарами для удаления:', e)

    print('Парсинг завершен')
    await bot.send_message(, 'Парсинг завершен')


if __name__ == '__main__':
    # asyncio.run(periodic_loading())
    loop = asyncio.get_event_loop()
    scheduler.add_job(periodic_loading, IntervalTrigger(hours=4))
    scheduler.start()
    loop.run_forever()