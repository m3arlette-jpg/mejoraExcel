import streamlit as st
import pandas as pd
import io
import chardet
from openpyxl import load_workbook
from copy import copy

# 🧱 Configuración de la app
st.set_page_config(page_title="Vaciado de datos", layout="wide")
st.title("✨ Vaciado de datos en un archivo")

# 🔐 Protección con contraseña
def verificar_acceso():
    st.sidebar.header("🔒 Acceso restringido")
    password = st.sidebar.text_input("Ingresa la contraseña", type="password")
    return password == "miclave123"  # Cambia esto por tu clave

if not verificar_acceso():
    st.warning("🔐 Esta aplicación está protegida. Ingresa la contraseña en la barra lateral.")
    st.stop()




# 📂 Función para cargar archivo base
def cargar_base(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    try:
        if ext == "csv":
            return pd.read_csv(uploaded_file, skiprows=7)
        elif ext == "xlsx":
            return pd.read_excel(uploaded_file, skiprows=7)
    except Exception as e:
        st.error(f"❌ Error al cargar base: {e}")
        return None

# 📂 Función para cargar archivo fuente con codificación flexible
def cargar_fuente(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    try:
        if ext == "csv":
            try:
                return pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                raw_data = uploaded_file.read()
                encoding_detected = chardet.detect(raw_data)['encoding']
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, encoding=encoding_detected)
        elif ext == "xlsx":
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error al cargar fuente: {e}")
        return None

# 📤 Subida de archivos
archivo_base = st.file_uploader("📂 Sube tu template (que la eqtiqueta siempre este pública)", type=["csv", "xlsx"])
archivo_fuente = st.file_uploader("📥 Sube tu Query (que la eqtiqueta siempre este pública)", type=["csv", "xlsx"])

if archivo_base and archivo_fuente:
    base_df = cargar_base(archivo_base)
    fuente_df = cargar_fuente(archivo_fuente)

    if base_df is not None and fuente_df is not None:
        if "C98_INDICADOR_DE_FINIQUITO" not in fuente_df.columns:
            st.error("❌ El archivo fuente debe tener la columna 'C98_INDICADOR_DE_FINIQUITO'")
        else:
            filtrado = fuente_df[fuente_df["C98_INDICADOR_DE_FINIQUITO"] == 0]

           # 🧠 Mostrar solo columnas que están en base, en el mismo orden del archivo base ✅ (AJUSTE FINAL)
            columnas_base = base_df.columns.tolist()
            columnas_comunes_mostrar = [col for col in columnas_base if col in filtrado.columns]

            # 🧾 Previsualización con orden exacto de columnas del archivo base
            st.subheader("✅ Registros filtrados con columnas en el orden del archivo base")
            preview_df = filtrado[columnas_comunes_mostrar].copy()
            st.dataframe(preview_df)


            
else:
    st.info("👆 Sube ambos archivos para comenzar.")
