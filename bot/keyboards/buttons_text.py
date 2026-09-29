from database.enums import Difficulty

START_INTERVIEW = '🎤 Начать собеседование'
VIEW_HISTORY = '📈 История'
PROFILE = '🧑 Профиль'
HELP = '❗ Помощь'
BUY_PREMIUM = '💎 PREMIUM'
END_INTERVIEW = 'Звершить собеседование'
DIFFICULTY_BUTTONS = {
    'Junior': Difficulty.JUNIOR,
    'Middle': Difficulty.MIDDLE,
    'Senior': Difficulty.SENIOR
}
JUNIOR = 'Junior'
MIDDLE = 'Middle'
SENIOR = 'Senior'

MAIN_MENU_BUTTONS = {
    START_INTERVIEW,
    VIEW_HISTORY,
    PROFILE,
    HELP,
    BUY_PREMIUM,
}

BUY_PREMIUM_CALLBACK = 'buy_premium'
