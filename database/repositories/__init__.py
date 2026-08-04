from .interview_question_repository import InterviewQuestionRepository
from .interview_repository import InterviewRepository
from .question_category_repository import QuestionCategoryRepository
from .user_answer_repository import UserAnswerRepository
from .user_repository import UserRepository

interview_question_repository = InterviewQuestionRepository()
interview_repository = InterviewRepository()
question_category_repository = QuestionCategoryRepository()
user_answer_repository = UserAnswerRepository()
user_repository = UserRepository()