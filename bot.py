from typing import Text

import config
import logging
import os
from aiogram.utils.markdown import link
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InputFile
from database import Database
from detector import detect_plants

logging.basicConfig(level=logging.INFO)

bot=Bot(token=config.API_TOKEN)
dp=Dispatcher(bot)

db = Database("db.db")

button = KeyboardButton("Почати аналіз")

keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
keyboard.add(button)

@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id)
    await message.answer("Вітаю! Надішліть фото для аналізу якості посіву поля")

@dp.message_handler(commands=['clear'])
async def clear_photos(message: types.Message):
    images = db.user_photos(message.from_user.id)
    if (bool(len(images))):
        for image in images:
            os.remove(f"images/{image[0]}.jpg")
            if os.path.exists(f"images/_{image[0]}.jpg"):
                os.remove(f"images/_{image[0]}.jpg")
        db.clear_user_photos(message.from_user.id)
    await message.answer("Фото видалені ✅", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(commands=['output'])
async def send_predicted_image(message: types.Message):
    images = db.user_photos(message.from_user.id)
    if (bool(len(images))):
        for image in images:
            if os.path.exists(f"images/_{image[0]}.jpg"):
                img = InputFile(f"images/_{image[0]}.jpg", filename = "result.jpg")
                await message.answer_document(img)
    else:
        await message.answer("Відсутні проаналізовані фото ❗️")

@dp.message_handler(commands=['photos'])
async def get_photos(message: types.Message):
    await message.answer(f"Усього завантажено {len(db.user_photos(message.from_user.id))} фото", reply_markup = keyboard)

@dp.message_handler(lambda message: message.text == "Почати аналіз")
async def start_detection(message: types.Message):
    images = db.user_photos(message.from_user.id)

    if (bool(len(images))):
        await message.answer("Фото прийняті в обробку 🔎", reply_markup=ReplyKeyboardRemove())
        total_rows, total_plants, total_empty = detect_plants(images)
        await message.answer(f"Виявлено {total_rows} рядів, серед яких:\n{total_plants} рослин та {total_empty} пустих зон\nЗагальна якість посіву = {round(total_plants/(total_plants + total_empty) * 100, 3)} %" + 
        "\nДля перегляду проаналізованих фото використайте команду /output")
    else:
        await message.answer("Фото відсутні ❗️")

@dp.message_handler(content_types=['photo'])
async def handle_photo(message):
    file_id = message.photo[-1].file_id
    file_unique_id = message.photo[-1].file_unique_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, "images/" + file_unique_id + ".jpg")
    if not db.user_photo_exists(message.from_user.id, file_unique_id):
        db.add_photo(message.from_user.id, file_unique_id)
        await message.answer(f"Успішно додано ✅\nУсього завантажено {len(db.user_photos(message.from_user.id))} фото", reply_markup = keyboard)
    else:
        await message.answer("Фото вже існує ❗️", reply_markup = keyboard)


@dp.message_handler(content_types=['document'])
async def handle_docs_photo(message):
    if message.document.mime_type.startswith("image"):
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        await bot.download_file(file_path, "images/" + file_unique_id + ".jpg")
        db.add_photo(message.from_user.id, file_unique_id)
        await message.answer(f"Успішно додано ✅\nУсього завантажено {len(db.user_photos(message.from_user.id))} фото", reply_markup = keyboard)
    else:
        await message.answer("Фото не розпізнано ❗️", reply_markup = keyboard)

if __name__ == '__main__':

	executor.start_polling(dp, skip_updates=True)