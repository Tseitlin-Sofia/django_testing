from http import HTTPStatus

import pytest
from pytest_django.asserts import assertFormError, assertRedirects

from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News


@pytest.mark.django_db  # Разрешаем доступ к базе данных.
# Указываем фикстуру form_data в параметрах теста.
def test_user_can_create_comment(author_client, author, news, form_data):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    # В POST-запросе отправляем данные, полученные из фикстуры form_data:
    response = author_client.post(url, data=form_data)
    # Проверяем редирект на страницу новости с якорем #comments
    expected_url = reverse('news:detail', kwargs={'pk': news.pk}) + '#comments'
    # Подсчитываем количество комментариев до создания нового.
    initial_comment_count = Comment.objects.count()
    # Проверяем, что был выполнен редирект
    # на страницу успешного добавления комментария:
    assertRedirects(response, expected_url)
    # Считаем общее количество комментариев в БД, ожидаем 1 комментарий.
    assert Comment.objects.count() == initial_comment_count + 1
    # Чтобы проверить значения полей заметки -
    # получаем её из базы при помощи метода get():
    new_comment = Comment.objects.latest('created')
    # Сверяем атрибуты объекта с ожидаемыми.
    assert new_comment.text == form_data['text']
    assert new_comment.author == author
    assert new_comment.news == news


# Добавляем маркер, который обеспечит доступ к базе данных:
@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news, form_data):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    # Через анонимный клиент пытаемся создать комметнарий:
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    # Подсчитываем количество комментариев до попытки создания нового.
    initial_comment_count = Comment.objects.count()
    # Проверяем, что произошла переадресация на страницу логина:
    assertRedirects(response, expected_url)
    # Считаем количество заметок в БД, ожидаем 0 заметок.
    assert Comment.objects.count() == initial_comment_count


@pytest.mark.django_db  # Разрешаем доступ к базе данных.
@pytest.mark.parametrize('bad_word', BAD_WORDS)
# Вызываем фикстуру отдельной новости, чтобы в базе появилась запись.
def test_no_bad_words(author_client, news, form_data, bad_word):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    comments_count = Comment.objects.count()
    # Подменяем текст комментария на ругательство
    form_data['text'] = bad_word
    # Пытаемся создать новую заметку:
    response = author_client.post(url, data=form_data)
    # Проверяем, что в ответе содержится ошибка формы для поля slug:
    assertFormError(response, 'form', 'text', errors=(WARNING))
    # Убеждаемся, что количество заметок в базе осталось равным 1:
    assert Comment.objects.count() == comments_count


# В параметрах вызвана фикстура news: значит, в БД создана новость.
def test_author_can_edit_comment(author_client, form_data, news, comment):
    # Получаем адрес страницы редактирования комментария:
    url = reverse('news:edit', kwargs={'pk': news.pk})
    # В POST-запросе на адрес редактирования комментария
    # отправляем form_data - новые значения для полей комментария:
    author_client.post(url, form_data)
    # Обновляем объект комментария comment: получаем обновлённые данные из БД:
    comment.refresh_from_db()
    # Проверяем, что атрибут комментария соответствуют обновлённым:
    assert comment.text == form_data['text']


def test_other_user_cant_edit_comment(
        not_author_client, form_data, news, comment
):
    url = reverse('news:edit', kwargs={'pk': news.pk})
    response = not_author_client.post(url, form_data)
    # Проверяем, что страница не найдена:
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Получаем новый объект запросом из БД.
    comment_from_db = Comment.objects.get(pk=news.pk)
    # Проверяем, что атрибуты объекта из БД равны атрибутам заметки до запроса.
    assert comment.text == comment_from_db.text


def test_author_can_delete_comment(author_client, pk_for_args):
    url = reverse('news:delete', args=pk_for_args)
    # Подсчитываем количество комментариев до удаления 1 комментария.
    initial_comment_count = Comment.objects.count()
    author_client.post(url)
    assert Comment.objects.count() == initial_comment_count - 1


def test_other_user_cant_delete_note(not_author_client, pk_for_args):
    url = reverse('news:delete', args=pk_for_args)
    # Подсчитываем количество новостей до удаления 1 новости.
    initial_news_count = News.objects.count()
    response = not_author_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == initial_news_count
