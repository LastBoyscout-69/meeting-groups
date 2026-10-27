import os
import pandas as pd
import streamlit as st
from dashboard import render_dashboard
from models import Student, DAYS, LANGUAGES, TIMEZONES
from grouping import group_students, find_best_splits

CSV_PATH = "students.csv"

# Инициализируем память приложения
if "saved_groups" not in st.session_state:
    st.session_state.saved_groups = None
if "saved_splits" not in st.session_state:
    st.session_state.saved_splits = {}


def load_students() -> list[Student]:
    if not os.path.exists(CSV_PATH):
        return []
    try:
        df = pd.read_csv(CSV_PATH, dtype={"grade": int}, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_PATH, dtype={"grade": int}, encoding="cp1251")

    students = []
    for _, row in df.iterrows():
        students.append(Student(
            name=str(row["name"]).strip(),
            city=str(row["city"]).strip(),
            district=str(row["district"]).strip(),
            grade=int(row["grade"]),
            language=str(row["language"]).strip(),
            days=[d.strip() for d in str(row["days"]).split(",") if d.strip()],
            timezone=str(row["timezone"]).strip(),
        ))
    return students


def save_students(students: list[Student]):
    df = pd.DataFrame([s.to_dict() for s in students])
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")


st.set_page_config(page_title="Группы учеников", page_icon="📚", layout="wide")
st.title("📚 Сборка групп учеников")

# Вкладки

mode = st.radio(
    "Режим",
    ["➕ Добавить ученика", "📋 Все ученики", "🧩 Собрать группы", "📊 Дашборд"],
    horizontal=True,
)
if mode == "➕ Добавить ученика":
    with st.form("add_student", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Имя ученика")
            city = st.text_input("Город")
            district = st.text_input("Район")
            grade = st.selectbox("Класс", list(range(1, 12)))
        with col2:
            language = st.selectbox("Язык", LANGUAGES)
            days = st.multiselect("Доступные дни", DAYS)
            timezone = st.selectbox("Часовой пояс", TIMEZONES, index=1)

        if st.form_submit_button("Добавить"):
            if not name or not city or not days:
                st.error("Заполните имя, город и хотя бы один день.")
            else:
                students = load_students()
                students.append(Student(name, city, district, grade, language, days, timezone))
                save_students(students)
                st.success(f"✅ {name} добавлен(а).")

if mode == "📋 Все ученики":
    st.subheader("📂 Импорт учеников из CSV")
    uploaded_file = st.file_uploader("Выберите файл формата .csv", type=["csv"])

    if uploaded_file is not None:
        if st.button("Загрузить этих учеников в базу"):
            try:
                # Читаем файл
                df_new = pd.read_csv(uploaded_file, dtype={"grade": int}, encoding="utf-8-sig")

                # Берем текущих учеников и добавляем новых
                current_students = load_students()
                added_count = 0

                for _, row in df_new.iterrows():
                    days = [d.strip() for d in str(row["days"]).split(",") if d.strip()]
                    current_students.append(Student(
                        name=str(row["name"]).strip(),
                        city=str(row["city"]).strip(),
                        district=str(row["district"]).strip(),
                        grade=int(row["grade"]),
                        language=str(row["language"]).strip(),
                        days=days,
                        timezone=str(row["timezone"]).strip(),
                    ))
                    added_count += 1

                save_students(current_students)
                st.session_state.saved_groups = None # Сбрасываем группы, чтобы они пересобрались
                st.success(f"✅ Успешно добавлено {added_count} учеников!")
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка чтения файла: {e}")

    st.divider()

    # --- Текущий список учеников ---
    students = load_students()
    if not students:
        st.info("Пока нет учеников.")
    else:
        df = pd.DataFrame([s.to_dict() for s in students])

        edited = st.data_editor(
            df,
            num_rows="dynamic",
            width="stretch",
            key="students_editor",
            column_config={
                "grade": st.column_config.NumberColumn("Класс", min_value=1, max_value=11, step=1),
                "name": st.column_config.TextColumn("Имя"),
                "city": st.column_config.TextColumn("Город"),
                "district": st.column_config.TextColumn("Район"),
                "language": st.column_config.SelectboxColumn("Язык", options=LANGUAGES),
                "days": st.column_config.TextColumn("Дни (через запятую)"),
                "timezone": st.column_config.SelectboxColumn("Часовой пояс", options=TIMEZONES),
            },
        )

        if st.button("💾 Сохранить изменения", type="primary"):
            new_students = []
            for _, row in edited.iterrows():
                if pd.isna(row["name"]) or str(row["name"]).strip() == "":
                    continue
                days = [d.strip() for d in str(row["days"]).split(",") if d.strip()]
                new_students.append(Student(
                    name=str(row["name"]).strip(),
                    city=str(row["city"]).strip(),
                    district=str(row["district"]).strip(),
                    grade=int(row["grade"]),
                    language=str(row["language"]).strip(),
                    days=days,
                    timezone=str(row["timezone"]).strip(),
                ))
            save_students(new_students)
            # Сбрасываем память, так как данные изменились
            st.session_state.saved_groups = None
            st.session_state.saved_splits = {}
            st.success(f"✅ Сохранено учеников: {len(new_students)}")

if mode == "🧩 Собрать группы":
    students = load_students()
    if not students:
        st.info("Нет данных для группировки.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            strict_district = st.checkbox("Строго по району", value=True)
        with col2:
            strict_grade = st.checkbox("Строго по классу", value=True)

        # Кнопка сохранения групп в память
        if st.button("🧩 Собрать группы", type="primary"):
            groups = group_students(students, strict_district, strict_grade)
            for g in groups:
                g["tz_warning"] = len(g.get("timezones", [])) > 1

            st.session_state.saved_groups = groups
            st.session_state.saved_splits = {}
            st.rerun()

        # Отрисовка из памяти (если группы уже собраны)
        if st.session_state.saved_groups is not None:
            groups = st.session_state.saved_groups

            ok = [g for g in groups if g["status"] == "ok"]
            bad = [g for g in groups if g["status"] == "conflict"]

            st.success(f"Собрано групп: {len(ok)} · Конфликтов: {len(bad)}")

            export_data = []

            if ok:
                st.subheader("✅ Успешные группы")
                for g in ok:
                    with st.container(border=True):
                        title = f"**{g['city']} / {g['district']} / {g['grade']} кл. / {g['language']}**"
                        if g["tz_warning"]:
                            title += " ⚠️ (разные часовые пояса)"

                        st.markdown(title)
                        st.write(f"📅 Дни: {', '.join(g['days'])}")
                        st.write(f"👥 Участники: {', '.join(g['students'])}")

                    export_data.append({
                        "Статус": "Собрана",
                        "Город": g['city'],
                        "Район": g['district'],
                        "Класс": g['grade'],
                        "Язык": g['language'],
                        "Общие дни": ", ".join(g['days']),
                        "Участники": ", ".join(g["students"]),
                        "Разные часовые пояса": "Да" if g["tz_warning"] else "Нет"
                    })

            if bad:
                st.subheader("⚠️ Конфликты")
                for idx, g in enumerate(bad):
                    with st.container(border=True):
                        title = f"**{g['city']} / {g['district']} / {g['grade']} кл. / {g['language']}**"

                        warnings = []
                        if not g["days"]:
                            warnings.append("нет общего дня")
                        if g["tz_warning"]:
                            warnings.append("разные часовые пояса")

                        if warnings:
                            title += f" <br><span style='color: #ff4b4b; font-size: 1.1em;'>⚠️ Причина: {', '.join(warnings)}</span>"

                        st.markdown(title, unsafe_allow_html=True)
                        st.write(f"👥 Участники: {', '.join(g['students'])}")

                        btn_key = f"split_btn_{idx}"
                        if st.button(f"🔀 Разбить группу {idx+1}", key=btn_key):
                            members = [s for s in students if s.name in g["students"]]
                            splits = find_best_splits(members, min_days_overlap=1)
                            st.session_state.saved_splits[idx] = splits
                            st.rerun()

                        if idx in st.session_state.saved_splits:
                            splits = st.session_state.saved_splits[idx]
                            if not splits:
                                st.warning("Эти ученики не имеют общих дней. Разбить невозможно.")
                            else:
                                st.success(f"Найдено подгрупп: {len(splits)}")
                                for i, sub in enumerate(splits, 1):
                                    sub_members = [s for s in students if s.name in sub["students"]]
                                    tz = sub_members[0].timezone if sub_members else ""

                                    st.info(
                                        f"**Подгруппа {i}** — дни: {', '.join(sub['days'])} | Участники: {', '.join(sub['students'])}\n\n"
                                        f"*Причина:* один город, один часовой пояс ({tz}), общие дни."
                                    )

                                    export_data.append({
                                        "Статус": "Подгруппа из конфликта",
                                        "Город": g['city'],
                                        "Район": g['district'],
                                        "Класс": g['grade'],
                                        "Язык": g['language'],
                                        "Общие дни": ", ".join(sub['days']),
                                        "Участники": ", ".join(sub['students']),
                                        "Разные часовые пояса": "Да" if g["tz_warning"] else "Нет"
                                    })

            if export_data:
                st.divider()
                st.subheader("📥 Экспорт результата")
                df_export = pd.DataFrame(export_data)
                csv = df_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

                st.download_button(
                    label="⬇️ Скачать группы в CSV",
                    data=csv,
                    file_name="groups_result.csv",
                    mime="text/csv",
                    type="primary"
                )

if mode == "📊 Дашборд":
    students = load_students()
    render_dashboard(students)
