from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.keyboards import main_menu
from app.models import SupportTicket
from app.services import get_user_by_telegram_id
from app.states import SupportForm

router = Router()
settings = get_settings()


@router.callback_query(F.data == "support")
async def support_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SupportForm.waiting_for_message)
    await callback.message.answer("پیام خود را برای پشتیبانی ارسال کنید:")
    await callback.answer()


@router.message(SupportForm.waiting_for_message)
async def support_receive(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.from_user or not message.text:
        await message.answer("لطفاً پیام متنی ارسال کنید.")
        return

    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        return

    ticket = SupportTicket(user_id=user.id, text=message.text.strip())
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    for admin_id in settings.admin_id_set:
        try:
            await message.bot.send_message(
                admin_id,
                f"☎️ تیکت #{ticket.id}\n"
                f"کاربر: {user.telegram_id}\n"
                f"متن: {ticket.text}\n\n"
                f"برای پاسخ: /answer {ticket.id} متن پاسخ",
            )
        except Exception:
            pass

    await state.clear()
    await message.answer(
        "✅ پیام شما برای پشتیبانی ارسال شد.",
        reply_markup=main_menu(),
    )
