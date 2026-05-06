import asyncio
from pathlib import Path
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile

# =========================================
# TOKEN
# =========================================
TOKEN = "8543670155:AAHu_-UUgWq5ljBZ4g1F-HiHEcg13w5nA-g"

# =========================================
# SETTINGS
# =========================================
MAX_PLAYERS = 5

PHOTO_PATH = Path(r"C:\Users\rog\Desktop\game_bot\picture2.png")
FULL_TEAM_PHOTO = Path(r"C:\Users\rog\Desktop\game_bot\picture.png")

# =========================================
# BOT INIT
# =========================================
bot = Bot(token=TOKEN)
dp = Dispatcher()

players = []
leave_users = []

team_completed = False

game_time = None
chat_id_global = None
reminder_sent = False

game_task = None  # 🔥 ДОБАВЛЕНО


# =========================================
# KEYBOARD
# =========================================
def get_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Join", callback_data="join")],
            [InlineKeyboardButton(text="➖ Leave", callback_data="leave")]
        ]
    )


# =========================================
# TEXT BUILDER
# =========================================
def build_text():
    text = f"🎮 Гравці ({len(players)}/{MAX_PLAYERS})\n\n"

    if players:
        text += "\n".join([f"• {p}" for p in players])
    else:
        text += "Поки нікого немає"

    if game_time:
        text += f"\n\n⏰ Час гри: {game_time.strftime('%H:%M')}"

    if len(players) == MAX_PLAYERS:
        text += "\n\n🔥 ТІМ ЗІБРАНО!"

    if leave_users:
        text += "\n\n🏳️🏳️‍🌈 Статус нетрадиційної орієнтації:\n"
        text += "\n".join([f"🏳️ {u}" for u in leave_users])

    return text


# =========================================
# 🔥 GAME TIMER (ДОДАНО)
# =========================================
async def game_manager(chat_id, message_id):
    global team_completed

    print("GAME TIMER STARTED")

    try:
        # =========================
        # 10 хв → UPDATE 1
        # =========================
        await asyncio.sleep(10 * 60)

        if len(players) >= MAX_PLAYERS:
            return

        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=build_text() + "\n\n🔄 Оновлення 1/2 (10 хв)",
            reply_markup=get_keyboard()
        )

        print("UPDATE 1 DONE")

        # =========================
        # 10 хв → UPDATE 2
        # =========================
        await asyncio.sleep(10 * 60)

        if len(players) >= MAX_PLAYERS:
            return

        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=build_text() + "\n\n🔄 Оновлення 2/2 (20 хв)",
            reply_markup=get_keyboard()
        )

        print("UPDATE 2 DONE")

        # =========================
        # 5 хв → FINAL
        # =========================
        await asyncio.sleep(5 * 60)

        await bot.send_message(
            chat_id,
            "⏳ Час вийшов!\n\n" + build_text()
        )

        print("FINAL SENT")

    except Exception as e:
        print("GAME TIMER ERROR:", e)


# =========================================
# REMINDER TASK
# =========================================
async def reminder_checker():
    global reminder_sent, game_time, chat_id_global

    while True:
        await asyncio.sleep(20)

        if not game_time or not chat_id_global:
            continue

        now = datetime.now()
        game_dt = datetime.combine(now.date(), game_time)

        if now > game_dt:
            continue

        if now >= game_dt - timedelta(minutes=10) and not reminder_sent:

            reminder_sent = True

            text = "⏰ Нагадування!\nГра почнеться через 10 хв!"

            if players:
                text += "\n\nГравці:\n" + "\n".join(players)

            await bot.send_message(chat_id_global, text)


# =========================================
# /PLAY
# =========================================
@dp.message()
async def play(message: types.Message):

    global game_time, chat_id_global, reminder_sent, team_completed, game_task

    if message.text.startswith("/play"):

        players.clear()
        leave_users.clear()
        team_completed = False
        reminder_sent = False

        chat_id_global = message.chat.id

        parts = message.text.split()

        game_time = None

        if len(parts) > 1:
            try:
                game_time = datetime.strptime(parts[1], "%H:%M").time()
            except ValueError:
                await message.answer("❌ Формат: /play 20:00")
                return

        if not PHOTO_PATH.exists():
            await message.answer("❌ Фото не знайдено")
            return

        photo = FSInputFile(PHOTO_PATH)

        msg = await message.answer_photo(
            photo=photo,
            caption="🎮 Збираємо тім (0/5)",
            reply_markup=get_keyboard()
        )

        # 🔥 ЗАПУСК ТАЙМЕРА
        game_task = asyncio.create_task(
            game_manager(message.chat.id, msg.message_id)
        )


# =========================================
# CALLBACKS
# =========================================
@dp.callback_query()
async def callbacks(callback: types.CallbackQuery):

    global team_completed

    user = callback.from_user.first_name

    if callback.data == "join":

        if user in players:
            await callback.answer("Вже в команді 😎", show_alert=True)
            return

        if len(players) < MAX_PLAYERS:
            players.append(user)

            if user in leave_users:
                leave_users.remove(user)

        else:
            await callback.answer("❌ Команда повна", show_alert=True)
            return

    elif callback.data == "leave":

        if user in players:
            players.remove(user)
            await callback.message.answer(f"❌ {user} вийшов")

        if user not in leave_users:
            leave_users.append(user)

        team_completed = False

    try:
        await callback.message.edit_caption(
            caption=build_text(),
            reply_markup=get_keyboard()
        )
    except:
        pass

    if len(players) == MAX_PLAYERS and not team_completed:

        team_completed = True

        if FULL_TEAM_PHOTO.exists():
            await callback.message.answer_photo(
                FSInputFile(FULL_TEAM_PHOTO),
                caption="🔥 Команда зібрана!"
            )
        else:
            await callback.message.answer("🔥 Команда зібрана!")

    await callback.answer()


# =========================================
# START
# =========================================
async def main():
    print("Бот запущений...")

    asyncio.create_task(reminder_checker())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())