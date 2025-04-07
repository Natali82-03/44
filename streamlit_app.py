import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import chardet

# Конфигурация страницы (должна быть первой!)
st.set_page_config(layout="wide")

# --- Загрузка данных (без изменений) ---
@st.cache_data
def load_data(file_name):
    with open(file_name, 'rb') as f:
        result = chardet.detect(f.read(10000))
    try:
        df = pd.read_csv(file_name, sep=';', encoding=result['encoding'])
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_name, sep=';', encoding='utf-8')
        except:
            df = pd.read_csv(file_name, sep=';', encoding='cp1251')
    df = df.rename(columns=lambda x: x.strip())
    if 'Name' in df.columns:
        df['Name'] = df['Name'].str.strip()
    else:
        st.error(f"В файле {file_name} отсутствует столбец 'Name'")
    return df

try:
    budget_df = load_data('budget.csv')
    housing_df = load_data('housing.csv')
    investments_df = load_data('investments.csv')
except Exception as e:
    st.error(f"Ошибка загрузки данных: {str(e)}")
    st.stop()

# --- Словарь данных ---
data_dict = {
    'Бюджет': (budget_df, 'Бюджет (рубли)', 'tab:blue'),
    'Жилищный фонд': (housing_df, 'Жилищный фонд (кв.м/чел.)', 'tab:orange'),
    'Инвестиции': (investments_df, 'Инвестиции (рубли)', 'tab:green')
}

# --- Боковая панель (без изменений) ---
with st.sidebar:
    st.title("Настройки анализа")
    all_regions = budget_df['Name'].unique()
    selected_region = st.selectbox('Выберите регион:', all_regions, index=0)
    topics = st.multiselect('Выберите темы:', list(data_dict.keys()), default=['Бюджет'])
    
    if not topics:
        st.warning("Выберите хотя бы одну тему!")
        st.stop()
    
    # Определение общего диапазона лет
    year_columns = []
    for topic in topics:
        df, _, _ = data_dict[topic]
        numeric_cols = [col for col in df.columns if str(col).isdigit()]
        year_columns = numeric_cols if not year_columns else [col for col in year_columns if col in numeric_cols]
    
    year_range = st.slider(
        'Диапазон лет:',
        min_value=int(min(year_columns)),
        max_value=int(max(year_columns)),
        value=(int(min(year_columns)), int(max(year_columns)))
    )
    year_columns = [str(year) for year in range(year_range[0], year_range[1]+1)]

# --- Основной интерфейс ---
st.title(f'Анализ региона: {selected_region}')

# 1. Линейный график (как было)
st.subheader("Динамика показателей")
fig_line, ax_line = plt.subplots(figsize=(12, 4))
for topic in topics:
    df, label, color = data_dict[topic]
    region_data = df[df['Name'] == selected_region]
    if not region_data.empty:
        ax_line.plot(
            year_columns,
            region_data[year_columns].values.flatten(),
            label=label, color=color, marker='o', linewidth=2
        )
ax_line.set_xlabel('Год')
ax_line.set_ylabel('Значение')
ax_line.legend()
ax_line.grid(True, linestyle='--', alpha=0.7)
st.pyplot(fig_line)

# 2. НОВАЯ СТОЛБЧАТАЯ ДИАГРАММА
st.subheader("Сравнение показателей по годам")
fig_bar, ax_bar = plt.subplots(figsize=(12, 5))

# Подготовка данных для столбцов
bar_width = 0.8 / len(topics)  # Ширина столбцов
opacity = 0.8

for i, topic in enumerate(topics):
    df, label, color = data_dict[topic]
    region_data = df[df['Name'] == selected_region]
    if not region_data.empty:
        values = region_data[year_columns].values.flatten()
        positions = [x + i * bar_width for x in range(len(year_columns))]
        ax_bar.bar(
            positions, values, bar_width,
            alpha=opacity, color=color, label=label
        )

ax_bar.set_xticks([x + bar_width * (len(topics)-1)/2 for x in range(len(year_columns))])
ax_bar.set_xticklabels(year_columns)
ax_bar.set_xlabel('Год')
ax_bar.set_ylabel('Значение')
ax_bar.legend(bbox_to_anchor=(1.05, 1))
ax_bar.grid(True, axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig_bar)

# 3. Таблицы с данными
st.subheader("Детальные данные")
for topic in topics:
    df, label, _ = data_dict[topic]
    st.dataframe(
        df[df['Name'] == selected_region][['Name'] + year_columns],
        use_container_width=True
    )
