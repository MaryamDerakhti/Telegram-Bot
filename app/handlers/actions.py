from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.keyboards import unblock_keyboard, vip_keyboard
from app.models import AnonymousMessage, Block, User
from app.services import (
    block_sender, get_user_by_telegram_id, report_sender, unblock_sender
)
from app.states import ReplyAnonymous

router = Router()
settings = get_settings()


@router.callback_query(F.data.startswith("reply:"))
async def reply_action(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    message_id = int(callback.data.split(":")[1])
    current = await get_user_by_telegram_id(session, callback.from_user.id)
    item = await session.get(AnonymousMessage, message_id)

    if not current or not item or item.receiver_id != current.id:
        await callback.answer("پیام معتبر نیست.", show_alert=True)
        return

    item.is_read = True
    await session.commit()
    await state.set_state(ReplyAnonymous.waiting_for_reply)
    await state.update_data(message_id=message_id)
    await callback.message.answer("پاسخ ناشناس خود را ارسال کنید:")
    await callback.answer()


@router.callback_query(F.data.startswith("block:"))
async def block_action(callback: CallbackQuery, session: AsyncSession) -> None:
    message_id = int(callback.data.split(":")[1])
    current = await get_user_by_telegram_id(session, callback.from_user.id)
    item = await session.get(AnonymousMessage, message_id)

    if not current or not item or item.receiver_id != current.id:
        await callback.answer("پیام معتبر نیست.", show_alert=True)
        return

    created = await block_sender(session, current.id, item.sender_id)
    text = "فرستنده بلاک شد." if created else "این فرستنده قبلاً بلاک شده است."
    await callback.answer(text, show_alert=True)


@router.callback_query(F.data.startswith("report:"))
async def report_action(callback: CallbackQuery, session: AsyncSession) -> None:
    message_id = int(callback.data.split(":")[1])
    current = await get_user_by_telegram_id(session, callback.from_user.id)
    item = await session.get(AnonymousMessage, message_id)

    if not current or not item or item.receiver_id != current.id:
        await callback.answer("پیام معتبر نیست.", show_alert=True)
        return

    created, _ = await report_sender(
        session, current.id, item.sender_id, item.id
    )
    text = "گزارش ثبت شد." if created else "این پیام را قبلاً گزارش کرده‌اید."
    await callback.answer(text, show_alert=True)


@router.callback_query(F.data == "inbox")
async def inbox(callback: CallbackQuery, session: AsyncSession) -> None:
    current = await get_user_by_telegram_id(session, callback.from_user.id)
    if not current:
        return

    result = await session.scalars(
        select(AnonymousMessage)
        .where(AnonymousMessage.receiver_id == current.id)
        .order_by(AnonymousMessage.created_at.desc())
        .limit(10)
    )
    items = list(result)
    if not items:
        await callback.message.answer("📭 صندوق پیام شما خالی است.")
    else:
        for item in items:
            item.is_read = True
            await callback.message.answer(
                f"📩 {item.text}",
                reply_markup=__import__("app.keyboards", fromlist=["message_actions"]).message_actions(item.id),
            )
        await session.commit()
    await callback.answer()


@router.callback_query(F.data == "score")
async def score(callback: CallbackQuery, session: AsyncSession) -> None:
    current = await get_user_by_telegram_id(session, callback.from_user.id)
    if current:
        await callback.message.answer(f"⭐ امتیاز فعلی شما: {current.score}")
    await callback.answer()


@router.callback_query(F.data == "vip")
async def vip(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "💎 VIP شامل سهمیه ارسال بیشتر و امکانات ویژه است.\n\n"
        "توجه: ارسال پیام به کسی که ربات را Start نکرده، به دلیل محدودیت تلگرام ممکن نیست.",
        reply_markup=vip_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "vip_request")
async def vip_request(callback: CallbackQuery) -> None:
    admin_text = (
        f"درخواست VIP\nTelegram ID: {callback.from_user.id}\n"
        f"Username: @{callback.from_user.username or '-'}"
    )
    for admin_id in settings.admin_id_set:
        try:
            await callback.bot.send_message(admin_id, admin_text)
        except Exception:
            pass
    await callback.answer("درخواست برای مدیریت ارسال شد.", show_alert=True)


@router.callback_query(F.data == "blocked_list")
async def blocked_list(callback: CallbackQuery, session: AsyncSession) -> None:
    current = await get_user_by_telegram_id(session, callback.from_user.id)
    if not current:
        return
    rows = await session.execute(
        select(Block.blocked_id, User.first_name)
        .join(User, User.id == Block.blocked_id)
        .where(Block.blocker_id == current.id)
    )
    items = [(row[0], row[1] or "کاربر") for row in rows.all()]
    if not items:
        await callback.message.answer("لیست بلاک شما خالی است.")
    else:
        await callback.message.answer(
            "کاربران بلاک‌شده:",
            reply_markup=unblock_keyboard(items),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("unblock:"))
async def unblock_action(callback: CallbackQuery, session: AsyncSession) -> None:
    blocked_id = int(callback.data.split(":")[1])
    current = await get_user_by_telegram_id(session, callback.from_user.id)
    if current and await unblock_sender(session, current.id, blocked_id):
        await callback.answer("کاربر آنبلاک شد.", show_alert=True)
    else:
        await callback.answer("موردی پیدا نشد.", show_alert=True)
