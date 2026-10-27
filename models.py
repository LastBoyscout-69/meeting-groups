from dataclasses import dataclass
from typing import List

DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

LANGUAGES = ["Английский", "Немецкий", "Французский", "Испанский"]

TIMEZONES = [
    "Europe/Kaliningrad",   # UTC+2
    "Europe/Moscow",        # UTC+3
    "Europe/Samara",        # UTC+4
    "Asia/Yekaterinburg",   # UTC+5
    "Asia/Omsk",            # UTC+6
    "Asia/Novosibirsk",     # UTC+7
    "Asia/Krasnoyarsk",     # UTC+8
    "Asia/Irkutsk",         # UTC+9
    "Asia/Vladivostok",     # UTC+10
]

@dataclass
class Student:
    name: str
    city: str
    district: str
    grade: int              # 1–11
    language: str
    days: List[str]         # список из DAYS
    timezone: str           # из TIMEZONES

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "city": self.city,
            "district": self.district,
            "grade": self.grade,
            "language": self.language,
            "days": ",".join(self.days),
            "timezone": self.timezone,
        }
# Словарь со смещениями часовых поясов относительно Москвы (UTC+3)
# Если у тебя есть другие пояса, их можно добавить сюда.
TZ_OFFSETS = {
    "Europe/Kaliningrad": -1,   # UTC+2
    "Europe/Moscow": 0,         # UTC+3
    "Europe/Samara": 1,         # UTC+4
    "Asia/Yekaterinburg": 2,    # UTC+5
    "Asia/Omsk": 3,             # UTC+6
    "Asia/Novosibirsk": 4,      # UTC+7
    "Asia/Krasnoyarsk": 5,      # UTC+8
    "Asia/Irkutsk": 6,          # UTC+9
    "Asia/Vladivostok": 7,      # UTC+10
}