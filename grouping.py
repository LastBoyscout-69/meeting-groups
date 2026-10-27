from collections import defaultdict
from itertools import combinations
from typing import List, Dict

from models import Student


def _intersect_days(day_lists: List[List[str]]) -> List[str]:
    """Пересечение списков дней у нескольких учеников."""
    if not day_lists:
        return []
    common = set(day_lists[0])
    for days in day_lists[1:]:
        common &= set(days)
    return sorted(list(common))


def group_students(
    students: List[Student],
    strict_district: bool = True,
    strict_grade: bool = True,
) -> List[Dict]:
    """Группирует учеников по (город, район, класс, язык)."""
    buckets: Dict[tuple, List[Student]] = defaultdict(list)
    for s in students:
        city_key = str(s.city).strip()
        district_key = str(s.district).strip() if strict_district else "*"
        grade_key = s.grade if strict_grade else s.grade // 2
        lang_key = str(s.language).strip()

        buckets[(city_key, district_key, grade_key, lang_key)].append(s)

    groups = []
    for (city, district, grade_key, language), members in buckets.items():
        common_days = _intersect_days([m.days for m in members])
        unique_tzs = list(set([str(m.timezone).strip() for m in members]))

        groups.append({
            "city": city,
            "district": district if district != "*" else "любой",
            "grade": grade_key if strict_grade else f"{grade_key*2}–{grade_key*2+1}",
            "language": language,
            "days": common_days,
            "students": [m.name for m in members],
            "timezones": unique_tzs,
            "status": "ok" if common_days else "conflict",
        })

    groups.sort(key=lambda g: (g["city"], g["district"], str(g["grade"]), g["language"]))
    return groups


def find_best_splits(students: List[Student], min_days_overlap: int = 1) -> List[Dict]:
    """
    Разбивает учеников на подгруппы так, чтобы охватить ВСЕХ.
    Теперь учитывает не только дни, но и часовые пояса!
    В одну подгруппу могут попасть только те, у кого совпадает пояс и есть общий день.
    """
    results = []
    remaining = list(students)

    while remaining:
        best_combo = None
        best_days = []

        n = len(remaining)
        for r in range(n, 0, -1):
            for combo in combinations(remaining, r):
                # Проверяем, что у всех ОДИНАКОВЫЙ часовой пояс
                tzs = set([str(s.timezone).strip() for s in combo])
                if len(tzs) > 1:
                    continue  # Пропускаем, если пояса разные

                # Проверяем, что есть общие дни
                common = _intersect_days([s.days for s in combo])
                if len(common) >= min_days_overlap:
                    best_combo = list(combo)
                    best_days = common
                    break
            if best_combo:
                break

        if best_combo:
            results.append({
                "students": [s.name for s in best_combo],
                "days": best_days,
                "size": len(best_combo),
            })
            # Убираем этих учеников из общего списка
            for s in best_combo:
                remaining.remove(s)
        else:
            # Если никого не смогли объединить (например, у всех разные пояса),
            # просто выводим каждого по отдельности
            for s in remaining:
                results.append({
                    "students": [s.name],
                    "days": s.days,
                    "size": 1,
                })
            break

    return results