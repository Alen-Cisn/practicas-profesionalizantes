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
    if 'analysis_log' not in st.session_state:
        st.session_state.analysis_log = []

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
        min_value=1.0,
        max_value=10.0,
        value=4.0,
        step=0.5,
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
    try:
        # Inicializar analizador
        add_log_entry("Inicializando analizador...", "info")
        analyzer = HistoricalTermAnalyzer(rate_limit_delay=config['rate_limit'])
        
        # Configurar procesamiento paralelo
        analyzer.processor.use_parallel = config['use_parallel']
        
        add_log_entry(f"Analizando período {config['start_year']}-{config['end_year']}", "info")
        add_log_entry(f"Dominios: {', '.join(config['domains'])}", "info")
        add_log_entry(f"Máximo de páginas: {config['max_documents']}", "info")
        
        # Ejecutar análisis
        results = analyzer.analyze_period(
            start_year=config['start_year'],
            end_year=config['end_year'],
            max_documents=config['max_documents'],
            domains=config['domains']
        )
        
        if 'error' in results:
            add_log_entry(f"Error en análisis: {results['error']}", "error")
            return None
        
        add_log_entry("Análisis completado exitosamente", "success")
        
        # Agregar estadísticas del cache si está disponible
        if hasattr(analyzer.processor, 'get_cache_stats'):
            cache_stats = analyzer.processor.get_cache_stats()
            add_log_entry(f"Cache hit rate: {cache_stats['hit_rate_percent']}%", "info")
        
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
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Top Términos", "📈 Distribución", "📋 Datos Detallados", "📁 Exportar"])
    
    with tab1:
        display_top_terms(results)
    
    with tab2:
        display_frequency_distribution(results)
    
    with tab3:
        display_detailed_data(results)
    
    with tab4:
        display_export_options(results)

def display_top_terms(results):
    """Mostrar términos más frecuentes"""
    top_terms = results.get('top_terms', [])
    
    if not top_terms:
        st.warning("No se encontraron términos para mostrar")
        return
    
    # Slider para seleccionar número de términos a mostrar
    num_terms = st.slider("Número de términos a mostrar", 10, min(50, len(top_terms)), 20)
    
    # Crear DataFrame
    df_terms = pd.DataFrame(top_terms[:num_terms], columns=['Término', 'Frecuencia'])
    
    # Gráfico de barras
    fig = px.bar(
        df_terms,
        x='Frecuencia',
        y='Término',
        orientation='h',
        title=f"Top {num_terms} Términos Más Frecuentes",
        color='Frecuencia',
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        height=max(400, num_terms * 25),
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de términos
    st.subheader("📋 Tabla de Términos")
    st.dataframe(df_terms, use_container_width=True)

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
        
        if st.button("▶️ Ejecutar Análisis", type="primary", disabled=st.session_state.analysis_running):
            st.session_state.analysis_running = True
            st.session_state.analysis_log = []
            
            # Contenedor para el progreso
            progress_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Iniciando análisis...")
                progress_bar.progress(10)
                
                # Ejecutar análisis
                results = run_analysis(config)
                
                progress_bar.progress(100)
                status_text.text("¡Análisis completado!")
                
                if results:
                    st.session_state.analysis_results = results
                    st.success("✅ Análisis completado exitosamente")
                else:
                    st.error("❌ Error durante el análisis. Revisa el log para más detalles.")
                
                st.session_state.analysis_running = False
                
                # Rerun para mostrar resultados
                time.sleep(1)
                st.rerun()
    
    with col2:
        display_log()
    
    # Mostrar resultados si están disponibles
    if st.session_state.analysis_results:
        display_results(st.session_state.analysis_results)

if __name__ == "__main__":
    main()