from datetime import datetime
from django.urls import reverse
import pytest

# Импортируем класс клиента.
from django.test.client import Client

# Импортируем модель новости, чтобы создать экземпляр.
from news.models import News, Comment


@pytest.fixture
def news_home_url():
    return reverse('news:home')


@pytest.fixture
def news_detail_url():
    return reverse('news:detail', kwargs={'pk': news.pk})


@pytest.fixture
# Используем встроенную фикстуру для модели пользователей django_user_model.
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author):  # Вызываем фикстуру автора.
    # Создаём новый экземпляр клиента, чтобы не менять глобальный.
    client = Client()
    client.force_login(author)  # Логиним автора в клиенте.
    return client


@pytest.fixture
def not_author_client(not_author):
    client = Client()
    client.force_login(not_author)  # Логиним обычного пользователя в клиенте.
    return client


@pytest.fixture
def news():
    news = News.objects.create(  # Создаём объект новости.
        title='Заголовок',
        text='Текст новости',
        date=datetime.today()
    )
    return news


@pytest.fixture
def news2():
    news2 = News.objects.create(  # Создаём объект новости.
        title='Заголовок 2',
        text='Текст второй новости',
        date=datetime.today()
    )
    return news2


@pytest.fixture
# Фикстура запрашивает другую фикстуру создания заметки.
def id_for_args(news):
    # И возвращает кортеж, который содержит id новости.
    # На то, что это кортеж, указывает запятая в конце выражения.
    return (news.pk,)


@pytest.fixture
def comment(news, author):
    comment = Comment.objects.create(  # Создаём объект комментария.
        news=news,
        text='Текст комментария',
        author=author
    )
    return comment


@pytest.fixture
def comment2(news, author):
    comment2 = Comment.objects.create(  # Создаём еще один объект комментария.
        news=news,
        text='Текст второго комментария',
        author=author
    )
    return comment2


@pytest.fixture
def pk_for_args(comment):
    return (comment.pk,)  # Передаем pk созданного комментария


# Добавляем фикстуру form_data
@pytest.fixture
def form_data():
    return {
        'text': 'Новый текст'
    }
