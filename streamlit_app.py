import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import chardet

# Улучшенная функция загрузки данных
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

# Загрузка данных
try:
    budget_df = load_data('budget.csv')
    housing_df = load_data('housing.csv')
    investments_df = load_data('investments.csv')
except Exception as e:
    st.error(f"Ошибка загрузки данных: {str(e)}")
    st.stop()

# Настройка страницы
st.title('Сравнение показателей региона')

# Выбор региона (только один)
all_regions = budget_df['Name'].unique()
selected_region = st.selectbox('Выберите регион:', all_regions, index=0)

# Выбор тем (можно несколько)
topics = st.multiselect(
    'Выберите темы для сравнения:',
    ['Бюджет', 'Жилищный фонд', 'Инвестиции'],
    default=['Бюджет']
)

if not topics:
    st.warning("Пожалуйста, выберите хотя бы одну тему.")
    st.stop()

# Словарь для данных и подписей
data_dict = {
    'Бюджет': (budget_df, 'Бюджет (рубли)', 'tab:blue'),
    'Жилищный фонд': (housing_df, 'Жилищный фонд (кв.м/чел.)', 'tab:orange'),
    'Инвестиции': (investments_df, 'Инвестиции (рубли)', 'tab:green')
}

# Определяем общие года для всех выбранных тем
year_columns = []
for topic in topics:
    df, _, _ = data_dict[topic]
    numeric_cols = [col for col in df.columns if str(col).isdigit()]
    if not year_columns:
        year_columns = numeric_cols
    else:
        year_columns = [col for col in year_columns if col in numeric_cols]

if not year_columns:
    st.error("Нет общих годов для выбранных тем.")
    st.stop()

available_years = [int(col) for col in year_columns]
min_year, max_year = min(available_years), max(available_years)

# Выбор диапазона лет
year_range = st.slider(
    'Выберите диапазон лет:',
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Фильтрация по годам
year_columns = [str(year) for year in range(year_range[0], year_range[1]+1)]

# Построение графика
st.subheader(f"Сравнение показателей для региона: {selected_region}")
fig, ax = plt.subplots(figsize=(12, 6))

# Для каждой выбранной темы
for topic in topics:
    df, y_label, color = data_dict[topic]
    region_data = df[df['Name'] == selected_region]
    
    if not region_data.empty:
        values = region_data[year_columns].values.flatten()
        years = [int(year) for year in year_columns]
        
        ax.plot(
            years,
            values,
            label=y_label,
            color=color,
            marker='o',
            linewidth=2
        )

ax.set_xlabel('Год', fontsize=12)
ax.set_ylabel('Значение показателя', fontsize=12)
ax.set_title(f'Сравнение показателей для {selected_region}', fontsize=14)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, linestyle='--', alpha=0.7)
plt.xticks([int(year) for year in year_columns], rotation=45)
plt.tight_layout()

st.pyplot(fig)

# Отображение таблиц с данными
st.subheader("Данные по выбранным темам")
for topic in topics:
    df, _, _ = data_dict[topic]
    st.markdown(f"**{topic}**")
    st.dataframe(
        df[df['Name'] == selected_region][['Name'] + year_columns].reset_index(drop=True),
        use_container_width=True
    )
