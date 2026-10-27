import streamlit as st
import pandas as pd
from models import Student
from grouping import group_students


def render_dashboard(students: list[Student]):
    st.header("📊 Аналитика и статистика")

    if not students:
        st.info("Пока нет данных для анализа. Добавьте учеников.")
        return

    df = pd.DataFrame([s.to_dict() for s in students])

    # --- 1. Общая статистика (карточки) ---
    st.subheader("Общая картина")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👨‍🎓 Всего учеников", len(df))
    with col2:
        st.metric("🏙️ Городов", df["city"].nunique())
    with col3:
        st.metric("🗣️ Языков", df["language"].nunique())
    with col4:
        st.metric("🏫 Классов", df["grade"].nunique())

    st.divider()

    # --- 2. Графики ---
    st.subheader("Распределение учеников")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.write("**По классам**")
        grade_counts = df["grade"].value_counts().sort_index()
        st.bar_chart(grade_counts, x_label="Класс", y_label="Количество")

    with col_chart2:
        st.write("**По языкам**")
        lang_counts = df["language"].value_counts()
        st.bar_chart(lang_counts, x_label="Язык", y_label="Количество")

    st.divider()

    # --- 3. Анализ дней недели ---
    st.subheader("Активность по дням недели")
    all_days = []
    for days_str in df["days"]:
        # Разбиваем строку "Пн,Ср" на отдельные дни
        for day in str(days_str).split(","):
            if day.strip():
                all_days.append(day.strip())

    if all_days:
        days_df = pd.Series(all_days).value_counts()
        # Упорядочиваем дни по порядку
        days_order = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        days_df = days_df.reindex(days_order).fillna(0)
        st.bar_chart(days_df, x_label="День недели", y_label="Количество учеников")

    st.divider()

    # --- 4. Статус групп (сколько собирается) ---
    st.subheader("Готовность групп")

    # Считаем группы с жесткими настройками (по умолчанию)
    groups = group_students(students, strict_district=True, strict_grade=True)
    ok = [g for g in groups if g["status"] == "ok"]
    bad = [g for g in groups if g["status"] == "conflict"]

    col_ok, col_bad = st.columns(2)
    with col_ok:
        st.success(f"✅ Можно собрать групп: **{len(ok)}**")
    with col_bad:
        if bad:
            st.warning(f"⚠️ Проблемных групп: **{len(bad)}**")
        else:
            st.info("🎉 Все группы собираются отлично!")

    # Показываем список городов, где есть проблемы
    if bad:
        cities_with_problems = list(set([g['city'] for g in bad]))
        st.write(f"Города, где нужна доработка: **{', '.join(cities_with_problems)}**")