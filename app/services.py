from __future__ import annotations

from datetime import datetime, time, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import (
    AnonymousMessage, Block, Report, ScoreTransaction,
    SubscriptionPlan, User, UserStatus
)

settings = get_settings()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str,
) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user:
        user.username = username
        user.first_name = first_name
    else:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )
        session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> User | None:
    return await session.scalar(
        select(User).where(User.telegram_id == telegram_id)
    )


def is_vip(user: User) -> bool:
    if user.plan != SubscriptionPlan.VIP:
        return False
    return user.vip_until is None or user.vip_until > datetime.now(timezone.utc)


async def daily_sent_count(session: AsyncSession, user_id: int) -> int:
    now = datetime.now(timezone.utc)
    start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    return int(
        await session.scalar(
            select(func.count(AnonymousMessage.id)).where(
                AnonymousMessage.sender_id == user_id,
                AnonymousMessage.created_at >= start,
            )
        )
        or 0
    )


async def can_send(session: AsyncSession, sender: User) -> tuple[bool, str]:
    if sender.status == UserStatus.SUSPENDED:
        return False, "حساب شما به دلیل گزارش‌های متعدد تعلیق شده است."

    limit = settings.vip_daily_limit if is_vip(sender) else settings.free_daily_limit
    count = await daily_sent_count(session, sender.id)
    if count >= limit:
        return False, f"سهمیه امروز شما تمام شده است ({limit} پیام)."
    return True, ""


async def is_blocked(
    session: AsyncSession, sender_id: int, receiver_id: int
) -> bool:
    block_id = await session.scalar(
        select(Block.id).where(
            Block.blocker_id == receiver_id,
            Block.blocked_id == sender_id,
        )
    )
    return block_id is not None


async def create_message(
    session: AsyncSession,
    sender_id: int,
    receiver_id: int,
    text: str,
    parent_id: int | None = None,
) -> AnonymousMessage:
    message = AnonymousMessage(
        sender_id=sender_id,
        receiver_id=receiver_id,
        text=text,
        parent_id=parent_id,
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def add_score(
    session: AsyncSession, user: User, amount: int, reason: str
) -> None:
    user.score += amount
    session.add(ScoreTransaction(user_id=user.id, amount=amount, reason=reason))
    await session.commit()


async def block_sender(
    session: AsyncSession, blocker_id: int, blocked_id: int
) -> bool:
    session.add(Block(blocker_id=blocker_id, blocked_id=blocked_id))
    try:
        await session.commit()
        return True
    except IntegrityError:
        await session.rollback()
        return False


async def unblock_sender(
    session: AsyncSession, blocker_id: int, blocked_id: int
) -> bool:
    item = await session.scalar(
        select(Block).where(
            Block.blocker_id == blocker_id,
            Block.blocked_id == blocked_id,
        )
    )
    if not item:
        return False
    await session.delete(item)
    await session.commit()
    return True


async def report_sender(
    session: AsyncSession,
    reporter_id: int,
    reported_id: int,
    message_id: int,
) -> tuple[bool, int]:
    session.add(
        Report(
            reporter_id=reporter_id,
            reported_id=reported_id,
            message_id=message_id,
        )
    )
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        count = int(
            await session.scalar(
                select(func.count(Report.id)).where(Report.reported_id == reported_id)
            )
            or 0
        )
        return False, count

    count = int(
        await session.scalar(
            select(func.count(Report.id)).where(Report.reported_id == reported_id)
        )
        or 0
    )
    if count >= settings.report_suspend_threshold:
        user = await session.get(User, reported_id)
        if user:
            user.status = UserStatus.SUSPENDED
            await session.commit()
    return True, count
