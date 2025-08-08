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
archivo_base = st.file_uploader("📂 Archivo donde se cargará la información (que la etiqueta siempre esté pública)", type=["csv", "xlsx"])
archivo_fuente = st.file_uploader("📥 Archivo que contiene los datos (que la etiqueta siempre esté pública)", type=["csv", "xlsx"])

if archivo_base and archivo_fuente:
    base_df = cargar_base(archivo_base)
    fuente_df = cargar_fuente(archivo_fuente)

    if base_df is not None and fuente_df is not None:
        if "C98_INDICADOR_DE_FINIQUITO" not in fuente_df.columns:
            st.error("❌ El archivo fuente debe tener la columna 'C98_INDICADOR_DE_FINIQUITO'")
        else:
            filtrado = fuente_df[fuente_df["C98_INDICADOR_DE_FINIQUITO"] == 0]

            columnas_base = base_df.columns.tolist()
            columnas_comunes_mostrar = [col for col in filtrado.columns if col in columnas_base]

            st.subheader("✅ Registros filtrados con columnas coincidentes")
            st.dataframe(filtrado[columnas_comunes_mostrar])

            if st.button("📄 Generar archivo Excel con los datos obtenidos"):
                buffer_excel = io.BytesIO()
                base_df.to_excel(buffer_excel, index=False, sheet_name="Datos")
                buffer_excel.seek(0)

                wb = load_workbook(buffer_excel)
                ws = wb.active

                # 🛡️ Guardar contenido adicional después de columna AH (col 34)
                contenido_extra = {}
                for row in ws.iter_rows(min_row=9, max_row=ws.max_row, min_col=35):
                    for cell in row:
                        if cell.value or cell.data_type == 'f':
                            contenido_extra[(cell.row, cell.column)] = {
                                'value': cell.value,
                                'formula': cell.value if cell.data_type == 'f' else None,
                                'style': {
                                    'font': copy(cell.font),
                                    'fill': copy(cell.fill),
                                    'alignment': copy(cell.alignment),
                                    'border': copy(cell.border),
                                    'number_format': cell.number_format
                                }
                            }

                # 🎨 Copiar estilo del encabezado original
                estilo_encabezado = {}
                for col in range(1, ws.max_column + 1):
                    celda_original = ws.cell(row=1, column=col)
                    estilo_encabezado[col] = {
                        'font': copy(celda_original.font),
                        'fill': copy(celda_original.fill),
                        'alignment': copy(celda_original.alignment),
                        'border': copy(celda_original.border),
                        'number_format': celda_original.number_format
                    }

                # 🧼 Limpiar y reescribir encabezados en fila 8
                ws.delete_rows(1, ws.max_row)
                for c_idx, col_name in enumerate(base_df.columns, start=1):
                    celda = ws.cell(row=8, column=c_idx, value=col_name)
                    estilo = estilo_encabezado.get(c_idx)
                    if estilo:
                        celda.font = estilo['font']
                        celda.fill = estilo['fill']
                        celda.alignment = estilo['alignment']
                        celda.border = estilo['border']
                        celda.number_format = estilo['number_format']

                encabezados_excel = [ws.cell(row=8, column=c).value for c in range(1, ws.max_column + 1)]
                columnas_comunes_reales = [col for col in filtrado.columns if col in encabezados_excel]

                # 🧠 Insertar datos alineados por nombre exacto
                for r_idx, row in enumerate(filtrado[columnas_comunes_reales].itertuples(index=False, name=None), start=9):
                    for col_name in columnas_comunes_reales:
                        for c_idx in range(1, ws.max_column + 1):
                            if ws.cell(row=8, column=c_idx).value == col_name:
                                ws.cell(row=r_idx, column=c_idx).value = row[columnas_comunes_reales.index(col_name)]
                                break

                    

                    # 📌 Copiar fórmulas de AH9:AQ9 a cada nueva fila
                    for col in range(34, 44 + 1):  # AH = 34, AQ = 44
                        formula_or_value = ws.cell(row=9, column=col).value
                        if formula_or_value:
                            ws.cell(row=r_idx, column=col).value = formula_or_value
                            ws.cell(row=r_idx, column=col).number_format = ws.cell(row=9, column=col).number_format
                            ws.cell(row=r_idx, column=col).font = copy(ws.cell(row=9, column=col).font)
                            ws.cell(row=r_idx, column=col).fill = copy(ws.cell(row=9, column=col).fill)
                            ws.cell(row=r_idx, column=col).alignment = copy(ws.cell(row=9, column=col).alignment)
                            ws.cell(row=r_idx, column=col).border = copy(ws.cell(row=9, column=col).border)


                # 🔁 Restaurar contenido adicional después de columna AH
                for (r, c), data in contenido_extra.items():
                    celda = ws.cell(row=r, column=c)
                    celda.value = data['value']
                    estilo = data['style']
                    celda.font = estilo['font']
                    celda.fill = estilo['fill']
                    celda.alignment = estilo['alignment']
                    celda.border = estilo['border']
                    celda.number_format = estilo['number_format']

                # ✅ Mostrar columnas válidas como tabla
                st.success("✅ Columnas válidas para insertar (presentes en ambos archivos):")
                st.table(pd.DataFrame(columnas_comunes_reales, columns=["Columnas Coincidentes"]))

                # 📥 Descargar archivo final
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)

                st.download_button(
                    label="📥 Descargar archivo_final.xlsx",
                    data=output,
                    file_name="archivo_final.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
else:
    st.info("👆 Sube ambos archivos para comenzar.")



