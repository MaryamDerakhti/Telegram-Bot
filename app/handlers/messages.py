from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import main_menu, message_actions
from app.models import User
from app.services import (
    add_score, can_send, create_message, get_user_by_telegram_id, is_blocked
)
from app.states import ReplyAnonymous, SendAnonymous

router = Router()


@router.message(SendAnonymous.waiting_for_message)
async def receive_anonymous_text(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.from_user or not message.text:
        await message.answer("لطفاً فقط یک پیام متنی ارسال کنید.")
        return

    text = message.text.strip()
    if not text or len(text) > 3000:
        await message.answer("متن پیام باید بین ۱ تا ۳۰۰۰ کاراکتر باشد.")
        return

    sender = await get_user_by_telegram_id(session, message.from_user.id)
    data = await state.get_data()
    receiver_id = data.get("receiver_id")
    receiver = await session.get(User, receiver_id)

    if not sender or not receiver:
        await state.clear()
        await message.answer("کاربر مقصد پیدا نشد.", reply_markup=main_menu())
        return

    allowed, error = await can_send(session, sender)
    if not allowed:
        await message.answer(error)
        return

    if await is_blocked(session, sender.id, receiver.id):
        await state.clear()
        await message.answer(
            "امکان ارسال پیام به این کاربر وجود ندارد.",
            reply_markup=main_menu(),
        )
        return

    item = await create_message(session, sender.id, receiver.id, text)
    await add_score(session, sender, 1, "ارسال پیام")

    try:
        await message.bot.send_message(
            receiver.telegram_id,
            f"📩 پیام ناشناس جدید:\n\n{text}",
            reply_markup=message_actions(item.id),
        )
    except Exception:
        await state.clear()
        await message.answer(
            "پیام ذخیره شد، اما اعلان برای دریافت‌کننده ارسال نشد؛ احتمالاً ربات را مسدود کرده است.",
            reply_markup=main_menu(),
        )
        return

    await state.clear()
    await message.answer("✅ پیام با موفقیت ارسال شد.", reply_markup=main_menu())


@router.message(ReplyAnonymous.waiting_for_reply)
async def receive_reply(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.from_user or not message.text:
        await message.answer("لطفاً پاسخ متنی ارسال کنید.")
        return

    user = await get_user_by_telegram_id(session, message.from_user.id)
    data = await state.get_data()
    original_id = data.get("message_id")
    original = await session.get(__import__("app.models", fromlist=["AnonymousMessage"]).AnonymousMessage, original_id)

    if not user or not original or original.receiver_id != user.id:
        await state.clear()
        await message.answer("پیام اصلی معتبر نیست.", reply_markup=main_menu())
        return

    sender = await session.get(User, original.sender_id)
    if not sender:
        await state.clear()
        return

    reply = await create_message(
        session,
        sender_id=user.id,
        receiver_id=sender.id,
        text=message.text.strip(),
        parent_id=original.id,
    )
    try:
        await message.bot.send_message(
            sender.telegram_id,
            f"↩️ پاسخ ناشناس به پیام شما:\n\n{message.text.strip()}",
            reply_markup=message_actions(reply.id),
        )
        await message.answer("✅ پاسخ ارسال شد.", reply_markup=main_menu())
    except Exception:
        await message.answer(
            "ارسال پاسخ ممکن نشد؛ کاربر احتمالاً ربات را مسدود کرده است.",
            reply_markup=main_menu(),
        )
    await state.clear()
