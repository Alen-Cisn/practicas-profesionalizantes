#!/usr/bin/env python3
"""
Ejemplo de Procesamiento por Lotes
Demuestra cómo procesar múltiples consultas y análisis automatizados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from historical_term_analyzer import HistoricalTermAnalyzer
import json
import time
from datetime import datetime


def batch_analysis_by_years():
    """
    Análisis por lotes dividido por años individuales
    """
    
    print("="*60)
    print("PROCESAMIENTO POR LOTES - ANÁLISIS POR AÑOS")
    print("="*60)
    print()
    
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=4.0)
    
    # Definir años a analizar
    target_years = [1996, 1998, 2000, 2002, 2004]
    
    batch_results = {}
    total_start_time = time.time()
    
    print(f"📅 Analizando {len(target_years)} años individuales:")
    print(f"Años objetivo: {target_years}")
    print()
    
    for i, year in enumerate(target_years, 1):
        print(f"🔍 Procesando año {year} ({i}/{len(target_years)})...")
        year_start_time = time.time()
        
        try:
            # Análisis de un solo año
            results = analyzer.analyze_period(
                start_year=year,
                end_year=year,
                max_documents=25,  # Documentos por año
                language='eng'
            )
            
            if 'error' not in results:
                year_duration = time.time() - year_start_time
                
                batch_results[str(year)] = {
                    'year': year,
                    'processing_time_minutes': year_duration / 60,
                    'documents_found': results['summary']['total_documents'],
                    'documents_with_content': results['summary']['documents_with_content'],
                    'unique_terms': results['summary']['total_unique_terms'],
                    'top_10_terms': results['top_terms'][:10]
                }
                
                print(f"  ✅ Completado en {year_duration/60:.1f} min")
                print(f"  📄 {results['summary']['total_documents']} documentos procesados")
                print(f"  🔤 {results['summary']['total_unique_terms']} términos únicos")
                
            else:
                print(f"  ❌ Error en año {year}: {results['error']}")
                batch_results[str(year)] = {'error': results['error']}
                
        except Exception as e:
            print(f"  ❌ Excepción en año {year}: {e}")
            batch_results[str(year)] = {'exception': str(e)}
        
        print()
    
    total_duration = time.time() - total_start_time
    
    # Generar resumen del lote
    print("📊 RESUMEN DEL PROCESAMIENTO POR LOTES:")
    print("=" * 50)
    print(f"Tiempo total: {total_duration/60:.1f} minutos")
    print(f"Años procesados exitosamente: {len([r for r in batch_results.values() if 'error' not in r and 'exception' not in r])}")
    print()
    
    # Mostrar estadísticas por año
    for year, data in batch_results.items():
        if 'error' not in data and 'exception' not in data:
            print(f"📅 {year}:")
            print(f"  Documentos: {data['documents_with_content']}")
            print(f"  Términos únicos: {data['unique_terms']}")
            if data['top_10_terms']:
                top_3 = data['top_10_terms'][:3]
                print(f"  Top 3: {', '.join([f'{term}({freq})' for term, freq in top_3])}")
            print()
    
    # Exportar resultados del lote
    batch_metadata = {
        'batch_info': {
            'processing_date': datetime.now().isoformat(),
            'total_processing_time_minutes': total_duration / 60,
            'years_processed': target_years,
            'successful_years': len([r for r in batch_results.values() if 'error' not in r]),
            'documents_per_year': 25
        },
        'results': batch_results
    }
    
    with open('batch_analysis_by_years.json', 'w', encoding='utf-8') as f:
        json.dump(batch_metadata, f, indent=2, ensure_ascii=False)
    
    print("📁 Resultados del lote exportados a: batch_analysis_by_years.json")
    
    return batch_results


def batch_thematic_analysis():
    """
    Análisis por lotes de diferentes temáticas
    """
    
    print("\n" + "="*60)
    print("PROCESAMIENTO TEMÁTICO POR LOTES")
    print("="*60)
    print()
    
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=4.5)
    
    # Definir temáticas con sus términos específicos
    themes = {
        'Technology': ['computer', 'software', 'digital', 'technology', 'programming'],
        'Internet': ['internet', 'website', 'web', 'online', 'email', 'browser'],
        'Business': ['business', 'company', 'market', 'economy', 'commerce', 'financial'],
        'Communication': ['communication', 'media', 'news', 'information', 'network']
    }
    
    thematic_results = {}
    
    print(f"🎯 Analizando {len(themes)} temáticas diferentes:")
    for theme in themes.keys():
        print(f"  • {theme}")
    print()
    
    for theme, keywords in themes.items():
        print(f"🔍 Procesando temática: {theme}")
        print(f"  Palabras clave: {', '.join(keywords[:3])}...")
        
        try:
            results = analyzer.analyze_period(
                start_year=1997,
                end_year=2003,
                max_documents=40,
                language='eng',
                search_terms=keywords
            )
            
            if 'error' not in results:
                # Filtrar términos relacionados con la temática
                theme_terms = {}
                for term, freq in results['frequencies'].items():
                    if (term in keywords or 
                        any(keyword.lower() in term.lower() for keyword in keywords)):
                        theme_terms[term] = freq
                
                theme_top = sorted(theme_terms.items(), key=lambda x: x[1], reverse=True)[:10]
                
                thematic_results[theme] = {
                    'keywords_searched': keywords,
                    'total_documents': results['summary']['total_documents'],
                    'documents_with_content': results['summary']['documents_with_content'],
                    'theme_specific_terms': len(theme_terms),
                    'top_theme_terms': theme_top,
                    'processing_time': results['summary']['elapsed_time_minutes']
                }
                
                print(f"  ✅ {results['summary']['total_documents']} docs, {len(theme_terms)} términos temáticos")
                
            else:
                print(f"  ❌ Error: {results['error']}")
                thematic_results[theme] = {'error': results['error']}
                
        except Exception as e:
            print(f"  ❌ Excepción: {e}")
            thematic_results[theme] = {'exception': str(e)}
        
        print()
    
    # Mostrar comparativa temática
    print("📈 COMPARATIVA TEMÁTICA:")
    print("=" * 40)
    
    for theme, data in thematic_results.items():
        if 'error' not in data and 'exception' not in data:
            print(f"\n🎯 {theme}:")
            print(f"  Documentos procesados: {data['documents_with_content']}")
            print(f"  Términos temáticos encontrados: {data['theme_specific_terms']}")
            if data['top_theme_terms']:
                print(f"  Término principal: {data['top_theme_terms'][0][0]} ({data['top_theme_terms'][0][1]} veces)")
    
    # Exportar análisis temático
    thematic_metadata = {
        'thematic_batch_info': {
            'processing_date': datetime.now().isoformat(),
            'period_analyzed': '1997-2003',
            'themes_count': len(themes),
            'documents_per_theme': 40
        },
        'themes': thematic_results
    }
    
    with open('batch_thematic_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(thematic_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Análisis temático exportado a: batch_thematic_analysis.json")
    
    return thematic_results


def automated_quality_report(batch_results, thematic_results):
    """
    Generar reporte automatizado de calidad del procesamiento por lotes
    """
    
    print("\n" + "="*60)
    print("REPORTE AUTOMATIZADO DE CALIDAD")
    print("="*60)
    print()
    
    # Análisis de calidad por años
    years_analysis = {
        'successful_years': 0,
        'failed_years': 0,
        'total_documents': 0,
        'avg_unique_terms': 0,
        'processing_efficiency': []
    }
    
    successful_year_data = []
    for year, data in batch_results.items():
        if 'error' not in data and 'exception' not in data:
            years_analysis['successful_years'] += 1
            years_analysis['total_documents'] += data['documents_with_content']
            successful_year_data.append(data)
        else:
            years_analysis['failed_years'] += 1
    
    if successful_year_data:
        years_analysis['avg_unique_terms'] = sum(d['unique_terms'] for d in successful_year_data) / len(successful_year_data)
        years_analysis['avg_processing_time'] = sum(d['processing_time_minutes'] for d in successful_year_data) / len(successful_year_data)
    
    # Análisis de calidad temático
    themes_analysis = {
        'successful_themes': 0,
        'failed_themes': 0,
        'total_thematic_documents': 0,
        'themes_efficiency': {}
    }
    
    for theme, data in thematic_results.items():
        if 'error' not in data and 'exception' not in data:
            themes_analysis['successful_themes'] += 1
            themes_analysis['total_thematic_documents'] += data['documents_with_content']
            themes_analysis['themes_efficiency'][theme] = {
                'docs_per_minute': data['documents_with_content'] / max(data['processing_time'], 0.1),
                'terms_found': data['theme_specific_terms']
            }
        else:
            themes_analysis['failed_themes'] += 1
    
    # Generar reporte
    quality_report = {
        'report_metadata': {
            'generated_at': datetime.now().isoformat(),
            'report_type': 'batch_processing_quality'
        },
        'yearly_analysis': years_analysis,
        'thematic_analysis': themes_analysis,
        'overall_metrics': {
            'total_processing_success_rate': (
                (years_analysis['successful_years'] + themes_analysis['successful_themes']) /
                max((years_analysis['successful_years'] + years_analysis['failed_years'] + 
                     themes_analysis['successful_themes'] + themes_analysis['failed_themes']), 1)
            ) * 100,
            'total_documents_processed': years_analysis['total_documents'] + themes_analysis['total_thematic_documents']
        },
        'recommendations': []
    }
    
    # Generar recomendaciones
    if years_analysis['failed_years'] > 0:
        quality_report['recommendations'].append(
            f"Se encontraron {years_analysis['failed_years']} años con errores. "
            "Considere verificar la conectividad y aumentar el rate_limit_delay."
        )
    
    if themes_analysis['failed_themes'] > 0:
        quality_report['recommendations'].append(
            f"Se encontraron {themes_analysis['failed_themes']} temáticas con errores. "
            "Considere usar términos de búsqueda más específicos."
        )
    
    if quality_report['overall_metrics']['total_processing_success_rate'] > 90:
        quality_report['recommendations'].append("Excelente tasa de éxito en el procesamiento por lotes.")
    elif quality_report['overall_metrics']['total_processing_success_rate'] > 70:
        quality_report['recommendations'].append("Buena tasa de éxito, pero hay margen de mejora.")
    else:
        quality_report['recommendations'].append("Baja tasa de éxito. Revise configuración y conectividad.")
    
    # Mostrar reporte
    print("📋 MÉTRICAS DE CALIDAD:")
    print(f"✅ Años procesados exitosamente: {years_analysis['successful_years']}")
    print(f"❌ Años con errores: {years_analysis['failed_years']}")
    print(f"✅ Temáticas procesadas exitosamente: {themes_analysis['successful_themes']}")
    print(f"❌ Temáticas con errores: {themes_analysis['failed_themes']}")
    print(f"📊 Tasa de éxito general: {quality_report['overall_metrics']['total_processing_success_rate']:.1f}%")
    print(f"📄 Total de documentos procesados: {quality_report['overall_metrics']['total_documents_processed']}")
    
    if years_analysis['avg_unique_terms']:
        print(f"🔤 Promedio de términos únicos por año: {years_analysis['avg_unique_terms']:.0f}")
    
    print("\n💡 RECOMENDACIONES:")
    for i, rec in enumerate(quality_report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # Exportar reporte
    with open('batch_quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(quality_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Reporte de calidad exportado a: batch_quality_report.json")
    
    return quality_report


def main():
    """Función principal para procesamiento por lotes"""
    
    print("🔄 PROCESAMIENTO POR LOTES - ANALIZADOR HISTÓRICO")
    print("Este script ejecuta múltiples análisis automáticamente")
    print()
    
    try:
        # Ejecutar análisis por años
        batch_results = batch_analysis_by_years()
        
        # Ejecutar análisis temático
        thematic_results = batch_thematic_analysis()
        
        # Generar reporte de calidad
        quality_report = automated_quality_report(batch_results, thematic_results)
        
        print("\n" + "="*60)
        print("✅ PROCESAMIENTO POR LOTES COMPLETADO")
        print("Se han generado los siguientes archivos:")
        print("  • batch_analysis_by_years.json - Análisis por años")
        print("  • batch_thematic_analysis.json - Análisis temático")
        print("  • batch_quality_report.json - Reporte de calidad")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Procesamiento por lotes interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado en procesamiento por lotes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()