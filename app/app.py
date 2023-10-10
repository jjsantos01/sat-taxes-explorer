import datetime
from io import StringIO
import random
import re
import uuid
import streamlit as st
import pandas as pd
from parse_cfdi_facturas import get_data_cfdi,\
CLIENT_RFC,DATABASE_FILE
from data_ops import delete_cfdi_from_db, fetch_cfdi_from_sqlite,\
fetch_previous_declaration, fetch_declaraciones_from_sqlite,\
save_cfdi_to_sqlite, save_declaracion_to_sqlite,\
delete_declaraciones_from_db
from parse_declaraciones_pdf import extract_text_from_pdf, extract_data_from_text

MONTHS_DICT = {"01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
               "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
               "09": "Septiembre", "10": "Octubre", "11": "Noviembre",
               "12": "Diciembre"}

def show_invoices():
    # Set the title and page layout
    st.title("Facturas")
    
    # load invoices
    load_invoices()

    # Connect to the SQLite database and fetch the data
    data, columns = fetch_cfdi_from_sqlite(DATABASE_FILE)
    df = pd.DataFrame(data, columns=columns)
    df["Borrar"] = False

    # Add widgets for filtering the data
    st.sidebar.title("Data Filters")

    # Filter by year
    years = sorted(df['fecha'].str[:4].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Select Year", years)

    # Filter by month
    months = sorted(df['fecha'].str[5:7].unique(), reverse=True)
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

    if "key" not in st.session_state:
        st.session_state["key"] = random.randint(0, 100000)
    
    edited_df = st.data_editor(filtered_df, key=st.session_state["key"])
    st.session_state['uuids_borrar'] = edited_df.loc[edited_df["Borrar"],
                                                      "uuid"].tolist()
    
    if st.session_state['uuids_borrar']:
        st.markdown(
                f"""
                    **¿Desea borrar las siguientes facturas?**:
                    {st.session_state['uuids_borrar']}
                """
        )
        def cancel_delete():
            st.session_state["key"] = str(random.randint(0, 100000))
            st.session_state["uuids_borrar"] = []

        def delete_invoice():
            delete_cfdi_from_db(st.session_state['uuids_borrar'],
                                          DATABASE_FILE)
            st.success(f"Facturas {st.session_state['uuids_borrar']}"
                       " borradas exitosamente")
            st.session_state["key"] = str(random.randint(0, 100000))
            st.session_state["uuids_borrar"] = []

        st.button("Borrar facturas", on_click=delete_invoice)       
        st.button("Cancelar", on_click=cancel_delete)

    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.header("ISR")
        st.write(f"""Ingresos del periodo: {ingresos_totales:.2f}""")
        st.write(f"""Gastos del periodo: {gastos_totales:.2f}""")
        st.write(f"""ISR retenido: {isr_retenido:.2f}""")
    with col2:
        st.header("IVA")
        st.write(f"""IVA retenido: {iva_retenido:.2f}""")
        st.write(f"""IVA trasladado en compras: {iva_trasladado:.2f}""")
    with col3:
        st.header("Anterior")
        previous_declaration = fetch_previous_declaration(
            DATABASE_FILE,
            int(selected_year),
            MONTHS_DICT[f"{int(selected_month)-1:02d}"]
            )
        if previous_declaration[0]:
            for k, v in zip(previous_declaration[1], previous_declaration[0]):
                st.write(f"{k}: {v}")
        else:
            st.info("No hay datos de declaracion anterior")

    if st.checkbox("Agregar factura manualmente"):
        new_invoice_form()

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

        exported = save_cfdi_to_sqlite(data_list, DATABASE_FILE)
        if exported:
            st.success(f"{exported} registros guardados exitosamente")
        else:
            st.info("No se guardaron registros nuevos")
        uploaded_files = None

def show_declaraciones():
    # Set the title and page layout
    st.title("Declaraciones Mensuales")

    # load declaraciones
    load_declaraciones()

    # Connect to the SQLite database and fetch the data
    data, columns = fetch_declaraciones_from_sqlite(DATABASE_FILE)
    df = pd.DataFrame(data, columns=columns)
    df["Borrar"] = False

    # Add widgets for filtering the data
    st.sidebar.title("Data Filters")

    # Filter by year
    years = sorted(df['ejercicio'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Ejercicio", years)
    
    # Apply filters to the data
    filtered_df = df[df['ejercicio'].eq(selected_year)]

    # Display the filtered data table
    if "key" not in st.session_state:
        st.session_state["key"] = random.randint(0, 100000)
    
    edited_df = st.data_editor(filtered_df, key=st.session_state["key"])
    st.session_state['ids_borrar'] = edited_df.loc[edited_df["Borrar"],
                                                         "id"].tolist()
    if st.session_state['ids_borrar']:
        st.markdown(
                f"""
                    **¿Desea borrar las siguientes declaraciones?**:
                    {st.session_state['ids_borrar']}
                """
        )
        def cancel_delete():
            st.session_state["key"] = str(random.randint(0, 100000))
            st.session_state["ids_borrar"] = []

        def delete_declaraciones():
            delete_declaraciones_from_db(st.session_state['ids_borrar'],
                                          DATABASE_FILE)
            st.success(f"Declaraciones {st.session_state['ids_borrar']}"
                       " borradas exitosamente")
            st.session_state["key"] = str(random.randint(0, 100000))
            st.session_state["ids_borrar"] = []

        st.button("Borrar facturas", on_click=delete_declaraciones)       
        st.button("Cancelar", on_click=cancel_delete)
  
def load_declaraciones():
    uploaded_files = st.file_uploader("Subir declaraciones", type="pdf",
                                       accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            extracted_text = extract_text_from_pdf(uploaded_file)
            extracted_data = extract_data_from_text(extracted_text)
            if extracted_data:
                saved = save_declaracion_to_sqlite(extracted_data, DATABASE_FILE)
                if saved:
                    st.success(f"Datos de {uploaded_file.name} guardados exitosamente")
                else:
                    st.info(f"{uploaded_file.name} ya estaba guardado")
            else:
                st.warning(f"No se pudieron extraer datos de {uploaded_file.name}") 

def new_invoice_form():
    # Create a form for user input
    cfdi_data = {}
    uuid_key = str(uuid.uuid4())
    with st.form(key="invoice_form"):
        cfdi_data['uuid'] = st.text_input('UUID', uuid_key)
        cfdi_data['fecha'] = st.text_input('Fecha',
                                            value=datetime.date.today().strftime("%Y-%m-%d"))
        cfdi_data['tipoComprobante'] = st.selectbox('Tipo de comprobante',
                                                    ['E', 'I', 'P'], index=0)
        cfdi_data['subtotal'] = st.number_input('Subtotal')
        cfdi_data['total'] = st.number_input('Total')
        cfdi_data['ivaTrasladado'] = st.number_input('IVA trasladado')
        cfdi_data['isrRetenido'] = st.number_input('ISR retenido')
        cfdi_data['ivaRetenido'] = st.number_input('IVA retenido')
        cfdi_data['impuestoTotalTraslado'] = st.number_input('Impuesto total traslado')
        cfdi_data['impuestoTotalRetenido'] = st.number_input('Impuesto total retenido')
        cfdi_data['emisorRFC'] = st.text_input('RFC emisor')
        cfdi_data['emisorNombre'] = st.text_input('Nombre emisor')
        cfdi_data['receptorRFC'] = st.text_input('RFC receptor')
        cfdi_data['receptorNombre'] = st.text_input('Nombre receptor')
        cfdi_data['tipo'] = st.selectbox('Tipo', ['gasto', 'ingreso'], index=0)
        cfdi_data['version'] = "manual"
        
        if not re.search(r"^\d{4}-\d{2}-\d{2}$", cfdi_data["fecha"]):
            st.error("Fecha debe tener formato YYYY-MM-DD")
        else:
            submitted = st.form_submit_button('Guardar')
        
        if submitted:
            # Now cfdi_data dictionary contains all the input values
            save_cfdi_to_sqlite([cfdi_data], DATABASE_FILE)
            st.success("Factura guardada exitosamente")
            st.experimental_rerun()
       
page_names_to_funcs = {
    "Facturas": show_invoices,
    "Declaraciones": show_declaraciones,
    }

page_name = st.sidebar.selectbox("Escoge tarea", page_names_to_funcs.keys())
page_names_to_funcs[page_name]()
