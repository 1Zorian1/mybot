import asyncio
from pathlib import Path
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, InputMediaPhoto

# =========================================
# TOKEN
# =========================================
TOKEN = "8543670155:AAHu_-UUgWq5ljBZ4g1F-HiHEcg13w5nA-g"

# =========================================
# PATHS
# =========================================
BASE_DIR = Path(__file__).resolve().parent

START_PHOTO = BASE_DIR / "picture.png"
FULL_TEAM_PHOTO = BASE_DIR / "picture2.png"

# =========================================
# BOT INIT
# =========================================
bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================================
# LISTS (🔥 2 ГРУПИ)
# =========================================
mujiki = []  # Join
status_list = []  # Leave

MAX_PLAYERS = 5

game_time = None
chat_id_global = None
reminder_sent = False
team_completed = False


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
    text = "🎮 ЛОБІ\n\n"

    # =====================
    # МУЖИКИ
    # =====================
    text += f"👨 Мужики ({len(mujiki)})\n"
    text += "\n".join([f"• {u}" for u in mujiki]) if mujiki else "— пусто"

    # =====================
    # STATUS LIST
    # =====================
    if status_list:
        text += "\n\n🏳️ статус нетрадиційної орієнтації підтверджено:\n"
        text += "\n".join([f"🏳️ {u}" for u in status_list])

    if game_time:
        text += f"\n\n⏰ Час гри: {game_time.strftime('%H:%M')}"

    if len(mujiki) == MAX_PLAYERS:
        text += "\n\n🔥 КОМАНДА ЗІБРАНА!"

    return text


# =========================================
# GAME TIMER
# =========================================
async def game_manager(chat_id, message_id):
    try:
        await asyncio.sleep(10 * 60)

        if len(mujiki) >= MAX_PLAYERS:
            return

        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=build_text() + "\n\n🔄 10 хв пройшло",
            reply_markup=get_keyboard()
        )

        await asyncio.sleep(10 * 60)

        if len(mujiki) >= MAX_PLAYERS:
            return

        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=build_text() + "\n\n🔄 20 хв пройшло",
            reply_markup=get_keyboard()
        )

        await asyncio.sleep(5 * 60)

        await bot.send_message(chat_id, "⏳ Час вийшов!\n\n" + build_text())

    except Exception as e:
        print("GAME ERROR:", e)


# =========================================
# REMINDER
# =========================================
async def reminder_checker():
    global reminder_sent, game_time, chat_id_global

    while True:
        await asyncio.sleep(20)

        if not game_time or not chat_id_global:
            continue

        now = datetime.now()
        game_dt = datetime.combine(now.date(), game_time)

        if now >= game_dt - timedelta(minutes=10) and not reminder_sent:
            reminder_sent = True
            await bot.send_message(chat_id_global, "⏰ Гра через 10 хв!")


# =========================================
# /PLAY
# =========================================
@dp.message(F.text.startswith("/play"))
async def play(message: types.Message):

    global game_time, chat_id_global, reminder_sent, team_completed

    mujiki.clear()
    status_list.clear()

    reminder_sent = False
    team_completed = False

    chat_id_global = message.chat.id

    parts = message.text.split()

    game_time = None

    if len(parts) > 1:
        try:
            game_time = datetime.strptime(parts[1], "%H:%M").time()
        except ValueError:
            await message.answer("❌ Формат: /play 20:00")
            return

    if not START_PHOTO.exists():
        await message.answer("❌ START PHOTO не знайдено")
        return

    msg = await message.answer_photo(
        FSInputFile(START_PHOTO),
        caption=build_text(),
        reply_markup=get_keyboard()
    )

    asyncio.create_task(game_manager(message.chat.id, msg.message_id))


# =========================================
# CALLBACKS
# =========================================
@dp.callback_query()
async def callbacks(callback: types.CallbackQuery):

    global team_completed

    user = callback.from_user.first_name

    # =====================
    # JOIN → МУЖИКИ
    # =====================
    if callback.data == "join":

        if user not in mujiki and len(mujiki) < MAX_PLAYERS:
            mujiki.append(user)

        elif len(mujiki) >= MAX_PLAYERS:
            await callback.answer("Команда повна", show_alert=True)
            return

        # якщо був у статусі — прибрати
        if user in status_list:
            status_list.remove(user)

    # =====================
    # LEAVE → STATUS
    # =====================
    elif callback.data == "leave":

        if user in mujiki:
            mujiki.remove(user)

        if user not in status_list:
            status_list.append(user)

    # =====================
    # UPDATE MESSAGE
    # =====================
    try:
        await callback.message.edit_caption(
            caption=build_text(),
            reply_markup=get_keyboard()
        )
    except:
        pass

    # =====================
    # TEAM COMPLETE
    # =====================
    if len(mujiki) == MAX_PLAYERS and not team_completed:

        team_completed = True

        if FULL_TEAM_PHOTO.exists():
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=FSInputFile(FULL_TEAM_PHOTO),
                    caption="🔥 КОМАНДА ЗІБРАНА!"
                ),
                reply_markup=None
            )
        else:
            await callback.message.answer("🔥 КОМАНДА ЗІБРАНА!")

    await callback.answer()


# =========================================
# START
# =========================================
async def main():
    print("🚀 Бот запущений")
    print("START:", START_PHOTO.exists())
    print("FULL:", FULL_TEAM_PHOTO.exists())

    asyncio.create_task(reminder_checker())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
