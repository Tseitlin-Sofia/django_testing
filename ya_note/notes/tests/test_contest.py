# Импортируем функцию для получения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
# Импортируем функцию reverse(), она понадобится для получения адреса страницы.
from django.urls import reverse

from notes.models import Note
from yanote.settings import NOTES_COUNT_ON_NOTES_LIST_PAGE


User = get_user_model()


class TestNotesList(TestCase):
    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    NOTES_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        all_notes = [
            Note(
                title=f'Заголовок-{index}',
                text='Просто текст.',
                slug=f'slug-{index}',
                author=cls.author,
            )
            for index in range(NOTES_COUNT_ON_NOTES_LIST_PAGE)
        ]
        Note.objects.bulk_create(all_notes)

    def test_notes_count(self):
        self.client.force_login(self.author)
        # Загружаем главную страницу.
        response = self.client.get(self.NOTES_URL)
        # Код ответа не проверяем, его уже проверили в тестах маршрутов.
        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']
        # Определяем количество записей в списке.
        notes_count = object_list.count()
        # Проверяем, что на странице именно 10 новостей.
        self.assertEqual(notes_count, NOTES_COUNT_ON_NOTES_LIST_PAGE)


class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title='Тестовая запись',
            text='Просто текст.',
            slug='test-note',
            author=cls.author
        )
        # Сохраняем в переменную адрес страницы с новостью:
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))

    def test_anonymous_client_has_no_form(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 302)
