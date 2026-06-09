from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.keyboards import main_menu
from app.services import get_or_create_user, get_user_by_telegram_id
from app.states import SendAnonymous

router = Router()
settings = get_settings()


@router.message(CommandStart())
async def start_handler(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.from_user:
        return

    user = await get_or_create_user(
        session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name or "",
    )

    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) == 2 and args[1].startswith("u_"):
        raw_id = args[1][2:]
        if raw_id.isdigit():
            receiver = await get_user_by_telegram_id(session, int(raw_id))
            if receiver and receiver.id != user.id:
                await state.set_state(SendAnonymous.waiting_for_message)
                await state.update_data(receiver_id=receiver.id)
                await message.answer(
                    "✍️ پیام ناشناس خود را بفرستید. هویت شما برای دریافت‌کننده نمایش داده نمی‌شود."
                )
                return

    await state.clear()
    await message.answer(
        "سلام! از این ربات می‌توانید پیام ناشناس دریافت کنید.",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "my_link")
async def my_link(callback: CallbackQuery) -> None:
    link = f"https://t.me/{settings.bot_username}?start=u_{callback.from_user.id}"
    await callback.message.answer(
        f"🔗 لینک اختصاصی شما:\n\n{link}\n\nاین لینک را برای دوستانتان بفرستید."
    )
    await callback.answer()
