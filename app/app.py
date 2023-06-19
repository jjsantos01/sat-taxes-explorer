from io import StringIO
import sqlite3
import streamlit as st
import pandas as pd
from parse_cfdi4_facturas import get_data_cfdi, export_data_to_sqlite, CLIENT_RFC,\
      DATABASE_FILE
from parse_declaraciones_pdf import extract_text_from_pdf, extract_data_from_text,\
      save_data_to_sqlite

MONTHS_DICT = {"01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
               "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
               "09": "Septiembre", "10": "Octubre", "11": "Noviembre",
               "12": "Diciembre"}

def fetch_cfdi_from_sqlite(database_file):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    # Fetch all rows from the table
    c.execute("SELECT * FROM cfdi")
    rows = c.fetchall()

    # Get the column names
    column_names = [description[0] for description in c.description]

    # Close the connection
    conn.close()

    return rows, column_names

def fetch_previous_declaration(database_file, ejercicio, periodo):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()

    # Fetch all rows from the table
    c.execute("""
        SELECT ejercicio, periodo,
          pagos_provisionales_periodos_anteriores,
          isr_retenido_periodos_anteriores
        FROM declaraciones_mensuales
        WHERE ejercicio = ? AND periodo = ?""", (ejercicio, periodo))
    rows = c.fetchone()

    # Get the column names
    column_names = [description[0] for description in c.description]

    # Close the connection
    conn.close()

    return rows, column_names

def show_invoices():
    # Set the title and page layout
    st.title("Facturas")

    # Connect to the SQLite database and fetch the data
    data, columns = fetch_cfdi_from_sqlite(DATABASE_FILE)
    df = pd.DataFrame(data, columns=columns)

    # Add widgets for filtering the data
    st.sidebar.title("Data Filters")

    # Filter by year
    years = sorted(df['fecha'].str[:4].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Select Year", years)

    # Filter by month
    months = sorted(df['fecha'].str[5:7].unique())
    selected_month = st.sidebar.selectbox("Select Month", months)

    # Filter by tipo
    tipos = ['gasto', 'ingreso']
    selected_tipo = st.sidebar.multiselect("Select Tipo", tipos, default=tipos)

    # Apply filters to the data
    filtered_df = df[df['fecha'].str.startswith(selected_year) &
                    df['fecha'].str[5:7].eq(selected_month) &
                    df['tipo'].isin(selected_tipo)]

    ingresos_totales = filtered_df.query('tipo == "ingreso"')['subtotal'].sum()
    gastos_totales = filtered_df.query('tipo == "gasto"')['total'].sum()
    isr_retenido = filtered_df.query('tipo == "ingreso"')['isrRetenido'].sum()
    iva_retenido = filtered_df.query('tipo == "ingreso"')['ivaRetenido'].sum()
    iva_trasladado = filtered_df.query('tipo == "gasto"')['ivaTrasladado'].sum()

    # Display the filtered data table
    st.dataframe(filtered_df, width=1200)


    if st.checkbox("Mostrar datos de declaracion anterior"):
        previous_declaration = fetch_previous_declaration(
            DATABASE_FILE,
            int(selected_year),
            MONTHS_DICT[f"{int(selected_month)-1:02d}"]
            )
        for k, v in zip(previous_declaration[1], previous_declaration[0]):
            st.write(f"{k}: {v}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("ISR")
        st.write(f"""Ingresos del periodo: {ingresos_totales:.2f}""")
        st.write(f"""Gastos del periodo: {gastos_totales:.2f}""")
        st.write(f"""ISR retenido: {isr_retenido:.2f}""")
    with col2:
        st.header("IVA")
        st.write(f"""IVA retenido: {iva_retenido:.2f}""")
        st.write(f"""IVA trasladado en compras: {iva_trasladado:.2f}""")

def load_invoices():
    uploaded_files = st.file_uploader("Subir facturas", type="xml",
                                       accept_multiple_files=True)
    if uploaded_files:
        data_list = []
        for uploaded_file in uploaded_files:
            file_content = StringIO(uploaded_file.getvalue().decode("utf-8"))
            data = get_data_cfdi(file_content, CLIENT_RFC)
            if data:
                data_list.append(data)

        exported = export_data_to_sqlite(data_list, DATABASE_FILE)
        if exported:
            st.success(f"{exported} registros guardados exitosamente")
        else:
            st.info("No se guardaron registros nuevos")

def fetch_declaraciones_from_sqlite(database_file):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()
    c.execute("SELECT * FROM declaraciones_mensuales ORDER BY fecha_presentacion ASC")
    rows = c.fetchall()
    column_names = [description[0] for description in c.description]
    conn.close()
    return rows, column_names

def show_declaraciones():
    # Set the title and page layout
    st.title("Declaraciones Mensuales")

    # Connect to the SQLite database and fetch the data
    data, columns = fetch_declaraciones_from_sqlite(DATABASE_FILE)
    df = pd.DataFrame(data, columns=columns)

    # Add widgets for filtering the data
    st.sidebar.title("Data Filters")

    # Filter by year
    years = sorted(df['ejercicio'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Ejercicio", years)
    
    # Apply filters to the data
    filtered_df = df[df['ejercicio'].eq(selected_year)]

    # Display the filtered data table
    st.dataframe(filtered_df, width=1200)

def load_declaraciones():
    uploaded_files = st.file_uploader("Subir declaraciones", type="pdf",
                                       accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            extracted_text = extract_text_from_pdf(uploaded_file)
            extracted_data = extract_data_from_text(extracted_text)
            print(extracted_data)
            if extracted_data:
                saved = save_data_to_sqlite(extracted_data, DATABASE_FILE)
                if saved:
                    st.success(f"Datos de {uploaded_file.name} guardados exitosamente")
                else:
                    st.info(f"{uploaded_file.name} ya estaba guardado")
            else:
                st.warning(f"No se pudieron extraer datos de {uploaded_file.name}") 


page_names_to_funcs = {
    "Cargar facturas": load_invoices,
    "Ver facturas": show_invoices,
    "Cargar declaraciones": load_declaraciones,
    "Ver declaraciones": show_declaraciones,
}

page_name = st.sidebar.selectbox("Escoge tarea", page_names_to_funcs.keys())
page_names_to_funcs[page_name]()
