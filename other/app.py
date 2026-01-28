import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import common
import config
from youtube_search import get_youtube_search_links

st.set_page_config(
    page_title="Urban Server Analytics",
    page_icon="📊",
    layout="wide"
)

@st.cache_data(ttl=3600)  # Кэшируем данные на 1 час
def load_data():
    """
    Загрузка данных из базы данных
    """
    try:
        ans, is_ok, _ = common.send_rest('v2/select/{schema}/nsi_list?column_order=id'.format(schema=config.schema_name))
        if not is_ok:
            st.error('Ошибка при получении данных из БД')
            return None
        
        # Преобразуем JSON в список словарей
        data = json.loads(ans)
        
        # Создаем DataFrame
        df = pd.DataFrame(data)
        
        # Выводим информацию о дубликатах
        st.write(f"Всего видео: {len(df)}")
        
        try:
            # Создаем новый DataFrame с уникальными значениями
            df_unique = df.drop_duplicates(subset=['id_site'], keep='last')
            
            # Переименовываем колонки для удобства
            df_unique = df_unique.rename(columns={
                'video_published_at': 'published_at',
                'id_site': 'video_id',
                'sh_name': 'title',
                'likes': 'likes_count',
                'dislikes': 'dislikes_count',
                'comments_count': 'comments_count',
                'views_count': 'views_count',
                'sentiment': 'sentiment',
                'value': 'sentiment_value',
                'channel_title': 'channel_title',
                'video_duration': 'duration'
            })
            
            # Преобразуем даты
            df_unique['published_at'] = pd.to_datetime(df_unique['published_at'], errors='coerce')
            
            # Преобразуем длительность видео
            def parse_duration(duration):
                if pd.isna(duration):
                    return "00:00"
                try:
                    # Убираем 'PT' из начала
                    duration = duration.replace('PT', '')
                    minutes = 0
                    seconds = 0
                    
                    # Обрабатываем минуты
                    if 'M' in duration:
                        minutes_part = duration.split('M')[0]
                        minutes = int(minutes_part)
                        duration = duration.split('M')[1]
                    
                    # Обрабатываем секунды
                    if 'S' in duration:
                        seconds_part = duration.split('S')[0]
                        seconds = int(seconds_part)
                    
                    return f"{minutes:02d}:{seconds:02d}"
                except:
                    return "00:00"
            
            df_unique['duration'] = df_unique['duration'].apply(parse_duration)
            
            # Преобразуем числовые значения
            numeric_columns = ['views_count', 'likes_count', 'dislikes_count', 'comments_count']
            for col in numeric_columns:
                df_unique[col] = pd.to_numeric(df_unique[col], errors='coerce').fillna(0)
            
            # Удаляем строки с пропущенными датами
            df_unique = df_unique.dropna(subset=['published_at'])
            
            return df_unique
            
        except Exception as e:
            st.error(f"Ошибка при преобразовании данных: {str(e)}")
            st.error(f"Тип ошибки: {type(e)}")
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
            return None
            
    except Exception as e:
        st.error(f'Ошибка при обработке данных: {str(e)}')
        st.error(f'Тип ошибки: {type(e)}')
        import traceback
        st.error(f'Traceback: {traceback.format_exc()}')
        return None

def create_sentiment_distribution(df):
    """
    Создание графика распределения настроений
    """
    sentiment_counts = df['sentiment'].value_counts()
    
    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title='Распределение настроений в видео',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_engagement_metrics(df):
    """
    Создание графика метрик вовлеченности
    """
    engagement_data = df.groupby('video_id').agg({
        'views_count': 'first',
        'likes_count': 'first',
        'dislikes_count': 'first',
        'comments_count': 'first'
    }).reset_index()
    
    fig = go.Figure()
    
    metrics = {
        'views_count': 'Просмотры',
        'likes_count': 'Лайки',
        'dislikes_count': 'Дизлайки',
        'comments_count': 'Комментарии'
    }
    
    for col, name in metrics.items():
        fig.add_trace(go.Bar(
            name=name,
            y=[engagement_data[col].mean()],
            x=[name],
            text=[f"{engagement_data[col].mean():,.0f}"],
            textposition='auto',
        ))
    
    fig.update_layout(
        title='Средние показатели вовлеченности',
        barmode='group',
        showlegend=False,
        yaxis_title='Количество'
    )
    
    return fig

def create_views_timeline(df):
    """
    Создание графика просмотров во времени
    """
    try:
        # Создаем копию DataFrame для работы
        df_timeline = df.copy()
        
        # Проверяем наличие колонки published_at
        if 'published_at' not in df_timeline.columns:
            st.error("Колонка published_at не найдена")
            return None
        
        # Проверяем на дубликаты
        if df_timeline['published_at'].duplicated().any():
            st.warning("Обнаружены дубликаты в датах публикации")
            # Добавляем уникальный идентификатор к дубликатам
            df_timeline['published_at'] = df_timeline.apply(
                lambda row: f"{row['published_at']}_{row['video_id']}", 
                axis=1
            )
        
        # Сортируем по дате
        df_timeline = df_timeline.sort_values('published_at')
        
        fig = px.line(
            df_timeline,
            x='published_at',
            y='views_count',
            title='Количество просмотров по времени публикации',
            labels={'views_count': 'Просмотры', 'published_at': 'Дата публикации'}
        )
        
        return fig
    except Exception as e:
        st.error(f"Ошибка при создании графика: {str(e)}")
        return None

def create_top_channels(df):
    """
    Создание графика топ каналов
    """
    channel_stats = df.groupby('channel_title').agg({
        'video_id': 'count',
        'views_count': 'sum',
        'likes_count': 'sum'
    }).reset_index()
    
    channel_stats = channel_stats.sort_values('views_count', ascending=False).head(10)
    
    fig = px.bar(
        channel_stats,
        x='channel_title',
        y='views_count',
        title='Топ-10 каналов по просмотрам',
        labels={'views_count': 'Просмотры', 'channel_title': 'Канал'},
        color='likes_count',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def main():
    st.title("📊 Urban Server Analytics")
    
    # Загрузка данных
    df = load_data()
    if df is None:
        st.stop()
    
    # Боковая панель с фильтрами
    st.sidebar.header("Фильтры")
    
    # Фильтр по дате
    try:
        min_date = df['published_at'].min().date()
        max_date = df['published_at'].max().date()
        
        # Добавляем отладочную информацию
        st.sidebar.write(f"**Доступный диапазон дат:**")
        st.sidebar.write(f"• От: {min_date.strftime('%d.%m.%Y')}")
        st.sidebar.write(f"• До: {max_date.strftime('%d.%m.%Y')}")
        
        # Добавляем выбор относительных дат
        date_filter_type = st.sidebar.radio(
            "Тип фильтра по дате",
            ["Произвольный период", "Относительный период"]
        )
        
        if date_filter_type == "Относительный период":
            relative_period = st.sidebar.selectbox(
                "Выберите период",
                ["Последние 7 дней", "Последние 30 дней", "Последние 90 дней", "Последние 180 дней", "Последние 365 дней"]
            )
            
            # Вычисляем даты на основе выбранного периода
            end_date = max_date  # Используем максимальную дату из данных
            if relative_period == "Последние 7 дней":
                start_date = end_date - pd.Timedelta(days=7)
            elif relative_period == "Последние 30 дней":
                start_date = end_date - pd.Timedelta(days=30)
            elif relative_period == "Последние 90 дней":
                start_date = end_date - pd.Timedelta(days=90)
            elif relative_period == "Последние 180 дней":
                start_date = end_date - pd.Timedelta(days=180)
            else:  # Последние 365 дней
                start_date = end_date - pd.Timedelta(days=365)
                
            date_range = (start_date, end_date)
        else:
            date_range = st.sidebar.date_input(
                "Выберите период",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
    except Exception as e:
        st.error(f"Ошибка при обработке дат: {str(e)}")
        min_date = max_date = datetime.now().date()
        date_range = (min_date, max_date)
    
    # Фильтр по настроению
    sentiments = df['sentiment'].dropna().unique()
    if len(sentiments) > 0:
        selected_sentiments = st.sidebar.multiselect(
            "Выберите настроения",
            options=sentiments,
            default=sentiments
        )
    else:
        selected_sentiments = []
        st.sidebar.write("Нет доступных настроений")
    
    # Фильтр по поисковым образам
    st.sidebar.subheader("Поисковые образы")
    search_query = st.sidebar.text_input("Поиск по названию или описанию")
    
    # Добавляем кнопку для нового поиска в YouTube
    if st.sidebar.button("Новый поиск в YouTube"):
        try:
            # Получаем результаты поиска
            videos = get_youtube_search_links(search_query, days_ago=30)
            
            if videos:
                st.sidebar.success(f"Найдено {len(videos)} видео")
                # Обновляем данные
                df = load_data()
            else:
                st.sidebar.warning("Видео не найдены")
        except Exception as e:
            st.sidebar.error(f"Ошибка при поиске: {str(e)}")
    
    # Применение фильтров
    try:
        # Создаем маску для фильтрации
        date_mask = (df['published_at'].dt.date >= date_range[0]) & (df['published_at'].dt.date <= date_range[1])
        
        # Применяем фильтры
        filtered_df = df[date_mask]
        
        if len(selected_sentiments) > 0:
            sentiment_mask = filtered_df['sentiment'].isin(selected_sentiments)
            filtered_df = filtered_df[sentiment_mask]
        
        # Применяем поисковый фильтр
        if search_query:
            search_mask = (
                filtered_df['title'].str.contains(search_query, case=False, na=False) |
                filtered_df['description'].str.contains(search_query, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]
            
        # Выводим информацию о примененных фильтрах
        st.sidebar.write("---")
        st.sidebar.write("**Примененные фильтры:**")
        st.sidebar.write(f"• Период: {date_range[0].strftime('%d.%m.%Y')} - {date_range[1].strftime('%d.%m.%Y')}")
        if len(selected_sentiments) > 0:
            st.sidebar.write(f"• Настроения: {', '.join(selected_sentiments)}")
        if search_query:
            st.sidebar.write(f"• Поисковый запрос: {search_query}")
        
        st.sidebar.write(f"**Результаты фильтрации:**")
        st.sidebar.write(f"• Найдено видео: {len(filtered_df)} из {len(df)}")
        
        # Добавляем отладочную информацию о данных
        if len(filtered_df) == 0:
            st.warning("Нет видео, соответствующих выбранным фильтрам. Попробуйте изменить параметры фильтрации.")
        
    except Exception as e:
        st.error(f"Ошибка при фильтрации данных: {str(e)}")
        filtered_df = df
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего видео", len(filtered_df))
    with col2:
        st.metric("Общее количество просмотров", f"{filtered_df['views_count'].sum():,}")
    with col3:
        st.metric("Общее количество лайков", f"{filtered_df['likes_count'].sum():,}")
    with col4:
        st.metric("Общее количество комментариев", f"{filtered_df['comments_count'].sum():,}")
    
    # Дополнительные метрики
    col1, col2 = st.columns(2)
    with col1:
        avg_views = filtered_df['views_count'].mean()
        st.metric("Среднее количество просмотров", f"{avg_views:,.0f}")
    with col2:
        engagement_rate = (filtered_df['likes_count'].sum() + filtered_df['comments_count'].sum()) / filtered_df['views_count'].sum() * 100
        st.metric("Уровень вовлеченности", f"{engagement_rate:.2f}%")
    
    # Графики
    st.plotly_chart(create_engagement_metrics(filtered_df), use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_sentiment_distribution(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(create_top_channels(filtered_df), use_container_width=True)
    
    timeline_fig = create_views_timeline(filtered_df)
    if timeline_fig is not None:
        st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Детальная статистика по отдельному видео
    st.subheader("Детальная статистика по видео")
    video_titles = filtered_df['title'].tolist()
    selected_video = st.selectbox(
        "Выберите видео для детального анализа",
        options=video_titles,
        index=0
    )
    
    if selected_video:
        video_data = filtered_df[filtered_df['title'] == selected_video].iloc[0]
        
        # Создаем вкладки для разных типов информации
        tab1, tab2 = st.tabs(["Основная информация", "Комментарии"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Основная информация:**")
                st.write(f"**Название:** {video_data['title']}")
                st.write(f"**Канал:** {video_data['channel_title']}")
                st.write(f"**Дата публикации:** {video_data['published_at'].strftime('%d.%m.%Y %H:%M')}")
                st.write(f"**Длительность:** {video_data['duration']}")
                st.write(f"**Настроение:** {video_data['sentiment']}")
                st.write(f"**Значение настроения:** {video_data['sentiment_value']}")
                
            with col2:
                st.write("**Метрики:**")
                st.write(f"**Просмотры:** {video_data['views_count']:,}")
                st.write(f"**Лайки:** {video_data['likes_count']:,}")
                st.write(f"**Дизлайки:** {video_data['dislikes_count']:,}")
                st.write(f"**Комментарии:** {video_data['comments_count']:,}")
                
                # Расчет дополнительных метрик
                like_ratio = video_data['likes_count'] / video_data['views_count'] * 100 if video_data['views_count'] > 0 else 0
                comment_ratio = video_data['comments_count'] / video_data['views_count'] * 100 if video_data['views_count'] > 0 else 0
                st.write(f"**Процент лайков:** {like_ratio:.2f}%")
                st.write(f"**Процент комментариев:** {comment_ratio:.2f}%")
            
            # Ссылка на видео
            st.write(f"**Ссылка на видео:** [{video_data['url']}]({video_data['url']})")
            
            # Описание видео
            if 'description' in video_data and video_data['description']:
                st.write("**Описание видео:**")
                st.write(video_data['description'])
        
        with tab2:
            st.write("**Комментарии к видео**")
            
            # Загружаем комментарии для выбранного видео
            try:
                comments_ans, is_ok, _ = common.send_rest(
                    f'v2/select/{config.schema_name}/nsi_comments?video_id={video_data["video_id"]}'
                )
                
                if is_ok:
                    comments_data = json.loads(comments_ans)
                    
                    if len(comments_data) > 0:
                        # Создаем DataFrame для комментариев
                        comments_df = pd.DataFrame(comments_data)
                        
                        # Форматируем даты
                        comments_df['published_at'] = pd.to_datetime(comments_df['published_at']).dt.strftime('%d.%m.%Y %H:%M')
                        
                        # Переименовываем колонки
                        comments_df = comments_df.rename(columns={
                            'sh_name': 'Автор',
                            'text': 'Текст',
                            'likes': 'Лайки',
                            'published_at': 'Дата'
                        })
                        
                        # Сортируем по дате (новые сверху)
                        comments_df = comments_df.sort_values('Дата', ascending=False)
                        
                        # Отображаем таблицу
                        st.dataframe(
                            comments_df[['Автор', 'Текст', 'Лайки', 'Дата']],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("К этому видео пока нет комментариев")
                else:
                    st.error("Не удалось загрузить комментарии")
                    
            except Exception as e:
                st.error(f"Ошибка при загрузке комментариев: {str(e)}")
    
    # Таблица с данными
    st.subheader("Детальные данные")
    
    # Создаем словарь для перевода названий колонок
    column_names = {
        'title': 'Название',
        'url': 'Ссылка',
        'views_count': 'Просмотры',
        'likes_count': 'Лайки',
        'dislikes_count': 'Дизлайки',
        'comments_count': 'Комментарии',
        'sentiment': 'Настроение',
        'sentiment_value': 'Значение настроения',
        'channel_title': 'Канал',
        'published_at': 'Дата публикации',
        'duration': 'Длительность'
    }
    
    display_columns = [
        'title', 'url', 'views_count', 
        'likes_count', 'dislikes_count', 'comments_count',
        'sentiment', 'sentiment_value', 'channel_title',
        'published_at', 'duration'
    ]
    
    # Проверяем наличие всех колонок
    display_columns = [col for col in display_columns if col in filtered_df.columns]
    
    # Сортируем данные по просмотрам
    filtered_df = filtered_df.sort_values('views_count', ascending=False)
    
    # Переименовываем колонки для отображения
    display_df = filtered_df[display_columns].rename(columns=column_names)
    
    # Форматируем даты
    display_df['Дата публикации'] = display_df['Дата публикации'].dt.strftime('%d.%m.%Y %H:%M')
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

if __name__ == '__main__':
    main() 