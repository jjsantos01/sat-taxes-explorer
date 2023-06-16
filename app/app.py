import sqlite3
import streamlit as st
import pandas as pd

DATABASE_FILE = "../../2023/facturas_2023.sqlite"

def fetch_data_from_sqlite(database_file):
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

# Set the title and page layout
st.title("Facturas")

# Connect to the SQLite database and fetch the data
data, columns = fetch_data_from_sqlite(DATABASE_FILE)
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
