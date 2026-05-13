import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

logging.basicConfig(level=logging.INFO)

# =========================================
# КОНФІГУРАЦІЯ
# =========================================
TOKEN = "8543670155:AAH83DxUCSmn5Nx4D9wm8N_YZMciucAjnWI"

BASE_DIR = Path(__file__).resolve().parent
START_PHOTO = BASE_DIR / "picture.png"
FULL_TEAM_PHOTO = BASE_DIR / "picture2.png"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Списки
mujiki = []       # Основний склад (max 5)
bench = []        # Запасні (без ліміту)
status_list = []  # Ті, хто злив
MAX_PLAYERS = 5

game_time = None
chat_id_global = None
reminder_sent = False
team_completed = False

# =========================================
# КЛАВІАТУРА
# =========================================
def get_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Join / Reserve", callback_data="join")],
            [InlineKeyboardButton(text="➖ Leave", callback_data="leave")]
        ]
    )

# =========================================
# ГЕНЕРАТОР ТЕКСТУ
# =========================================
def build_text():
    text = "🎮 **ЛОБІ**\n\n"

    # ОСНОВА
    text += f"👨 **Основний склад ({len(mujiki)}/{MAX_PLAYERS})**\n"
    if mujiki:
        text += "\n".join([f"• {u[1]}" for u in mujiki])
    else:
        text += "— шукаємо таланти"

    # ЗАПАСНІ
    if bench:
        text += f"\n\n⏳ **Запасні ({len(bench)})**\n"
        text += "\n".join([f"• {u[1]}" for u in bench])

    # ЗЛИЛИСЯ
    if status_list:
        text += "\n\n🏳️ Статус нетрадиційної орієнтації підтверджено:\n"
        text += "\n".join([f"🏳️ {u[1]}" for u in status_list])

    if game_time:
        text += f"\n\n⏰ Час гри: {game_time.strftime('%H:%M')}"

    if len(mujiki) == MAX_PLAYERS:
        text += "\n\n🔥 **ОСНОВНА П'ЯТІРКА В ЗБОРІ!**"

    return text

# =========================================
# HANDLERS
# =========================================
@dp.message(F.text.startswith("/play"))
async def play(message: types.Message):
    global game_time, chat_id_global, reminder_sent, team_completed
    
    mujiki.clear()
    bench.clear()
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
        await message.answer("❌ Фото не знайдено.")
        return

    await message.answer_photo(
        FSInputFile(START_PHOTO),
        caption=build_text(),
        reply_markup=get_keyboard()
    )

@dp.callback_query()
async def callbacks(callback: types.CallbackQuery):
    global team_completed

    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    user_data = (user_id, user_name)
    
    action_made = False

    # --- JOIN / RESERVE ---
    if callback.data == "join":
        # Перевірка чи вже є десь
        if any(u[0] == user_id for u in mujiki) or any(u[0] == user_id for u in bench):
            await callback.answer("Ти вже у черзі!")
            return
        
        # Якщо є місце в основі
        if len(mujiki) < MAX_PLAYERS:
            mujiki.append(user_data)
        # Якщо місця немає — в запас
        else:
            bench.append(user_data)
            await callback.answer("Місць немає, ти в запасі!", show_alert=False)
        
        # Видаляємо з "leave", якщо був там
        status_list[:] = [u for u in status_list if u[0] != user_id]
        action_made = True

    # --- LEAVE ---
    elif callback.data == "leave":
        # Вихід з основи
        if any(u[0] == user_id for u in mujiki):
            mujiki[:] = [u for u in mujiki if u[0] != user_id]
            
            # АВТО-ЗАМІНА: Беремо першого із запасних
            if bench:
                lucky_guy = bench.pop(0)
                mujiki.append(lucky_guy)
                await callback.message.answer(f"⚡️ {lucky_guy[1]} переходить в основний склад!")
            else:
                team_completed = False
            
            if not any(u[0] == user_id for u in status_list):
                status_list.append(user_data)
            action_made = True

        # Вихід із запасу
        elif any(u[0] == user_id for u in bench):
            bench[:] = [u for u in bench if u[0] != user_id]
            if not any(u[0] == user_id for u in status_list):
                status_list.append(user_data)
            action_made = True
        else:
            await callback.answer("Тебе немає в списках.")
            return

    # --- UPDATE ---
    if action_made:
        try:
            if len(mujiki) == MAX_PLAYERS and not team_completed:
                team_completed = True
                photo = FULL_TEAM_PHOTO if FULL_TEAM_PHOTO.exists() else START_PHOTO
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=FSInputFile(photo), caption=build_text()),
                    reply_markup=get_keyboard()
                )
            else:
                await callback.message.edit_caption(
                    caption=build_text(),
                    reply_markup=get_keyboard()
                )
        except TelegramBadRequest:
            pass

    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
