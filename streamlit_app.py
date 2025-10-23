#!/usr/bin/env python3
"""
Streamlit Frontend para Historical Term Analyzer
Interfaz web interactiva para análisis de términos en páginas web históricas

Autor: Ian Alén Cisneros
Fecha: 2025-10-08
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
from datetime import datetime, timedelta
import io
import base64

# Importar el analizador principal
from historical_term_analyzer import HistoricalTermAnalyzer, InternetArchiveClient

# Configuración de la página
st.set_page_config(
    page_title="Historical Term Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 2rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #566573;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E86C1;
        margin-bottom: 1rem;
    }
    .status-running {
        color: #F39C12;
    }
    .status-complete {
        color: #27AE60;
    }
    .status-error {
        color: #E74C3C;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Inicializar variables de estado de sesión"""
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False
    if 'analysis_progress' not in st.session_state:
        st.session_state.analysis_progress = 0
    if 'analysis_status' not in st.session_state:
        st.session_state.analysis_status = ""
    if 'analysis_log' not in st.session_state:
        st.session_state.analysis_log = []
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'selected_analysis_id' not in st.session_state:
        st.session_state.selected_analysis_id = None
    if 'cancel_requested' not in st.session_state:
        st.session_state.cancel_requested = False

def add_log_entry(message: str, level: str = "info"):
    """Agregar entrada al log de análisis"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.analysis_log.append({
        'timestamp': timestamp,
        'level': level,
        'message': message
    })

def display_log():
    """Mostrar log de análisis"""
    if st.session_state.analysis_log:
        st.subheader("📋 Log de Análisis")
        log_container = st.container()
        
        with log_container:
            for entry in reversed(st.session_state.analysis_log[-10:]):  # Últimas 10 entradas
                level_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}.get(entry['level'], "ℹ️")
                st.text(f"{entry['timestamp']} {level_icon} {entry['message']}")

def add_to_history(results):
    """Agregar resultados al historial"""
    if results and 'error' not in results:
        # Crear ID único para este análisis
        analysis_id = f"analysis_{len(st.session_state.analysis_history) + 1}"
        
        config = results.get('config', {})
        
        # Crear entrada de historial
        history_entry = {
            'id': analysis_id,
            'timestamp': datetime.now(),
            'config': config,
            'results': results,
            'summary': results.get('summary', {}),
            'label': f"{config.get('start_year', '?')}-{config.get('end_year', '?')} ({config.get('max_documents', '?')} docs)"
        }
        
        # Agregar al historial (mantener máximo 10 análisis)
        st.session_state.analysis_history.append(history_entry)
        if len(st.session_state.analysis_history) > 10:
            st.session_state.analysis_history.pop(0)
        
        # Seleccionar automáticamente el nuevo análisis
        st.session_state.selected_analysis_id = analysis_id
        
        return analysis_id
    return None

def get_selected_results():
    """Obtener resultados del análisis seleccionado"""
    if st.session_state.selected_analysis_id:
        for entry in st.session_state.analysis_history:
            if entry['id'] == st.session_state.selected_analysis_id:
                return entry['results']
    
    # Si no hay selección o no se encuentra, usar el último
    if st.session_state.analysis_history:
        return st.session_state.analysis_history[-1]['results']
    
    return st.session_state.analysis_results

def create_sidebar():
    """Crear sidebar con configuraciones"""
    st.sidebar.title("⚙️ Configuración")
    
    # Configuración temporal
    st.sidebar.subheader("📅 Período de Análisis")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_year = st.number_input(
            "Año inicio",
            min_value=1995,
            max_value=2023,
            value=2000,
            step=1
        )
    with col2:
        end_year = st.number_input(
            "Año fin",
            min_value=1995,
            max_value=2023,
            value=2005,
            step=1
        )
    
    # Validación de años
    if start_year >= end_year:
        st.sidebar.error("El año de inicio debe ser menor al año de fin")
        return None
    
    # Configuración de documentos
    st.sidebar.subheader("📊 Parámetros de Análisis")
    
    max_documents = st.sidebar.slider(
        "Máximo de páginas web",
        min_value=50,
        max_value=1000,
        value=300,
        step=50,
        help="Número máximo de páginas web a analizar"
    )
    
    # Selección de dominios
    st.sidebar.subheader("🌐 Dominios a Analizar")
    
    # Dominios predefinidos
    available_domains = [
        'cnn.com', 'bbc.co.uk', 'nytimes.com', 'washingtonpost.com',
        'reuters.com', 'bloomberg.com', 'guardian.co.uk', 'time.com',
        'newsweek.com', 'usatoday.com', 'abcnews.go.com', 'cbsnews.com',
        'npr.org', 'economist.com', 'wsj.com'
    ]
    
    selected_domains = st.sidebar.multiselect(
        "Seleccionar dominios",
        available_domains,
        default=available_domains[:5],
        help="Selecciona los dominios web a analizar"
    )
    
    # Dominio personalizado
    custom_domain = st.sidebar.text_input(
        "Dominio personalizado",
        placeholder="ejemplo.com",
        help="Agregar un dominio personalizado"
    )
    
    if custom_domain and custom_domain not in selected_domains:
        selected_domains.append(custom_domain)
    
    # Configuración avanzada
    st.sidebar.subheader("🔧 Configuración Avanzada")
    
    rate_limit = st.sidebar.slider(
        "Delay entre requests (segundos)",
        min_value=0.5,
        max_value=5.0,
        value=1.0,
        step=0.1,
        help="Tiempo de espera entre requests para evitar rate limiting"
    )
    
    use_parallel = st.sidebar.checkbox(
        "Procesamiento paralelo",
        value=True,
        help="Usar procesamiento paralelo para mejor rendimiento"
    )
    
    return {
        'start_year': start_year,
        'end_year': end_year,
        'max_documents': max_documents,
        'domains': selected_domains,
        'rate_limit': rate_limit,
        'use_parallel': use_parallel
    }

def run_analysis(config):
    """Ejecutar análisis con la configuración dada"""
    
    # Callback para reportar progreso
    def progress_callback(percent, message):
        st.session_state.analysis_progress = percent
        st.session_state.analysis_status = message
        add_log_entry(message, "info")
    
    try:
        # Inicializar analizador con callback
        add_log_entry("Inicializando analizador...", "info")
        analyzer = HistoricalTermAnalyzer(
            rate_limit_delay=config['rate_limit'],
            progress_callback=progress_callback
        )
        
        # Configurar procesamiento paralelo
        analyzer.processor.use_parallel = config['use_parallel']
        
        add_log_entry(f"Analizando período {config['start_year']}-{config['end_year']}", "info")
        add_log_entry(f"Dominios: {', '.join(config['domains'])}", "info")
        add_log_entry(f"Máximo de páginas: {config['max_documents']}", "info")
        
        # Ejecutar análisis con análisis por año habilitado
        results = analyzer.analyze_period(
            start_year=config['start_year'],
            end_year=config['end_year'],
            max_documents=config['max_documents'],
            domains=config['domains'],
            analyze_by_year=True  # Siempre generar resultados por año
        )
        
        if 'error' in results:
            add_log_entry(f"Error en análisis: {results['error']}", "error")
            return None
        
        add_log_entry("Análisis completado exitosamente", "success")
        
        # Agregar estadísticas del cache si está disponible
        if hasattr(analyzer.processor, 'get_cache_stats'):
            cache_stats = analyzer.processor.get_cache_stats()
            add_log_entry(f"Cache hit rate: {cache_stats['hit_rate_percent']}%", "info")
        
        # Agregar metadatos de configuración a los resultados
        results['config'] = {
            'start_year': config['start_year'],
            'end_year': config['end_year'],
            'max_documents': config['max_documents'],
            'domains': config['domains'],
            'timestamp': datetime.now().isoformat()
        }
        
        return results
        
    except Exception as e:
        add_log_entry(f"Error inesperado: {str(e)}", "error")
        return None

def display_results(results):
    """Mostrar resultados del análisis"""
    if not results:
        return
        
    st.markdown("---")
    st.markdown('<h2 class="main-header">📊 Resultados del Análisis</h2>', unsafe_allow_html=True)
    
    # Selector de historial si hay múltiples análisis
    if len(st.session_state.analysis_history) > 1:
        st.subheader("🗂️ Historial de Análisis")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Crear opciones para el selector
            history_options = {
                entry['id']: f"{entry['timestamp'].strftime('%Y-%m-%d %H:%M')} - {entry['label']}"
                for entry in st.session_state.analysis_history
            }
            
            selected_id = st.selectbox(
                "Seleccionar análisis",
                options=list(history_options.keys()),
                format_func=lambda x: history_options[x],
                index=len(history_options) - 1 if st.session_state.selected_analysis_id is None 
                      else list(history_options.keys()).index(st.session_state.selected_analysis_id),
                key="history_selector"
            )
            
            if selected_id != st.session_state.selected_analysis_id:
                st.session_state.selected_analysis_id = selected_id
                st.rerun()
        
        with col2:
            if st.button("🗑️ Limpiar Historial"):
                st.session_state.analysis_history = []
                st.session_state.selected_analysis_id = None
                st.session_state.analysis_results = None
                st.rerun()
    
    # Métricas principales
    summary = results.get('summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📄 Total de Páginas",
            summary.get('total_documents', 0)
        )
    
    with col2:
        st.metric(
            "✅ Páginas con Contenido",
            summary.get('documents_with_content', 0)
        )
    
    with col3:
        st.metric(
            "🔤 Términos Únicos",
            summary.get('total_unique_terms', 0)
        )
    
    with col4:
        elapsed_time = summary.get('elapsed_time_minutes', 0)
        st.metric(
            "⏱️ Tiempo de Análisis",
            f"{elapsed_time:.1f} min"
        )
    
    # Tasa de éxito
    if 'session_stats' in summary:
        success_rate = summary['session_stats'].get('success_rate', 0)
        st.metric("📈 Tasa de Éxito", f"{success_rate:.1f}%")
    
    # Tabs para diferentes visualizaciones
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resultados Agregados", 
        "📅 Resultados por Año",
        "📈 Distribución", 
        "📋 Datos Detallados", 
        "📁 Exportar"
    ])
    
    with tab1:
        display_aggregated_results(results)
    
    with tab2:
        display_yearly_results(results)
    
    with tab3:
        display_frequency_distribution(results)
    
    with tab4:
        display_detailed_data(results)
    
    with tab5:
        display_export_options(results)

def display_aggregated_results(results):
    """Mostrar resultados agregados de todos los años"""
    st.subheader("📊 Top Términos - Todos los Años")
    display_top_terms_chart(results.get('top_terms', []), "Agregado")

def display_yearly_results(results):
    """Mostrar resultados separados por año"""
    results_by_year = results.get('results_by_year', {})
    
    if not results_by_year:
        st.warning("No hay resultados por año disponibles. El análisis puede no haber generado datos separados por año.")
        return
    
    st.subheader("📅 Análisis por Año Individual")
    
    # Selector de año
    years = sorted(results_by_year.keys())
    
    if not years:
        st.info("No hay años disponibles para mostrar")
        return
    
    # Crear tabs para cada año
    year_tabs = st.tabs([f"{year}" for year in years])
    
    for i, year in enumerate(years):
        with year_tabs[i]:
            year_data = results_by_year[year]
            
            # Métricas del año
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 Documentos", year_data.get('document_count', 0))
            
            with col2:
                st.metric("🔤 Términos Únicos", len(year_data.get('frequencies', {})))
            
            with col3:
                top_term = year_data.get('top_terms', [('N/A', 0)])[0]
                st.metric("🏆 Término Top", f"{top_term[0]} ({top_term[1]})")
            
            # Gráfico de términos
            st.subheader(f"Top Términos en {year}")
            display_top_terms_chart(year_data.get('top_terms', []), f"Año {year}")
            
            # Comparación con otros años (opcional)
            if len(years) > 1:
                st.subheader(f"Comparación de {year} con otros años")
                display_year_comparison(results_by_year, year)

def display_year_comparison(results_by_year, current_year):
    """Mostrar comparación de términos entre años"""
    # Obtener top 10 términos del año actual
    current_top = results_by_year[current_year].get('top_terms', [])[:10]
    
    if not current_top:
        return
    
    # Crear DataFrame para comparación
    comparison_data = []
    
    for term, freq in current_top:
        row = {'Término': term, str(current_year): freq}
        
        # Buscar el término en otros años
        for year in sorted(results_by_year.keys()):
            if year != current_year:
                year_freqs = results_by_year[year].get('frequencies', {})
                row[str(year)] = year_freqs.get(term, 0)
        
        comparison_data.append(row)
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Gráfico de barras agrupadas
    fig = go.Figure()
    
    for year in sorted(results_by_year.keys()):
        fig.add_trace(go.Bar(
            name=str(year),
            x=df_comparison['Término'],
            y=df_comparison[str(year)],
        ))
    
    fig.update_layout(
        barmode='group',
        title=f"Frecuencia de Top Términos de {current_year} en Todos los Años",
        xaxis_title="Término",
        yaxis_title="Frecuencia",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_top_terms_chart(top_terms, label=""):
    """Mostrar gráfico de términos más frecuentes"""
    
    if not top_terms:
        st.warning("No se encontraron términos para mostrar")
        return
    
    # Slider para seleccionar número de términos a mostrar
    num_terms = st.slider(
        f"Número de términos a mostrar - {label}", 
        10, 
        min(50, len(top_terms)), 
        20,
        key=f"slider_{label}"
    )
    
    # Crear DataFrame
    df_terms = pd.DataFrame(top_terms[:num_terms], columns=['Término', 'Frecuencia'])
    
    # Gráfico de barras
    fig = px.bar(
        df_terms,
        x='Frecuencia',
        y='Término',
        orientation='h',
        title=f"Top {num_terms} Términos Más Frecuentes - {label}",
        color='Frecuencia',
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        height=max(400, num_terms * 25),
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de términos
    st.subheader(f"📋 Tabla de Términos - {label}")
    st.dataframe(df_terms, use_container_width=True)

def display_top_terms(results):
    """Mostrar términos más frecuentes - función legacy, redirige a la nueva"""
    display_top_terms_chart(results.get('top_terms', []), "Todos los años")

def display_frequency_distribution(results):
    """Mostrar distribución de frecuencias"""
    frequencies = results.get('frequencies', {})
    
    if not frequencies:
        st.warning("No hay datos de frecuencia para mostrar")
        return
    
    # Crear bins para histograma
    freq_values = list(frequencies.values())
    
    # Histograma de distribución
    fig_hist = px.histogram(
        x=freq_values,
        nbins=50,
        title="Distribución de Frecuencias de Términos",
        labels={'x': 'Frecuencia', 'y': 'Número de Términos'}
    )
    
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Estadísticas descriptivas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Estadísticas Descriptivas")
        df_stats = pd.DataFrame({
            'Estadística': ['Media', 'Mediana', 'Desv. Estándar', 'Mínimo', 'Máximo'],
            'Valor': [
                f"{pd.Series(freq_values).mean():.2f}",
                f"{pd.Series(freq_values).median():.2f}",
                f"{pd.Series(freq_values).std():.2f}",
                f"{pd.Series(freq_values).min()}",
                f"{pd.Series(freq_values).max()}"
            ]
        })
        st.dataframe(df_stats, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Términos por Rango de Frecuencia")
        
        # Crear rangos
        ranges = [
            (1, 5, "1-5"),
            (6, 10, "6-10"),
            (11, 25, "11-25"),
            (26, 50, "26-50"),
            (51, 100, "51-100"),
            (101, float('inf'), "100+")
        ]
        
        range_counts = []
        for min_freq, max_freq, label in ranges:
            count = sum(1 for freq in freq_values if min_freq <= freq <= max_freq)
            range_counts.append({'Rango': label, 'Términos': count})
        
        df_ranges = pd.DataFrame(range_counts)
        st.dataframe(df_ranges, use_container_width=True)

def display_detailed_data(results):
    """Mostrar datos detallados"""
    
    # Información de documentos
    documents = results.get('documents', [])
    
    if documents:
        st.subheader("📄 Información de Páginas Web Analizadas")
        
        # Crear DataFrame con metadatos de documentos
        doc_data = []
        for doc in documents[:100]:  # Limitar a 100 para rendimiento
            metadata = doc.get_metadata()
            doc_data.append({
                'Identificador': metadata.get('identifier', ''),
                'Título': metadata.get('title', '')[:50] + '...' if len(metadata.get('title', '')) > 50 else metadata.get('title', ''),
                'Año': metadata.get('year', ''),
                'URL Original': metadata.get('original_url', ''),
                'Longitud Contenido': metadata.get('content_length', 0)
            })
        
        df_docs = pd.DataFrame(doc_data)
        st.dataframe(df_docs, use_container_width=True)
        
        # Gráfico de páginas por año
        years = [doc.year for doc in documents if doc.year]
        if years:
            year_counts = pd.Series(years).value_counts().sort_index()
            
            fig_years = px.bar(
                x=year_counts.index,
                y=year_counts.values,
                title="Distribución de Páginas Web por Año",
                labels={'x': 'Año', 'y': 'Número de Páginas'}
            )
            
            st.plotly_chart(fig_years, use_container_width=True)
    
    # Metadatos del análisis
    st.subheader("🔍 Metadatos del Análisis")
    analysis_metadata = results.get('analysis_metadata', {})
    
    metadata_df = pd.DataFrame([
        {'Campo': 'Versión del Analizador', 'Valor': analysis_metadata.get('analyzer_version', 'N/A')},
        {'Campo': 'Fecha de Análisis', 'Valor': analysis_metadata.get('analysis_date', 'N/A')},
        {'Campo': 'Total de Términos Analizados', 'Valor': analysis_metadata.get('total_terms_analyzed', 'N/A')},
        {'Campo': 'Páginas Procesadas', 'Valor': analysis_metadata.get('documents_processed', 'N/A')}
    ])
    
    st.dataframe(metadata_df, use_container_width=True)

def display_export_options(results):
    """Mostrar opciones de exportación"""
    st.subheader("📁 Exportar Resultados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Top Términos (CSV)")
        
        # Preparar CSV de términos
        top_terms = results.get('top_terms', [])
        if top_terms:
            df_export = pd.DataFrame(top_terms, columns=['Término', 'Frecuencia'])
            csv_data = df_export.to_csv(index=False)
            
            st.download_button(
                label="Descargar CSV",
                data=csv_data,
                file_name=f"top_terms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.subheader("📋 Datos Completos (JSON)")
        
        # Preparar JSON (serializable)
        export_data = {
            'summary': results.get('summary', {}),
            'top_terms': results.get('top_terms', []),
            'analysis_metadata': results.get('analysis_metadata', {}),
            'frequencies': dict(list(results.get('frequencies', {}).items())[:1000])  # Limitar para tamaño
        }
        
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
        
        st.download_button(
            label="Descargar JSON",
            data=json_data,
            file_name=f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def main():
    """Función principal de la aplicación"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🔍 Historical Term Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Análisis de términos en páginas web históricas usando Internet Archive</p>', unsafe_allow_html=True)
    
    # Sidebar con configuración
    config = create_sidebar()
    
    if not config:
        st.error("Por favor, revisa la configuración en la barra lateral")
        return
    
    if not config['domains']:
        st.error("Debes seleccionar al menos un dominio para analizar")
        return
    
    # Área principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🚀 Iniciar Análisis")
        
        # Mostrar contenido según el estado
        if not st.session_state.analysis_running:
            # Mostrar botón solo cuando NO está ejecutando
            if st.button("▶️ Ejecutar Análisis", type="primary", key="run_button"):
                st.session_state.analysis_running = True
                st.session_state.analysis_log = []
                st.session_state.analysis_progress = 0
                st.session_state.analysis_status = "Iniciando..."
                st.rerun()
        else:
            # Ejecutando análisis - NO mostrar botón
            st.info("⏳ Análisis en progreso... Por favor espera.")
            
            # Botón de cancelar
            col_cancel1, col_cancel2 = st.columns([1, 4])
            with col_cancel1:
                if st.button("⏹️ Cancelar", type="secondary", key="cancel_button"):
                    st.session_state.cancel_requested = True
                    add_log_entry("Cancelación solicitada por el usuario", "warning")
            
            # Crear placeholders para actualización en tiempo real
            progress_bar = st.progress(0)
            progress_text = st.empty()
            status_placeholder = st.empty()
            
            # Callback para actualizar UI en tiempo real
            def update_progress(percent, message):
                # Verificar si se solicitó cancelación
                if st.session_state.cancel_requested:
                    raise InterruptedError("Análisis cancelado por el usuario")
                
                st.session_state.analysis_progress = percent
                st.session_state.analysis_status = message
                add_log_entry(message, "info")
                progress_bar.progress(percent / 100.0)
                progress_text.text(f"{percent}% - {message}")
            
            # Ejecutar análisis con callback personalizado
            try:
                analyzer = HistoricalTermAnalyzer(
                    rate_limit_delay=config['rate_limit'],
                    progress_callback=update_progress
                )
                
                analyzer.processor.use_parallel = config['use_parallel']
                
                results = analyzer.analyze_period(
                    start_year=config['start_year'],
                    end_year=config['end_year'],
                    max_documents=config['max_documents'],
                    domains=config['domains'],
                    analyze_by_year=True
                )
                
                if results and 'error' not in results:
                    results['config'] = {
                        'start_year': config['start_year'],
                        'end_year': config['end_year'],
                        'max_documents': config['max_documents'],
                        'domains': config['domains'],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    st.session_state.analysis_results = results
                    add_to_history(results)
                    status_placeholder.success("✅ Análisis completado exitosamente")
                else:
                    error_msg = results.get('error', 'Error desconocido') if results else 'Error desconocido'
                    status_placeholder.error(f"❌ Error durante el análisis: {error_msg}")
                
            except InterruptedError as e:
                status_placeholder.warning(f"⚠️ {str(e)}")
                add_log_entry(f"Análisis cancelado: {str(e)}", "warning")
                
            except Exception as e:
                status_placeholder.error(f"❌ Error inesperado: {str(e)}")
                add_log_entry(f"Error: {str(e)}", "error")
            
            finally:
                st.session_state.analysis_running = False
                st.session_state.cancel_requested = False
                time.sleep(2)
                st.rerun()
    
    with col2:
        display_log()
    
    # Mostrar resultados si están disponibles
    results_to_display = get_selected_results()
    if results_to_display:
        display_results(results_to_display)

if __name__ == "__main__":
    main()