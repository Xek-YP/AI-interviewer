from constants.interview import (
    ANSWER_PROMPT,
    INTERVIEW_EVALUATION_PROMPT,
    INTERVIEW_VALIDATION_PROMPT,
    QUESTION_POOL_PROMPT,
)

PROMPT_QUESTION_POOL = 'question_pool'
PROMPT_ANSWER = 'answer_evaluation'
PROMPT_INTERVIEW_EVALUATION = 'interview_evaluation'
PROMPT_INTERVIEW_VALIDATION = 'interview_validation'

DEFAULT_PROMPTS: dict[str, dict[str, str]] = {
    PROMPT_QUESTION_POOL: {
        'title': 'Пул вопросов собеседования',
        'content': QUESTION_POOL_PROMPT,
    },
    PROMPT_ANSWER: {
        'title': 'Оценка ответа кандидата',
        'content': ANSWER_PROMPT,
    },
    PROMPT_INTERVIEW_EVALUATION: {
        'title': 'Итоговая оценка собеседования',
        'content': INTERVIEW_EVALUATION_PROMPT,
    },
    PROMPT_INTERVIEW_VALIDATION: {
        'title': 'Валидация вакансии',
        'content': INTERVIEW_VALIDATION_PROMPT,
    },
}
