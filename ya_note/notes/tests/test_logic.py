from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    # Текст заметки понадобится в нескольких местах кода,
    # поэтому запишем его в атрибуты класса.
    TITLE = 'Заметка'
    NOTE_TEXT = 'Текст заметки'
    SLUG = 'new-note'

    @classmethod
    def setUpTestData(cls):
        # Адрес страницы с записью.
        cls.url = reverse('notes:add')
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании записи.
        cls.form_data = {
            'title': cls.TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.SLUG,
            'author': cls.user
        }

    def test_anonymous_user_cant_create_note(self):
        # Считаем количество заметок до попытки добавления заметки.
        initial_notes_count = Note.objects.count()
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, initial_notes_count)

    def test_user_can_create_note(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.SLUG)
        self.assertEqual(note.author, self.user)

    def test_user_cant_create_note_with_dublicate_slug(self):
        original_slug_data = {
            'text': self.NOTE_TEXT,
            'title': self.TITLE,
            'slug': self.SLUG,
            'author': self.user
        }
        # Создаем первую заметку
        self.auth_client.post(self.url, data=original_slug_data)

        # Данные для второй заметки с тем же slug
        dublicate_slug_data = {
            'text': self.NOTE_TEXT,
            'title': self.TITLE,
            'slug': self.SLUG,
            'author': self.user
        }
        # Пытаемся создать вторую заметку
        dublicate_note = self.auth_client.post(
            self.url, data=dublicate_slug_data
        )
        expected_error = f'{self.SLUG}{WARNING}'
        self.assertFormError(
            dublicate_note,
            form='form',
            field='slug',
            errors=expected_error
        )


class TestNoteEditDelete(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Обновлённая заметка'

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя - автора заметки.
        cls.author = User.objects.create(username='Автор заметки')
        # Создаём заметку в БД.
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note_slug',
            author=cls.author
        )
        # Формируем адрес блока с заметками, который понадобится для тестов.
        cls.note_url = reverse('notes:success')  # Адрес заметки.
        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # URL для редактирования заметки.
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        # URL для удаления заметки.
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        # Формируем данные для POST-запроса по обновлению заметки.
        cls.form_data = {'text': cls.NEW_NOTE_TEXT}
        # Обновляем данные формы, добавляем все поля
        cls.form_data = {
            'title': cls.note.title,  # Используем текущий title
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.note.slug,   # Используем текущий slug
            'author': cls.note.author
        }

    def test_author_can_delete_note(self):
        # От имени автора заметки отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу с заметкой.
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.note_url)
        # Считаем количество записей в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка по-прежнему на месте.
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_note(self):
        # Выполняем запрос на редактирование от имени автора заметки.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.note_url)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст заметки соответствует обновленному.
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.text, self.NOTE_TEXT)
