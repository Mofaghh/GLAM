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
    waiting_service = State()
    waiting_description = State()


SERVICES = {
    "premium": {
        "label": "Премиум скин",
        "short": "Премиум",
        "price": 349,
        "desc": "Работают все скин-мейкеры студии одновременно. Бесконечный спектр идей и доработок. Максимальный уровень детализации.",
    },
    "classic": {
        "label": "Обычный скин",
        "short": "Обычный",
        "price": 149,
        "desc": "Индивидуальная проработка скина одним скин-мейкером студии. Качественный результат по доступной цене.",
    },
    "clothes": {
        "label": "Одежда на скин",
        "short": "Одежда",
        "price": 119,
        "desc": "Создание уникальной одежды поверх существующего скина. Детали, аксессуары, стилистика под ваш запрос.",
    },
    "reshade": {
        "label": "Решейд скина",
        "short": "Решейд",
        "price": 89,
        "desc": "Полная переработка и улучшение существующего скина. Обновление стиля, исправление ошибок, новая жизнь вашего скина.",
    },
}

STUDIO_NAME = "GLAM СТУДИЯ"

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Заказать услугу")],
        [KeyboardButton(text="Прайс-лист")],
        [KeyboardButton(text="Мои заказы")],
    ],
    resize_keyboard=True,
)

service_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=f"Премиум скин — {SERVICES['premium']['price']} руб.", callback_data="svc_premium")],
        [InlineKeyboardButton(text=f"Обычный скин — {SERVICES['classic']['price']} руб.", callback_data="svc_classic")],
        [InlineKeyboardButton(text=f"Одежда на скин — {SERVICES['clothes']['price']} руб.", callback_data="svc_clothes")],
        [InlineKeyboardButton(text=f"Решейд скина — {SERVICES['reshade']['price']} руб.", callback_data="svc_reshade")],
    ]
)

close_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Завершить заказ", callback_data="close_order")]
    ]
)


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    payload = ""
    if message.text and message.text.startswith("/start"):
        payload = message.text[len("/start"):].strip()

    if payload.startswith("calc_"):
        try:
            parts = payload.split("_")
            base = parts[1] if len(parts) > 1 else "classic"
            adds = parts[2:] if len(parts) > 2 else []
            svc = SERVICES.get(base, SERVICES["classic"])
            lines = [f"• {svc['label']} — {svc['price']} руб."]
            total = svc["price"]
            for a in adds:
                if a in SERVICES:
                    lines.append(f"• {SERVICES[a]['label']} — {SERVICES[a]['price']} руб.")
                    total += SERVICES[a]["price"]
                elif a == "cape":
                    lines.append("• Плащ — 99 руб.")
                    total += 99
            if db.get_order_by_user(message.from_user.id):
                await message.answer("У вас уже есть активный заказ. Дождитесь его завершения.")
                return
            await state.set_state(OrderStates.waiting_description)
            await state.update_data(service_type=base, addons=adds)
            await message.answer(
                "Вы собрали заказ на сайте:\n" + "\n".join(lines) +
                f"\n\nИтого: {total} руб.\n\nОсталось только описать, что вы хотите — "
                "идея, детали, стиль и референсы (можно прикрепить фото). Чем подробнее ТЗ — тем точнее результат.",
            )
            return
        except Exception as e:
            logging.warning(f"calc deep link parse failed: {e}")

    await message.answer(
        f"Добро пожаловать в студию {STUDIO_NAME}.\n"
        "Мы создаём уникальные скины для Minecraft. Выберите действие ниже.",
        reply_markup=main_keyboard,
    )


@dp.message(F.text == "Мои заказы")
async def my_orders(message: Message):
    orders = db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("У вас пока нет заказов.")
        return

    text = "Ваши заказы:\n\n"
    for o in orders:
        svc = SERVICES.get(o.get("service_type"), {"label": "Услуга", "price": ""})
        created = str(o.get("created_at", ""))[:10]
        status = "в работе" if o.get("status") == "active" else "завершён"
        price = f"{svc['price']} руб." if svc.get("price") else ""
        text += f"• #{o['id']} — {svc['label']} ({price})\n  📅 {created} · {status}\n\n"
    await message.answer(text)


@dp.message(F.text == "Прайс-лист")
async def price_list(message: Message):
    text = f"Прайс-лист студии {STUDIO_NAME}:\n\n"
    for svc in SERVICES.values():
        text += (
            f"• {svc['label']} — {svc['price']} руб.\n"
            f"  {svc['desc']}\n\n"
        )
    text += "Для заказа нажмите «Заказать услугу»."
    await message.answer(text)


@dp.message(F.text == "Заказать услугу")
async def start_order(message: Message, state: FSMContext):
    if db.get_order_by_user(message.from_user.id):
        await message.answer("У вас уже есть активный заказ. Дождитесь его завершения.")
        return

    await state.set_state(OrderStates.waiting_service)
    await message.answer(
        "Выберите услугу:", reply_markup=service_keyboard
    )


@dp.callback_query(F.data.startswith("svc_"), OrderStates.waiting_service)
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service_type = callback.data.split("_", 1)[1]
    await state.update_data(service_type=service_type)
    await state.set_state(OrderStates.waiting_description)
    await callback.answer()
    svc = SERVICES[service_type]
    await callback.message.answer(
        f"Отлично, вы выбрали «{svc['label']}» за {svc['price']} руб.\n\n"
        "Теперь распишите, пожалуйста, максимально подробно, что вы хотите увидеть:\n"
        "— Идея и концепция\n"
        "— Детали и элементы\n"
        "— Стиль и цветовая гамма\n"
        "— Референсы (если есть, можно прикрепить фото)\n\n"
        "Чем подробнее ТЗ — тем точнее будет результат."
    )


@dp.message(OrderStates.waiting_service)
async def waiting_service_fallback(message: Message):
    await message.answer(
        "Выберите услугу кнопкой ниже.", reply_markup=service_keyboard
    )


@dp.message(OrderStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    user = message.from_user
    data = await state.get_data()
    service_type = data.get("service_type", "classic")
    svc = SERVICES.get(service_type, SERVICES["classic"])

    topic = await bot.create_forum_topic(
        chat_id=GROUP_CHAT_ID,
        name=f"Заказ | {svc['short']} | {user.first_name} (@{user.username or user.id})",
        icon_color=0xCB86DB,
    )
    topic_id = topic.message_thread_id

    description = message.text or message.caption or "Описание в виде фото"
    db.create_order(
        user_id=user.id,
        username=user.username or str(user.id),
        service_type=service_type,
        description=description,
        topic_id=topic_id,
    )

    await bot.send_message(
        chat_id=GROUP_CHAT_ID,
        message_thread_id=topic_id,
        text=(
            f"Новый заказ!\n\n"
            f"Услуга: {svc['label']} ({svc['price']} руб.)\n"
            f"Заказчик: @{user.username or user.id}\n"
            f"ТЗ:\n{description}\n\n"
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
        "Ваш заказ принят и передан команде. Ожидайте — скин-мейкер свяжется с вами в ближайшее время.\n"
        "Если хотите что-то добавить, просто напишите сюда."
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
            text="Ваш заказ завершён. Спасибо за обращение.",
        )
    except Exception:
        pass
    return True


@dp.message(Command("done"), F.chat.id == GROUP_CHAT_ID, F.message_thread_id)
async def close_order_cmd(message: Message):
    result = await finish_order(message.message_thread_id, message.from_user.id)
    if result is False:
        await message.answer("Только админ или мейкер может завершить заказ.")
    elif result is None:
        await message.answer("Заказ не найден.")


@dp.callback_query(F.data == "close_order")
async def close_order_callback(callback: CallbackQuery):
    topic_id = callback.message.message_thread_id
    result = await finish_order(topic_id, callback.from_user.id)
    if result is True:
        await callback.answer("Заказ завершён и очищен.")
    elif result is False:
        await callback.answer("Нет прав для завершения", show_alert=True)
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


async def receive_order(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "bad json"}, status=400)

    name = str(data.get("name") or "").strip()
    tg = str(data.get("telegram") or "").strip().lstrip("@")
    service = data.get("service") or "classic"
    desc = str(data.get("description") or "").strip()
    ref = str(data.get("reference") or "").strip()

    if not name or not tg or not desc:
        return web.json_response({"ok": False, "error": "missing fields"}, status=400)

    svc = SERVICES.get(service, SERVICES["classic"])
    text = (
        "🟣 Новая заявка с сайта!\n\n"
        f"Услуга: {svc['label']} ({svc['price']} руб.)\n"
        f"Имя: {name}\n"
        f"Telegram: @{tg}\n"
        f"ТЗ: {desc}\n"
        + (f"Референс: {ref}\n" if ref else "")
    )
    try:
        await bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
        return web.json_response({"ok": True})
    except Exception as e:
        logging.warning(f"Order submit failed: {e}")
        return web.json_response({"ok": False, "error": "send failed"}, status=500)


def main() -> None:
    if WEBHOOK_URL:
        logging.info("Бот запущен в webhook-режиме: %s", WEBHOOK_URL)
        app = web.Application()
        app.add_routes([web.get("/", health), web.get("/health", health), web.post("/api/order", receive_order)])
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        dp.startup.register(on_startup)
        web.run_app(app, host="0.0.0.0", port=PORT)
    else:
        logging.info("Бот запущен в режиме поллинга!")
        asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
