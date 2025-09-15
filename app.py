"""
Aplicación Streamlit: Minería de datos - medidas de tendencia central y visualizaciones
Archivo: app_mineria_datos.py
Descripción:
- Permite cargar un dataset (Excel o CSV) o usar el dataset de ejemplo incluido.
- Calcula medidas (media, mediana, moda) para EDAD y SALARIO, además de otras agrupadas.
- Genera gráficos (histograma, boxplot, scatter, barras) y los muestra en la app.
- Permite descargar: dataset original, tabla resumen (CSV) y reporte PDF con resultados y figuras.

Requisitos:
pip install streamlit pandas numpy matplotlib openpyxl xlrd scipy

Ejecución:
streamlit run app_mineria_datos.py

Autor: Generado por ChatGPT para la asignatura de Minería de Datos
Comentarios: los comentarios y textos están en español.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO
from scipy import stats

# -------------------- Utilidades --------------------

def cargar_dataset(uploaded_file):
    """Carga archivo Excel o CSV y devuelve DataFrame."""
    if uploaded_file is None:
        return None
    name = uploaded_file.name.lower()
    try:
        if name.endswith('.xlsx') or name.endswith('.xls'):
            df = pd.read_excel(uploaded_file)
        elif name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            st.error('Formato no soportado. Use .xlsx, .xls o .csv')
            return None
        # Limpiar nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f'Error al cargar el archivo: {e}')
        return None


def detectar_columnas(df):
    """Intento robusto de mapear columnas esperadas a nombres reales del DataFrame."""
    cols = {c.lower(): c for c in df.columns}
    def buscar(variantes):
        for v in variantes:
            if v.lower() in cols:
                return cols[v.lower()]
        # búsqueda por contiene
        for key, orig in cols.items():
            for v in variantes:
                if v.lower() in key:
                    return orig
        return None

    mapping = {}
    mapping['edad'] = buscar(['edad', 'age'])
    mapping['salario'] = buscar(['salario', 'salary', 'ingreso', 'income'])
    mapping['mascota'] = buscar(['tiene_mascota', 'mascota', 'pet'])
    mapping['nivel'] = buscar(['nivel_escolar', 'nivel', 'educacion', 'education'])
    mapping['marca_auto'] = buscar(['marca_auto', 'marca de auto', 'marca', 'car_brand'])
    mapping['hijos'] = buscar(['num_hijos', 'hijos', 'children'])
    mapping['sexo'] = buscar(['sexo', 'gender', 'sex'])
    mapping['estatura'] = buscar(['estatura', 'altura', 'height'])
    return mapping


def calcular_medidas(df, mapping):
    """Calcula medidas solicitadas y devuelve un diccionario con resultados y tablas auxiliares."""
    res = {}
    # EDAD
    if mapping['edad'] and mapping['edad'] in df.columns:
        edad = pd.to_numeric(df[mapping['edad']], errors='coerce')
        res['edad_mean'] = float(edad.mean()) if not edad.dropna().empty else np.nan
        res['edad_median'] = float(edad.median()) if not edad.dropna().empty else np.nan
        modes = edad.mode()
        res['edad_mode'] = float(modes.iloc[0]) if not modes.empty else np.nan
        res['edad_series'] = edad
    else:
        res['edad_mean'] = res['edad_median'] = res['edad_mode'] = np.nan
        res['edad_series'] = pd.Series(dtype=float)

    # SALARIO
    if mapping['salario'] and mapping['salario'] in df.columns:
        salario = pd.to_numeric(df[mapping['salario']], errors='coerce')
        res['salario_mean'] = float(salario.mean()) if not salario.dropna().empty else np.nan
        res['salario_median'] = float(salario.median()) if not salario.dropna().empty else np.nan
        res['salario_series'] = salario
    else:
        res['salario_mean'] = res['salario_median'] = np.nan
        res['salario_series'] = pd.Series(dtype=float)

    # Mascota: media de edad con/sin mascota
    if mapping['mascota'] and mapping['mascota'] in df.columns and not res['edad_series'].empty:
        pet = df[mapping['mascota']].astype(str).str.lower().fillna('')
        tiene = pet.str.contains('sí|si|s|yes|true|1')
        res['edad_media_con_mascota'] = float(res['edad_series'][tiene].mean()) if tiene.any() else np.nan
        res['edad_media_sin_mascota'] = float(res['edad_series'][~tiene].mean()) if (~tiene).any() else np.nan
        res['pet_counts'] = {'con': int(tiene.sum()), 'sin': int((~tiene).sum())}
    else:
        res['edad_media_con_mascota'] = res['edad_media_sin_mascota'] = np.nan
        res['pet_counts'] = {'con': 0, 'sin': 0}

    # Salario por nivel educativo
    if mapping['nivel'] and mapping['nivel'] in df.columns and mapping['salario'] and mapping['salario'] in df.columns:
        tabla = df[[mapping['nivel'], mapping['salario']]].copy()
        tabla[mapping['salario']] = pd.to_numeric(tabla[mapping['salario']], errors='coerce')
        salario_por_nivel = tabla.groupby(mapping['nivel'])[mapping['salario']].mean().sort_values(ascending=False)
        res['salario_por_nivel'] = salario_por_nivel
    else:
        res['salario_por_nivel'] = pd.Series(dtype=float)

    # Marca de auto conteo
    if mapping['marca_auto'] and mapping['marca_auto'] in df.columns:
        marcas = df[mapping['marca_auto']].astype(str).fillna('Sin especificar')
        res['marca_counts'] = marcas.value_counts()
    else:
        res['marca_counts'] = pd.Series(dtype=int)

    # Hijos
    if mapping['hijos'] and mapping['hijos'] in df.columns:
        hijos = pd.to_numeric(df[mapping['hijos']], errors='coerce')
        res['hijos_mean'] = float(hijos.mean()) if not hijos.dropna().empty else np.nan
        res['hijos_median'] = float(hijos.median()) if not hijos.dropna().empty else np.nan
    else:
        res['hijos_mean'] = res['hijos_median'] = np.nan

    # Salario por sexo
    if mapping['sexo'] and mapping['sexo'] in df.columns and mapping['salario'] and mapping['salario'] in df.columns:
        s = df[[mapping['sexo'], mapping['salario']]].copy()
        s[mapping['salario']] = pd.to_numeric(s[mapping['salario']], errors='coerce')
        res['salario_por_sexo'] = s.groupby(mapping['sexo'])[mapping['salario']].mean()
    else:
        res['salario_por_sexo'] = pd.Series(dtype=float)

    # Estatura por nivel
    if mapping['estatura'] and mapping['estatura'] in df.columns and mapping['nivel'] and mapping['nivel'] in df.columns:
        e = df[[mapping['nivel'], mapping['estatura']]].copy()
        e[mapping['estatura']] = pd.to_numeric(e[mapping['estatura']], errors='coerce')
        res['estatura_por_nivel'] = e.groupby(mapping['nivel'])[mapping['estatura']].mean()
    else:
        res['estatura_por_nivel'] = pd.Series(dtype=float)

    return res


def crear_figuras(res, mapping, df):
    """Crea y devuelve una lista de figuras matplotlib con las visualizaciones principales."""
    figs = []
    plt.close('all')

    # Histograma EDAD
    if not res['edad_series'].empty:
        fig1, ax1 = plt.subplots()
        ax1.hist(res['edad_series'].dropna(), bins=15)
        ax1.set_title('Histograma: EDAD')
        ax1.set_xlabel('Edad')
        ax1.set_ylabel('Frecuencia')
        figs.append(fig1)

    # Boxplot SALARIO
    if not res['salario_series'].empty:
        fig2, ax2 = plt.subplots()
        ax2.boxplot(res['salario_series'].dropna().values, vert=True)
        ax2.set_title('Boxplot: SALARIO')
        ax2.set_ylabel('Salario')
        figs.append(fig2)

    # Boxplot EDAD por nivel
    if isinstance(res['salario_por_nivel'], pd.Series) and not res['salario_por_nivel'].empty and mapping['nivel'] in df.columns:
        # usar edad por nivel
        groups = []
        labels = []
        for name, group in df.groupby(mapping['nivel']):
            edad_g = pd.to_numeric(group[mapping['edad']], errors='coerce').dropna()
            if len(edad_g) > 0:
                groups.append(edad_g)
                labels.append(str(name))
        if groups:
            fig3, ax3 = plt.subplots(figsize=(8,4))
            ax3.boxplot(groups, labels=labels)
            ax3.set_title('Boxplot: EDAD por NIVEL ESCOLAR')
            ax3.set_xlabel('Nivel escolar')
            ax3.set_ylabel('Edad')
            plt.xticks(rotation=45)
            figs.append(fig3)

    # Scatter EDAD vs SALARIO
    if not res['edad_series'].empty and not res['salario_series'].empty:
        fig4, ax4 = plt.subplots()
        ax4.scatter(res['edad_series'], res['salario_series'])
        ax4.set_title('Scatter: EDAD vs SALARIO')
        ax4.set_xlabel('Edad')
        ax4.set_ylabel('Salario')
        figs.append(fig4)

    # Barra marcas de auto
    if isinstance(res['marca_counts'], pd.Series) and not res['marca_counts'].empty:
        fig5, ax5 = plt.subplots(figsize=(8,4))
        res['marca_counts'].plot(kind='bar', ax=ax5)
        ax5.set_title('Número de personas por MARCA DE AUTO')
        ax5.set_xlabel('Marca de auto')
        ax5.set_ylabel('Cantidad')
        plt.xticks(rotation=45)
        figs.append(fig5)

    # Barra mascotas
    if res['pet_counts']['con'] + res['pet_counts']['sin'] > 0:
        fig6, ax6 = plt.subplots()
        ax6.bar(['con_mascota', 'sin_mascota'], [res['pet_counts']['con'], res['pet_counts']['sin']])
        ax6.set_title('Personas con y sin mascota')
        ax6.set_ylabel('Cantidad')
        figs.append(fig6)

    # Salario por sexo
    if isinstance(res['salario_por_sexo'], pd.Series) and not res['salario_por_sexo'].empty:
        fig7, ax7 = plt.subplots()
        res['salario_por_sexo'].plot(kind='bar', ax=ax7)
        ax7.set_title('Salario promedio por sexo')
        ax7.set_ylabel('Salario promedio')
        figs.append(fig7)

    # Estatura por nivel
    if isinstance(res['estatura_por_nivel'], pd.Series) and not res['estatura_por_nivel'].empty:
        fig8, ax8 = plt.subplots()
        res['estatura_por_nivel'].plot(kind='bar', ax=ax8)
        ax8.set_title('Estatura promedio por nivel escolar')
        ax8.set_ylabel('Estatura promedio')
        figs.append(fig8)

    return figs


def generar_pdf_bytes(res, figs, df):
    """Genera un PDF en memoria (bytes) con los resultados y figuras. Devuelve bytes."""
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        # Página 1: Resumen numérico
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        title = 'Informe: Medidas de tendencia central y visualizaciones'
        ax.text(0.5, 0.95, title, ha='center', fontsize=14)
        y = 0.9
        line_h = 0.04
        ax.text(0.05, y, f"Edad - media: {res.get('edad_mean', np.nan):.2f}  mediana: {res.get('edad_median', np.nan):.2f}  moda: {res.get('edad_mode', np.nan)}", fontsize=10)
        y -= line_h
        ax.text(0.05, y, f"Salario - media: {res.get('salario_mean', np.nan):.2f}  mediana: {res.get('salario_median', np.nan):.2f}", fontsize=10)
        y -= line_h
        ax.text(0.05, y, f"Edad media CON mascota: {res.get('edad_media_con_mascota', np.nan):.2f}   SIN mascota: {res.get('edad_media_sin_mascota', np.nan):.2f}", fontsize=10)
        y -= line_h
        ax.text(0.05, y, f"Hijos - media: {res.get('hijos_mean', np.nan):.2f}  mediana: {res.get('hijos_median', np.nan):.2f}", fontsize=10)
        y -= line_h
        pdf.savefig(fig)
        plt.close(fig)

        # Figuras
        for f in figs:
            pdf.savefig(f)
            plt.close(f)

        # Página final: conclusiones breves
        figc, axc = plt.subplots(figsize=(8.27, 11.69))
        axc.axis('off')
        conclusions = [
            'Conclusiones (resumen):',
            '- Diferencias entre media y mediana pueden indicar asimetría y valores extremos.',
            "- Revisar violin/boxplot para detectar outliers en salario.",
            '- Comparar salario por nivel educativo para ver tendencia de aumento con educación.'
        ]
        y = 0.9
        for line in conclusions:
            axc.text(0.05, y, line, fontsize=11)
            y -= 0.04
        pdf.savefig(figc)
        plt.close(figc)

    buffer.seek(0)
    return buffer.read()


# -------------------- Interfaz Streamlit --------------------

st.set_page_config(page_title='Minería de Datos - App', layout='wide')
st.title('Minería de Datos: Medidas de tendencia central y visualizaciones')
st.markdown('''
Sube el dataset (Excel o CSV). La aplicación calculará medidas estadísticas y generará gráficos. 
Podrás descargar el dataset original, una tabla resumen en CSV y un informe en PDF con las figuras.
''')

# Sidebar: opciones y carga
st.sidebar.header('Cargar y opciones')
uploaded = st.sidebar.file_uploader('Cargar archivo (.xlsx, .xls, .csv)', type=['xlsx','xls','csv'])
use_example = st.sidebar.checkbox('Usar dataset de ejemplo incluido (si aplica)', value=False)

# Si se desea, también permitir URL? (no implementado para simplicidad)

# Cargar dataset
if uploaded is None and not use_example:
    st.info('Sube un archivo o marca "Usar dataset de ejemplo" para continuar.')
    # Mostrar ejemplo mínimo instructivo
    if st.button('Mostrar ejemplo de estructura esperada'):
        st.write(pd.DataFrame({
            'EDAD': [23, 45, 34],
            'SALARIO': [1200, 2500, 1800],
            'TIENE_MASCOTA': ['si', 'no', 'si'],
            'NIVEL_ESCOLAR': ['Secundaria', 'Universidad', 'Técnico']
        }))
else:
    # Cargar archivo o usar dataset existente en el servidor (si el usuario ya subió anteriormente al entorno)
    if use_example and uploaded is None:
        try:
            example_path = 'data/DATASET 500.xlsx'
            df_raw = pd.read_excel(example_path)
            st.success('Dataset de ejemplo cargado desde el repositorio.')
        except Exception as e:
            st.error(f'No se encontró dataset de ejemplo. Error: {e}')
            df_raw = None
    else:
        df_raw = cargar_dataset(uploaded)

    if df_raw is not None:
        st.subheader('Preview del dataset (primeras filas)')
        st.dataframe(df_raw.head(20))

        # Detectar columnas
        mapping = detectar_columnas(df_raw)
        st.sidebar.subheader('Mapeo automático de columnas (revise y corrija si necesario)')
        # Mostrar mapeo y permitir corrección manual
        keys = list(mapping.keys())
        for k in keys:
            col_selected = st.sidebar.selectbox(f"Columna para '{k}'", options=['(ninguna)'] + list(df_raw.columns), index=(0 if mapping[k] is None else (list(df_raw.columns).index(mapping[k]) + 1)))
            mapping[k] = None if col_selected == '(ninguna)' else col_selected

        # Botón calcular
        if st.sidebar.button('Calcular medidas y generar visualizaciones'):
            with st.spinner('Calculando...'):
                res = calcular_medidas(df_raw, mapping)
                figs = crear_figuras(res, mapping, df_raw)

            # Mostrar resultados numéricos
            st.subheader('Medidas calculadas')
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('**EDAD**')
                st.write({
                    'media': res.get('edad_mean'),
                    'mediana': res.get('edad_median'),
                    'moda': res.get('edad_mode')
                })
                st.markdown('**SALARIO**')
                st.write({
                    'media': res.get('salario_mean'),
                    'mediana': res.get('salario_median')
                })
                st.markdown('**Hijos**')
                st.write({
                    'media': res.get('hijos_mean'),
                    'mediana': res.get('hijos_median')
                })
            with col2:
                st.markdown('**Edad según mascota**')
                st.write({
                    'edad_media_con_mascota': res.get('edad_media_con_mascota'),
                    'edad_media_sin_mascota': res.get('edad_media_sin_mascota')
                })
                st.markdown('**Conteos mascotas**')
                st.write(res.get('pet_counts'))

            # Mostrar tablas de agrupación
            if isinstance(res['salario_por_nivel'], pd.Series) and not res['salario_por_nivel'].empty:
                st.subheader('Salario promedio por nivel educativo')
                st.table(res['salario_por_nivel'].reset_index().rename(columns={0:'salario_promedio'}))

            if isinstance(res['marca_counts'], pd.Series) and not res['marca_counts'].empty:
                st.subheader('Conteo por marca de auto')
                st.table(res['marca_counts'].reset_index().rename(columns={0:'count'}))

            # Mostrar figuras en la app
            st.subheader('Gráficos')
            for i, f in enumerate(figs):
                st.pyplot(f)

            # Generar CSV resumen y PDF para descargar
            # CSV resumen (con medidas claves)
            resumen = {
                'edad_mean': [res.get('edad_mean')],
                'edad_median': [res.get('edad_median')],
                'edad_mode': [res.get('edad_mode')],
                'salario_mean': [res.get('salario_mean')],
                'salario_median': [res.get('salario_median')],
                'edad_media_con_mascota': [res.get('edad_media_con_mascota')],
                'edad_media_sin_mascota': [res.get('edad_media_sin_mascota')],
                'hijos_mean': [res.get('hijos_mean')],
                'hijos_median': [res.get('hijos_median')]
            }
            resumen_df = pd.DataFrame(resumen)
            csv_bytes = resumen_df.to_csv(index=False).encode('utf-8')

            pdf_bytes = generar_pdf_bytes(res, figs, resumen_df)

            st.download_button('Descargar tabla resumen (CSV)', data=csv_bytes, file_name='resumen_estadistico.csv', mime='text/csv')
            st.download_button('Descargar informe completo (PDF)', data=pdf_bytes, file_name='informe_mineria_datos.pdf', mime='application/pdf')

            # Descargar dataset original
            # Convertir df_raw a excel bytes
            to_excel_buffer = BytesIO()
            try:
                df_raw.to_excel(to_excel_buffer, index=False)
                to_excel_buffer.seek(0)
                st.download_button('Descargar dataset original (.xlsx)', data=to_excel_buffer, file_name='dataset_original.xlsx')
            except Exception:
                # Si falla, ofrecer CSV
                st.download_button('Descargar dataset original (.csv)', data=df_raw.to_csv(index=False).encode('utf-8'), file_name='dataset_original.csv')

            # Opcional: estadísticas adicionales y pruebas
            st.subheader('Estadísticas y pruebas adicionales (opcional)')
            if st.checkbox('Calcular correlación Pearson entre EDAD y SALARIO'):
                try:
                    edad_arr = pd.to_numeric(df_raw[mapping['edad']], errors='coerce')
                    sal_arr = pd.to_numeric(df_raw[mapping['salario']], errors='coerce')
                    # eliminar NA
                    mask = edad_arr.notna() & sal_arr.notna()
                    corr, pval = stats.pearsonr(edad_arr[mask], sal_arr[mask])
                    st.write({'pearson_r': corr, 'p_value': pval})
                except Exception as e:
                    st.error(f'Error calculando correlación: {e}')

            if st.checkbox('Prueba t (edad con mascota vs sin)'):
                try:
                    pet = df_raw[mapping['mascota']].astype(str).str.lower().fillna('')
                    tiene = pet.str.contains('sí|si|s|yes|true|1')
                    edad_arr = pd.to_numeric(df_raw[mapping['edad']], errors='coerce')
                    grupo1 = edad_arr[tiene].dropna()
                    grupo2 = edad_arr[~tiene].dropna()
                    tstat, pval = stats.ttest_ind(grupo1, grupo2, equal_var=False, nan_policy='omit')
                    st.write({'t_statistic': float(tstat), 'p_value': float(pval)})
                except Exception as e:
                    st.error(f'Error en la prueba t: {e}')

            st.success('Proceso finalizado. Usa los botones para descargar los resultados.')

# -------------------- Fin app --------------------
