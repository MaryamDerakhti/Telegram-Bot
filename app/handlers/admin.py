from datetime import datetime, timedelta, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import SubscriptionPlan, SupportTicket, User

router = Router()
settings = get_settings()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_set


@router.message(Command("stats"))
async def stats(message: Message, session: AsyncSession) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        return
    users = int(await session.scalar(select(func.count(User.id))) or 0)
    tickets = int(
        await session.scalar(
            select(func.count(SupportTicket.id)).where(
                SupportTicket.is_answered.is_(False)
            )
        )
        or 0
    )
    await message.answer(f"👥 کاربران: {users}\n☎️ تیکت‌های باز: {tickets}")


@router.message(Command("answer"))
async def answer_ticket(message: Message, session: AsyncSession) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("فرمت: /answer TICKET_ID متن پاسخ")
        return

    ticket = await session.get(SupportTicket, int(parts[1]))
    if not ticket:
        await message.answer("تیکت پیدا نشد.")
        return

    user = await session.get(User, ticket.user_id)
    if not user:
        return

    try:
        await message.bot.send_message(
            user.telegram_id,
            f"☎️ پاسخ پشتیبانی:\n\n{parts[2]}",
        )
        ticket.is_answered = True
        await session.commit()
        await message.answer("پاسخ ارسال شد.")
    except Exception:
        await message.answer("ارسال پاسخ ممکن نشد.")


@router.message(Command("vip"))
async def activate_vip(message: Message, session: AsyncSession) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer("فرمت: /vip TELEGRAM_ID DAYS")
        return

    user = await session.scalar(
        select(User).where(User.telegram_id == int(parts[1]))
    )
    if not user:
        await message.answer("کاربر پیدا نشد.")
        return

    days = int(parts[2])
    user.plan = SubscriptionPlan.VIP
    user.vip_until = datetime.now(timezone.utc) + timedelta(days=days)
    await session.commit()
    await message.answer(f"VIP برای {days} روز فعال شد.")
    try:
        await message.bot.send_message(
            user.telegram_id,
            f"💎 اشتراک VIP شما برای {days} روز فعال شد.",
        )
    except Exception:
        pass
