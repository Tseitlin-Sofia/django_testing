from unittest import TestCase


def get_square(num):
    return num ** 2


class TestExample(TestCase):

    def test_square(self):
        """Тест возведения в квадрат."""
        values_results = (
            (2, 4),
            (3, 10),
            (4, 20),
        )
        # В цикле присваиваем кортежи переменной item.
        for item in values_results:
            # Отдельной строкой распаковываем item на две переменных.
            value, expected_result = item
            # Остальной код без изменений.
            with self.subTest(
                value=value,
                expected_result=expected_result,
                msg=f'Возведение числа {value} в квадрат дало результат,\n'
                    f'отличающийся от ожидаемого {expected_result}',
            ):
                result = get_square(value)
                self.assertEqual(result, expected_result)
