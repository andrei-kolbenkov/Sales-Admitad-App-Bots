import asyncio
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from message import get_coupons, get_advcampaigns_for_website2


ADMIN_CHAT_ID = []
API_TOKEN = ''
bot = Bot(token=API_TOKEN)

# Глобальный планировщик
scheduler = AsyncIOScheduler()

async def periodic_loading():
    print('Начало парсинга')
    try:
        for admin in ADMIN_CHAT_ID:
            await bot.send_message(admin, 'Парсинг начался')
    except Exception as e:
        print(e)
        await asyncio.sleep(30)
        for admin in ADMIN_CHAT_ID:
            await bot.send_message(admin, 'Парсинг начался')

    try:
        messages_for_delete, text, go_out_shops = get_coupons()
        try:
            for admin in ADMIN_CHAT_ID:
                await bot.send_message(admin, text)
                await bot.send_message(admin, text=f'Магазины, которые больше не с нами: {go_out_shops}')
        except Exception as e:
            print(e)
            await asyncio.sleep(30)
            for admin in ADMIN_CHAT_ID:
                await bot.send_message(admin, text)
                await bot.send_message(admin, text=f'Магазины, которые больше не с нами: {go_out_shops}')
        for message in messages_for_delete.values():
            if (message[0] is not None) and (message[1] is not None):
                try:
                    await bot.delete_message(message[0], message[1])
                except Exception as e:
                    print(e)
                    await asyncio.sleep(30)
                    await bot.delete_message(message[0], message[1])
    except Exception as e:
        print('Нет сообщений для удаления:', e)

    
    try:
        products_for_delete, not_rub = get_advcampaigns_for_website2()
        try:
            for product in products_for_delete:
                try:
                    await bot.delete_message(product[0], product[1])
                except Exception as e:
                    print(e)
                    await asyncio.sleep(30)
                    await bot.delete_message(product[0], product[1])
        except Exception as e:
            print('Нет постов с товарами для удаления:', e)
        print(not_rub)
    except Exception as e:
        print(e)

    print('Парсинг завершен')
    try:
        for admin in ADMIN_CHAT_ID:
            await bot.send_message(admin, 'Парсинг завершен')
    except Exception as e:
        print(e)
        await asyncio.sleep(30)
        for admin in ADMIN_CHAT_ID:
            await bot.send_message(admin, 'Парсинг завершен')



if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)  # Используем текущий цикл событий

    # Добавляем задачу для периодической загрузки
    scheduler.add_job(periodic_loading, IntervalTrigger(hours=4))
    scheduler.start()

    # Ручной запуск первого выполнения задачи
    loop.create_task(periodic_loading())

    try:
        print("Запуск событийного цикла")
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("Остановка событийного цикла")
        scheduler.shutdown()
