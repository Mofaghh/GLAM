import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import (
    BOT_TOKEN,
    GROUP_CHAT_ID,
    ADMIN_IDS,
    WEBHOOK_URL,
    WEBHOOK_PATH,
    PORT,
)
import db

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


class OrderStates(StatesGroup):
    waiting_description = State()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🟣 Заказать скин")],
        [KeyboardButton(text="📋 Мои заказы")],
    ],
    resize_keyboard=True,
)

close_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Завершить заказ", callback_data="close_order")]
    ]
)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Это бот студии скинов.\n"
        "Нажми кнопку ниже, чтобы оформить заказ.",
        reply_markup=main_keyboard,
    )


@dp.message(F.text == "📋 Мои заказы")
async def my_orders(message: Message):
    orders = db.get_active_orders()
    user_orders = [o for o in orders if o["user_id"] == message.from_user.id]
    if not user_orders:
        await message.answer("У тебя пока нет активных заказов.")
        return

    text = "📋 Твои активные заказы:\n\n"
    for o in user_orders:
        text += f"• Заказ #{o['id']}\n  {o['description'][:200]}\n\n"
    await message.answer(text)


@dp.message(F.text == "🟣 Заказать скин")
async def start_order(message: Message, state: FSMContext):
    if db.get_order_by_user(message.from_user.id):
        await message.answer("⚠️ У тебя уже есть активный заказ. Дождись его завершения.")
        return

    await state.set_state(OrderStates.waiting_description)
    await message.answer(
        "📝 Опиши скин, который хочешь:\n"
        "— Персонаж / идея\n"
        "— Стиль (классика, 3D, аниме и т.д.)\n"
        "— Референсы можно прислать картинкой\n\n"
        "Просто напиши описание сюда 👇"
    )


@dp.message(OrderStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    user = message.from_user

    topic = await bot.create_forum_topic(
        chat_id=GROUP_CHAT_ID,
        name=f"Заказ | {user.first_name} (@{user.username or user.id})",
        icon_color=0xCB86DB,
    )
    topic_id = topic.message_thread_id

    description = message.text or message.caption or "Описание в виде фото"
    db.create_order(
        user_id=user.id,
        username=user.username or str(user.id),
        description=description,
        topic_id=topic_id,
    )

    await bot.send_message(
        chat_id=GROUP_CHAT_ID,
        message_thread_id=topic_id,
        text=(
            f"🆕 <b>Новый заказ!</b>\n\n"
            f"👤 Заказчик: @{user.username or user.id}\n"
            f"📝 Описание:\n{description}\n\n"
            f"Пишите сюда — я передам заказчику."
        ),
        reply_markup=close_button,
    )

    await bot.copy_message(
        chat_id=GROUP_CHAT_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        message_thread_id=topic_id,
    )

    await message.answer(
        "✅ Заказ создан! Скин-мейкер скоро ответит.\n"
        "Пиши сюда — я передам сообщение в рабочий чат."
    )
    await state.clear()


async def finish_order(topic_id: int, by_user_id: int) -> None:
    if ADMIN_IDS and by_user_id not in ADMIN_IDS:
        return False
    order = db.get_order_by_topic(topic_id)
    if not order:
        return None

    try:
        await bot.delete_forum_topic(chat_id=GROUP_CHAT_ID, message_thread_id=topic_id)
    except Exception as e:
        logging.warning(f"Не удалось удалить тему: {e}")

    db.delete_order(topic_id)

    try:
        await bot.send_message(
            chat_id=order["user_id"],
            text="🎉 Твой заказ завершён! Спасибо за обращение.",
        )
    except Exception:
        pass
    return True


@dp.message(Command("done"), F.chat.id == GROUP_CHAT_ID, F.message_thread_id)
async def close_order_cmd(message: Message):
    result = await finish_order(message.message_thread_id, message.from_user.id)
    if result is False:
        await message.answer("⛔ Только админ/мейкер может завершить заказ.")
    elif result is None:
        await message.answer("Заказ не найден.")


@dp.callback_query(F.data == "close_order")
async def close_order_callback(callback: CallbackQuery):
    topic_id = callback.message.message_thread_id
    result = await finish_order(topic_id, callback.from_user.id)
    if result is True:
        await callback.answer("Заказ завершён и очищен ✅")
    elif result is False:
        await callback.answer("⛔ Нет прав для завершения", show_alert=True)
    else:
        await callback.answer("Заказ не найден", show_alert=True)


@dp.message(F.chat.id == GROUP_CHAT_ID, F.message_thread_id, ~F.text.startswith("/"))
async def relay_to_customer(message: Message):
    order = db.get_order_by_topic(message.message_thread_id)
    if not order:
        return
    if message.from_user.is_bot or message.from_user.id == order["user_id"]:
        return

    try:
        await bot.copy_message(
            chat_id=order["user_id"],
            from_chat_id=GROUP_CHAT_ID,
            message_id=message.message_id,
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить заказчику: {e}")


@dp.message(F.chat.type == "private", ~F.text.startswith("/"))
async def relay_to_group(message: Message):
    order = db.get_order_by_user(message.from_user.id)
    if not order:
        return

    try:
        await bot.copy_message(
            chat_id=GROUP_CHAT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=order["topic_id"],
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить в группу: {e}")


async def on_startup() -> None:
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")


def health(request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def main() -> None:
    if WEBHOOK_URL:
        logging.info("Бот запущен в webhook-режиме: %s", WEBHOOK_URL)
        app = web.Application()
        app.add_routes([web.route("/", health), web.route("/health", health)])
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        dp.startup.register(on_startup)
        web.run_app(app, host="0.0.0.0", port=PORT)
    else:
        logging.info("Бот запущен в режиме поллинга!")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
