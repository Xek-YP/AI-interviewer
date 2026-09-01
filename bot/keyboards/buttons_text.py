from database.enums import Difficulty

START_INTERVIEW = '🎤 Начать собеседование'
VIEW_HISTORY = '📈 История'
PROFILE = '🧑 Профиль'
HELP = '❗ Помощь'
END_INTERVIEW = 'Звершить собеседование'
DIFFICULTY_BUTTONS = {
    'Junior': Difficulty.JUNIOR,
    'Middle': Difficulty.MIDDLE,
    'Senior': Difficulty.SENIOR
}
JUNIOR = 'Junior'
MIDDLE = 'Middle'
SENIOR = 'Senior'

MAIN_MENU_BUTTONS = {START_INTERVIEW, VIEW_HISTORY, PROFILE, HELP}