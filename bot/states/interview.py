from aiogram.fsm.state import State, StatesGroup


class InterviewStates(StatesGroup):
    waiting_position = State()
    waiting_requirements = State()
    waiting_difficulty = State()
    answering = State()
