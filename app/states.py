from aiogram.fsm.state import State, StatesGroup


class SendAnonymous(StatesGroup):
    waiting_for_message = State()


class ReplyAnonymous(StatesGroup):
    waiting_for_reply = State()


class SupportForm(StatesGroup):
    waiting_for_message = State()


class AdminReply(StatesGroup):
    waiting_for_reply = State()
