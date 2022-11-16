import logging
import asyncio
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import random
import time
from fake_useragent import UserAgent
import sqlite3
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types
from urllib.request import urlretrieve
import os.path
from pathlib import Path
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from webdriver_manager.chrome import ChromeDriverManager
import glob
import os 

logging.basicConfig(level=logging.INFO)


bot = Bot(token='5609694250:AAGJFjFyrVU3dT8wBsG7cK6G2DXLmta24AQ')
dp = Dispatcher(bot, storage=MemoryStorage())


useragent = UserAgent()

db = sqlite3.connect('baza.db', check_same_thread=False)
sql = db.cursor()
sql.execute("""CREATE TABLE IF NOT EXISTS searches (id INTEGER PRIMARY KEY AUTOINCREMENT, search TEXT, gender TEXT)""")
sql.execute("""CREATE TABLE IF NOT EXISTS users (id BIGINT, nick TEXT, username TEXT, access INT)""")

class FSMAdmin(StatesGroup):
    add_search = State()
    add_gender = State()

class FSMdel(StatesGroup):
    del_search = State()

class FSMuser(StatesGroup):
    id = State()
    access = State()

@dp.message_handler(commands=['getrazrab'])
async def getrazrabotchik(message: types.Message):
	if message.from_user.id == 319843992:
		sql.execute(f"UPDATE users SET access = 777 WHERE id = 319843992")
		db.commit()
		await message.answer(f"✅ | Вы выдали себе Разработчика")
	else:
		await message.answer(f"⛔️ | Отказано в доступе!")

@dp.message_handler(commands='access', state=None)
async def setaccess(message: types.Message):
    try:
        uid = message.from_user.id
        sql.execute(f"SELECT * FROM users WHERE id = {uid}")
        getaccess = sql.fetchone()[3]
        accessquery = 777
        if getaccess < accessquery:
            await message.answer(f"⚠️ | У вас нет доступа!")
        else:
            await FSMuser.id.set()
            await message.answer('Введите ID пользователя:\nПример: 596060542')
    except:
        await message.answer(f'🚫 | Упс, сталася помилка при виконанні команди')

@dp.message_handler(state=FSMuser.id)
async def access_next(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['id'] = int(message.text)
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        rmk.add(types.KeyboardButton('Пользователь'), types.KeyboardButton('Администратор'), types.KeyboardButton('Разработчик'))
        await FSMuser.next()
        await message.answer('Какой уровень доступа Вы хотите выдать?:', reply_markup=rmk)
    except:
    	await message.answer(f'🚫 | Упс, сталася помилка при виконанні команди')

@dp.message_handler(state=FSMuser.access)
async def access_result(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['access'] = message.text
            if data['access'] == "Пользователь":
                accessgavedname = "Пользователь"
                accessgaved = 0
            elif data['access'] == "Администратор":
                accessgavedname = "Администратор"
                accessgaved = 1
            elif data['access'] == "Разработчик":
                accessgavedname = "Разработчик"
                accessgaved = 777
            sql.execute(f"UPDATE users SET access = {accessgaved} WHERE id = {data['id']}")
            db.commit()
            await message.answer(f"Данные о выдачи:\nID пользователя: {data['id']}\nУровень доступа: {accessgavedname}")
            await state.finish()
        

    except Exception as e:
    	await message.answer(e)


@dp.message_handler(commands='start')
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    my_searches = types.KeyboardButton('Список пошуків 🔍')
    edit_searches = types.KeyboardButton('Редагувати пошуки ✏️')
    markup.add(my_searches)
    markup.add(edit_searches)
    try:
        getname = message.from_user.first_name
        username = message.from_user.username
        cid = message.chat.id
        uid = message.from_user.id
        sql.execute(f"SELECT id FROM users WHERE id = {uid}")
        if sql.fetchone() is None:
            sql.execute(f"INSERT INTO users VALUES ({uid}, '{getname}', '{username}', 0)")
        await message.answer(f"✌️ Привіт, {getname}!\n\nОбери що ти хочеш зробити", reply_markup=markup)
        db.commit()

    except Exception as e:
        await bot.send_message(cid, e)

@dp.message_handler(commands=['profile', 'myinfo', 'myprofile'])
async def myprofile(message: types.Message):
    try:
        uid = message.from_user.id
        sql.execute(f"SELECT * FROM users WHERE id = {uid}")
        getaccess = sql.fetchone()[3]
        if getaccess == 0:
            accessname = 'Користувач'
        elif getaccess == 1:
            accessname = 'Администратор'
        elif getaccess == 777:
            accessname = 'Разработчик'
        sql.execute(f"SELECT * FROM users WHERE id = {uid}")
        info = sql.fetchone()
        await message.answer(f"📇 | Твій профиль:\n\n👤 | Твій ID: {info[0]}\n👑 | Рівень доступу: {accessname}\n\n")
    except Exception as e:
    	await message.answer(e)



@dp.message_handler(content_types=['text'], state=None)
async def menu(message: types.Message):
    try:
        cid = message.chat.id
        if message.text == 'Редагувати пошуки ✏️':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            new_search = types.KeyboardButton('Додати пошук ➕')
            del_search = types.KeyboardButton('Видалити пошук ❌')
            markup.add(new_search, del_search)
            await message.answer(f"Окей, ти хочеш редагувати свої пошуки\n\nТи бажаєш додати новий чи видалити існуючий пошук?", reply_markup= markup)
        elif message.text == 'Список пошуків 🔍':
            sql.execute(f"SELECT * FROM searches")
            searches = sql.fetchall()
            answer_text = ''
            for i in searches:
                answer_text += f'{i[0]}. {i[1]}\n\n'
            await message.answer(answer_text)
        elif message.text == 'Додати пошук ➕':
            await FSMAdmin.add_search.set()
            await message.answer('Введи новий пошук')
        elif message.text == 'Видалити пошук ❌':
            await FSMdel.del_search.set()
            await message.answer('Введи ID пошуку який треба видалити')


    except Exception as e:
        bot.send_message(cid, e)

@dp.message_handler(content_types=['text'], state=FSMAdmin.add_search)
async def gender_add(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_search'] = message.text
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        rmk.add(types.KeyboardButton('Чоловічий'), types.KeyboardButton('Жіночий'), types.KeyboardButton('Обидва'))
        await FSMAdmin.next()
        await message.answer('Оберіть який одяг боту слід відслідковувати:', reply_markup=rmk)


@dp.message_handler(content_types=['text'], state=FSMAdmin.add_gender)
async def approve_add(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_gender'] = message.text
        rmk = types.InlineKeyboardMarkup()
        add_yes = types.InlineKeyboardButton(text='✅', callback_data='add_yes')
        add_no = types.InlineKeyboardButton(text='❌', callback_data='add_no')
        rmk.add(add_yes, add_no)
        await message.answer(f"Назва: {data['add_search']}\nСтать: {data['add_gender']}\n\nТи дійсно бажаєш додати цей пошук?", reply_markup=rmk)

@dp.callback_query_handler(lambda call: call.data == 'add_yes' or call.data == 'add_no', state=FSMAdmin.add_gender)
async def add_search_result(call: types.CallbackQuery, state: FSMContext):
    try:
        if call.data == 'add_yes':
            async with state.proxy() as data:
                sql.execute(f"INSERT INTO searches (search, gender) VALUES ('{data['add_search']}', '{data['add_gender']}')")
                db.commit()
                json_name = data['add_search'].replace(' ','').lower().strip()
                if not os.path.exists(f'searches/'):
                    Path(f'searches/').mkdir(parents=True, exist_ok=True)
                open(f'searches/{json_name}.json', 'w').close()
                await call.message.answer(f"✅ | Ти успішно додав пошук {data['add_search']}")
                await state.finish()
        elif call.data == 'add_no':
            await bot.delete_message(call.message.chat.id, call.message.message_id-0)
            await call.answer(f"🚫 | Ти відмінив додавання пошуку")
            await state.finish()
        await bot.answer_callback_query(callback_query_id=call.id)

    except Exception as e:
        print(e)

@dp.message_handler(content_types=['text'], state=FSMdel.del_search)
async def search_del(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['del_search'] = int(message.text)
            rmk = types.InlineKeyboardMarkup()
            add_yes = types.InlineKeyboardButton(text='✅', callback_data='del_yes')
            add_no = types.InlineKeyboardButton(text='❌', callback_data='del_no')
            rmk.add(add_yes, add_no)
            sql.execute(f"SELECT * FROM searches WHERE id = {data['del_search']}")
            global item_del
            item_del = sql.fetchone()[1]
            await message.answer(f"Ти дійсно бажаєш видалити {item_del} з відстежування?", reply_markup=rmk)
    except:
        await state.finish()
        await start(message)



@dp.callback_query_handler(lambda call: call.data == 'del_yes' or call.data == 'del_no', state=FSMdel.del_search)
async def del_search_result(call: types.CallbackQuery, state: FSMContext):
    try:
        if call.data == 'del_yes':
            async with state.proxy() as data:
                sql.execute(f"SELECT * FROM searches WHERE id = {data['del_search']}")
                search_name = sql.fetchone()[1]
                sql.execute(f"DELETE FROM searches WHERE id = {data['del_search']}")
                db.commit()
                await call.message.answer(f"✅ | Ти успішно видалив пошук {item_del}")
                await state.finish()
            name_search = search_name.replace(' ','').lower().strip()
            for file in glob.glob(f'photos/{name_search}/*'):
                os.remove(file)
            os.rmdir(os.path.abspath(f'photos/{name_search}'))
            os.remove(f'searches/{name_search}.json')
            
            
        elif call.data == 'del_no':
            await bot.delete_message(call.message.chat.id, call.message.message_id-0)
            await call.answer(f"🚫 | Ти відмінив видалення пошуку")
            await state.finish()
        await bot.answer_callback_query(callback_query_id=call.id)
    
    except Exception as e:
        print(e)


async def get_data(url):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument(f'user-agent={useragent.random}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.headless = True

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url=url)

        with open("source-page.html", 'w') as file:
            file.write(driver.page_source)
        await get_items("source-page.html")


    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


async def get_items(file_path):
    try:
        with open(file_path) as file:
            src = file.read()

        soup = BeautifulSoup(src, "lxml")
        items_divs = soup.find('ul', class_='b-catalog b-catalog_max-columns_4 b-block').find_all("li", class_='b-catalog__item')

        ads_list = []

        for item in items_divs:
            item_price = item.find("div", class_='b-tile-item__info').find("div", class_='b-tile-item__price-holder').find("div", class_ ='b-tile-item__price').text.strip()
            item_name = item.find("div", class_='b-tile-item__info').find("a").text.strip()
            item_link = item.find("div", class_='b-tile-item__info').find("a").get("href")
            item_link = f'https://shafa.ua{item_link}'
            item_size = item.find("div", class_='b-tile-item__info').find("span", class_='b-tile-item__size').text.strip()
            item_image = item.find('img')['data-src']
            folder_name = item_search.replace(' ','').lower().strip()
            if not os.path.exists(f'photos/{folder_name}/'):
                Path(f'photos/{folder_name}/').mkdir(parents=True, exist_ok=True)
            image_name = item_image.split('/')[3]
            path = f'photos/{folder_name}/{image_name}.png'
        

            ads_list.append(
                {
                    "item_name": item_name,
                    "item_price": item_price,
                    "item_size": item_size,
                    "item_link": item_link,
                    "item_path": path,
                    "item_image": item_image
                }
            )

        search_item = item_search.replace(' ','').lower()
            
        with open (f'searches/{search_item}.json', 'r') as f:
            ads = json.load(f)


        for ad in ads_list:
            if ad not in ads:
                path = ad['item_path']
                item_image = ad['item_image']
                urlretrieve(item_image, path)
                with open (f'searches/{search_item}.json', 'r') as check:
                    file_len = json.load(check)
                    if len(file_len) > 192:
                        with open (f'searches/{search_item}.json', 'w+') as result:
                            del file_len[:48]
                            json.dump(file_len, result, indent=4, ensure_ascii=False)


                with open (f'searches/{search_item}.json', 'r+') as f1:
                    file_data = json.load(f1)
                    file_data.append(ad)
                    f1.seek(0)
                    json.dump(file_data, f1, indent = 4, ensure_ascii=False)
                            

                sql.execute(f"SELECT * FROM users WHERE access = 1")
                admins = sql.fetchall()
                for i in admins:
                    with open (f"{ad['item_path']}", 'rb') as photo:
                        await bot.send_photo(i[0], photo, caption=f"Назва:{ad['item_name']}\nЦіна:{ad['item_price']}\nРозмір:{ad['item_size']}\n\n{ad['item_link']}")
                os.remove(ad['item_path'])
        

        await asyncio.sleep(random.randrange(2,7))
    

    except json.JSONDecodeError:
        with open (f'searches/{search_item}.json', 'w') as f3:
            json.dump(ads_list, f3, indent=4, ensure_ascii=False)


async def main(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        sql.execute(f'SELECT * FROM searches')
        searches = sql.fetchall()
        if len(searches) == 0:
            await asyncio.sleep(60)
        else:
            
            for i in searches:
                global item_search
                item_search = i[1]
                if i[2] == 'Чоловічий':
                    await get_data(f"https://shafa.ua/men?search_text={item_search.replace(' ','%20')}&conditions=2&conditions=3&conditions=4&conditions=5&sort=4")
                elif i[2] == 'Жіночий':
                    await get_data(f"https://shafa.ua/women?search_text={item_search.replace(' ','%20')}&conditions=2&conditions=3&conditions=4&conditions=5&sort=4")
                else:
                    await get_data(f"https://shafa.ua/men?search_text={item_search.replace(' ','%20')}&conditions=2&conditions=3&conditions=4&conditions=5&sort=4")
                    await get_data(f"https://shafa.ua/women?search_text={item_search.replace(' ','%20')}&conditions=2&conditions=3&conditions=4&conditions=5&sort=4")



async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main(10))
    executor.start_polling(dp, skip_updates=True, on_shutdown=shutdown)