import pytest

from django.urls import reverse

from news.forms import CommentForm


@pytest.mark.django_db  # Разрешаем доступ к базе данных.
@pytest.mark.parametrize(
    # Задаём названия для параметров:
    'parametrized_client, news_in_list',
    (
        # Передаём фикстуры в параметры при помощи "ленивых фикстур":
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('not_author_client'), True),
    )
)
def test_news_list_for_different_users(
        # Используем фикстуру новости и параметры из декоратора:
        news, news2, parametrized_client, news_in_list
):
    url = reverse('news:home')
    # Выполняем запрос от имени параметризованного клиента:
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    # Проверяем истинность утверждения "новость есть в списке":
    assert (news in object_list) is news_in_list
    assert (news2 in object_list) is news_in_list
    # Проверяем количество новостей на странице:
    assert len(object_list) <= 10
    # Новости отсортированы по дате публикации по возрастанию.
    for i in range(len(object_list) - 1):
        assert object_list[i].date >= object_list[i + 1].date


@pytest.mark.django_db  # Разрешаем доступ к базе данных.
def test_comments_order(
        # Используем фикстуру для создания комментариев:
        comment, comment2, not_author_client, news
):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    # Выполняем запрос от имени не автора поста:
    response = not_author_client.get(url)
    # Извлекаем объект новости из контекста
    news_object = response.context['news']
    # Получаем комментарии через связь с новостью
    comments = news_object.comment_set.all()
    # Проверяем истинность утверждения "комментарий есть в списке":
    assert (comment in comments) is True
    assert (comment2 in comments) is True
    # Комментарии отсортированы по дате публикации по убыванию.
    for i in range(len(comments) - 1):
        assert comments[i].created <= comments[i + 1].created


@pytest.mark.django_db  # Разрешаем доступ к базе данных.
@pytest.mark.parametrize(
    # В качестве параметров передаём name и args для reverse.
    'name, args',
    (
        # Для тестирования страницы редактирования комментария
        # нужен pk комментария.
        ('news:edit', pytest.lazy_fixture('pk_for_args')),
    )
)
def test_pages_contains_form(author_client, name, args):
    # Формируем URL.
    url = reverse(name, args=args)
    # Запрашиваем нужную страницу:
    response = author_client.get(url)
    # Проверяем, есть ли объект формы в словаре контекста:
    assert 'form' in response.context
    # Проверяем, что объект формы относится к нужному классу.
    assert isinstance(response.context['form'], CommentForm)


@pytest.mark.django_db  # Разрешаем доступ к базе данных.
@pytest.mark.parametrize(
    # Задаём названия для параметров:
    'parametrized_client, form_avalibility',
    (
        # Передаём фикстуры в параметры при помощи "ленивых фикстур":
        (pytest.lazy_fixture('client'), False),
        (pytest.lazy_fixture('not_author_client'), True),
    ),
)
def test_comment_form_avalibility_for_differenr_users(
    parametrized_client, form_avalibility, news
):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = parametrized_client.get(url)
    # Проверяем, есть ли форма в контексте в зависимости от пользователя
    assert ('form' in response.context) == form_avalibility
    # Если форма должна быть, проверяем её тип
    if form_avalibility:
        assert isinstance(response.context['form'], CommentForm)
