from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 لینک من", callback_data="my_link")
    builder.button(text="📥 صندوق پیام", callback_data="inbox")
    builder.button(text="⭐ امتیاز من", callback_data="score")
    builder.button(text="💎 اشتراک VIP", callback_data="vip")
    builder.button(text="🚫 لیست بلاک", callback_data="blocked_list")
    builder.button(text="☎️ ارتباط با ما", callback_data="support")
    builder.adjust(2)
    return builder.as_markup()


def message_actions(message_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ پاسخ", callback_data=f"reply:{message_id}")
    builder.button(text="🚫 بلاک", callback_data=f"block:{message_id}")
    builder.button(text="⚠️ گزارش", callback_data=f"report:{message_id}")
    builder.adjust(3)
    return builder.as_markup()


def unblock_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for blocked_user_id, title in items:
        builder.button(
            text=f"✅ آنبلاک {title}",
            callback_data=f"unblock:{blocked_user_id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def vip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="درخواست فعال‌سازی VIP", callback_data="vip_request")]
        ]
    )
