from datetime import datetime

from django.core.exceptions import ValidationError


class PinTesting():
    def __init__(self, pin: str):
        self.pin = pin
        self.birth_date = None
        self.gender = None

    def show_pin(self):
        if len(self.pin) == 14:
            try:
                birth_date_str = self.pin[1:9]  # Extract substring from 2nd to 7th character of PIN
                self.birth_date = datetime.strptime(birth_date_str, '%d%m%Y').date()
            except ValueError:
                raise ValidationError("Invalid PIN format for birth date extraction.")
        else:
            raise ValidationError("PIN должен быть длиной 14 символов.")

        first_digit = int(self.pin[0])
        if first_digit == 1:
            self.gender = 'Женский'
        elif first_digit == 2:
            self.gender = 'Мужской'
        else:
            raise ValidationError("Invalid first digit in PIN for gender determination.")

    def __str__(self):
        return f'Год рождения {self.birth_date.strftime("%d %B %Y")} и пол {self.gender}'


if __name__ == "__main__":
    pin = input('Ввод пина (14 цифр): ')
    pin_testing = PinTesting(pin)
    pin_testing.show_pin()
    print(pin_testing)
