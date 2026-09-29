from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import SubscriptionType
from database.repositories.interview_repository import interview_repository
from database.repositories.user_repository import user_repository
from database.session import get_async_session
from services.prompt_service import prompt_service
from services.subscription_service import subscription_service

router = APIRouter()
templates = Jinja2Templates(directory='admin/templates')


@router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа."""
    if request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/users', status_code=303)
    return templates.TemplateResponse(
        request,
        'login.html',
        {'error': None},
    )


@router.post('/login')
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Обработка входа."""
    from config.settings import settings

    valid = (
        username == settings.admin_username
        and password == settings.admin_password.get_secret_value()
    )
    if not valid:
        return templates.TemplateResponse(
            request,
            'login.html',
            {'error': 'Неверный логин или пароль'},
            status_code=401,
        )

    request.session['admin_authenticated'] = True
    return RedirectResponse('/admin/users', status_code=303)


@router.post('/logout')
async def logout(request: Request):
    """Выход из админки."""
    request.session.clear()
    return RedirectResponse('/admin/login', status_code=303)


@router.get('/', response_class=HTMLResponse)
async def admin_index(request: Request):
    """Редирект на список пользователей."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)
    return RedirectResponse('/admin/users', status_code=303)


@router.get('/users', response_class=HTMLResponse)
async def users_list(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Список пользователей."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    users = await user_repository.list_users(session=session)
    return templates.TemplateResponse(
        request,
        'users.html',
        {
            'users': users,
            'active_page': 'users',
            'subscription_service': subscription_service,
        },
    )


@router.get('/users/{user_id}', response_class=HTMLResponse)
async def user_detail(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Карточка пользователя."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    user = await user_repository.get_with_interviews(
        session=session,
        user_id=user_id,
    )
    if user is None:
        return RedirectResponse('/admin/users', status_code=303)

    interviews = sorted(
        user.interviews,
        key=lambda item: item.created_at,
        reverse=True,
    )
    return templates.TemplateResponse(
        request,
        'user_detail.html',
        {
            'user': user,
            'interviews': interviews,
            'active_page': 'users',
            'subscription_types': list(SubscriptionType),
            'subscription_service': subscription_service,
        },
    )


@router.post('/users/{user_id}/subscription')
async def update_subscription(
    request: Request,
    user_id: int,
    subscription_type: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    """Меняет тип подписки пользователя."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    user = await user_repository.get_by_id(session=session, user_id=user_id)
    if user is None:
        return RedirectResponse('/admin/users', status_code=303)

    if subscription_type == SubscriptionType.PREMIUM.value:
        subscription_service.activate_premium(user)
    else:
        user.subscription_type = SubscriptionType.FREE
        user.subscription_started_at = None

    await session.commit()
    return RedirectResponse(f'/admin/users/{user_id}', status_code=303)


@router.post('/users/{user_id}/block')
async def toggle_block(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Блокирует или разблокирует пользователя."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    user = await user_repository.get_by_id(session=session, user_id=user_id)
    if user is None:
        return RedirectResponse('/admin/users', status_code=303)

    user.is_blocked = not user.is_blocked
    await session.commit()
    return RedirectResponse(f'/admin/users/{user_id}', status_code=303)


@router.get('/interviews', response_class=HTMLResponse)
async def interviews_list(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Список собеседований."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    interviews = await interview_repository.list_recent(session=session)
    return templates.TemplateResponse(
        request,
        'interviews.html',
        {
            'interviews': interviews,
            'active_page': 'interviews',
        },
    )


@router.get('/interviews/{interview_id}', response_class=HTMLResponse)
async def interview_detail(
    request: Request,
    interview_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Детали собеседования: вопросы, ответы, оценки."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    interview = await interview_repository.get_detail_by_id(
        session=session,
        interview_id=interview_id,
    )
    if interview is None:
        return RedirectResponse('/admin/interviews', status_code=303)

    questions = sorted(interview.questions, key=lambda q: q.order_number)
    return templates.TemplateResponse(
        request,
        'interview_detail.html',
        {
            'interview': interview,
            'questions': questions,
            'active_page': 'interviews',
        },
    )


@router.get('/prompts', response_class=HTMLResponse)
async def prompts_list(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Список промптов."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    await prompt_service.ensure_defaults(session=session)
    prompts = await prompt_service.list_prompts(session=session)
    return templates.TemplateResponse(
        request,
        'prompts.html',
        {
            'prompts': prompts,
            'active_page': 'prompts',
        },
    )


@router.get('/prompts/{key}', response_class=HTMLResponse)
async def prompt_edit_page(
    request: Request,
    key: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Страница редактирования промпта."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    await prompt_service.ensure_defaults(session=session)
    prompt = await prompt_service.get_prompt(session=session, key=key)
    if prompt is None:
        return RedirectResponse('/admin/prompts', status_code=303)

    return templates.TemplateResponse(
        request,
        'prompt_edit.html',
        {
            'prompt': prompt,
            'active_page': 'prompts',
            'saved': False,
        },
    )


@router.post('/prompts/{key}', response_class=HTMLResponse)
async def prompt_save(
    request: Request,
    key: str,
    content: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    """Сохраняет изменения промпта."""
    if not request.session.get('admin_authenticated'):
        return RedirectResponse('/admin/login', status_code=303)

    prompt = await prompt_service.update_prompt(
        session=session,
        key=key,
        content=content,
    )
    return templates.TemplateResponse(
        request,
        'prompt_edit.html',
        {
            'prompt': prompt,
            'active_page': 'prompts',
            'saved': True,
        },
    )
