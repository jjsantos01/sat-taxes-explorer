from datetime import datetime
import os
import PyPDF2
import re
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DATABASE_FILE = os.getenv("DATABASE_FILE")
folder_path = os.path.dirname(DATABASE_FILE)
if not os.path.exists(folder_path):
    os.makedirs(folder_path, exist_ok=True)

VAR_REGEX_DICT = {
    "RFC": r"RFC\s+(\w+)",
    "TIPO DE DECLARACIÓN": r"TIPO DE DECLARACIÓN\s+(\w+)",
    "EJERCICIO": r"EJERCICIO\s+(\d+)",
    "PERIODO": r"PERIODO\s+(\w+)",
    "FECHA Y HORA DE PRESENTACIÓN": r"FECHA Y HORA DE\nPRESENTACIÓN(\S+)",
    "NÚMERO DE OPERACIÓN": r"NÚMERO DE\nOPERACIÓN(\d+)",
    "INGRESOS DE PERIODOS ANTERIORES": r"INGRESOS DE PERIODOS\nANTERIORES([\d,]+)",
    "INGRESOS DEL PERIODO": r"INGRESOS DEL PERIODO ([\d,]+)",
    "COMPRAS Y GASTOS DE PERIODOS ANTERIORES": r"COMPRAS Y GASTOS DE PERIODOS\nANTERIORES([\d,]+)",
    "COMPRAS Y GASTOS DEL PERIODO": r"COMPRAS Y GASTOS DEL PERIODO ([\d,]+)",
    "ISR CAUSADO": r"ISR CAUSADO ([\d,]+)",
    "PAGOS PROVISIONALES DE PERIODOS ANTERIORES": r"(?:PAGOS PROVISIONALES DE\nPERIODOS ANTERIORES|PAGOS PROVISIONALES\nEFECTUADOS CON ANTERIORIDAD)([\d,]+)",
    "ISR RETENIDO DE PERIODOS ANTERIORES": r"ISR RETENIDO DE PERIODOS\nANTERIORES([\d,]+)",
    "ISR RETENIDO DEL PERIODO": r"ISR RETENIDO DEL PERIODO ([\d,]+)",
    "ISR A CARGO": r"ISR A CARGO ([\d,]+)",
    "ACTIVIDADES GRAVADAS A LA TASA DEL 16%": r"ACTIVIDADES GRAVADAS A LA TASA\nDEL 16%([\d,]+)",
    "IVA COBRADO DEL PERIODO A LA TASA DEL 16%": r"IVA COBRADO DEL PERIODO A LA\nTASA DEL 16%([\d,]+)",
    "IVA ACREDITABLE DEL PERIODO": r"IVA ACREDITABLE DEL PERIODO ([\d,]+)",
    "IVA RETENIDO": r"IVA RETENIDO ([\d,]+)",
    "IMPUESTO AL VALOR AGREGADO A CARGO": r"IMPUESTO AL VALOR AGREGADO\nA CARGO ([\d,]+)",
    "IMPUESTO AL VALOR AGREGADO A FAVOR": r"IMPUESTO AL VALOR AGREGADO\nA FAVOR ([\d,]+)",
}

NON_NUMERIC_VARIABLES = ["RFC", "TIPO DE DECLARACIÓN", "PERIODO", "FECHA Y HORA DE PRESENTACIÓN"]
DATE_VARIABLES = ["FECHA Y HORA DE PRESENTACIÓN"]

def extract_text_from_pdf(pdf_file_path):
    #with open(pdf_file_path, 'rb') as file:
    reader = PyPDF2.PdfReader(pdf_file_path)
    num_pages = len(reader.pages)

    text = ""
    for page_num in range(num_pages):
        page = reader.pages[page_num]
        text += page.extract_text()

    return text

def make_integer_number(text):
    return int(text.replace(",",""))

def extract_data_from_text(text):
    data = {}
    for var_name, regex in VAR_REGEX_DICT.items():
        match = re.search(regex, text)
        if match:
            value = match.group(1)
            if value:
                if var_name not in NON_NUMERIC_VARIABLES:
                    data[var_name] = make_integer_number(value)
                elif var_name in DATE_VARIABLES:
                    data[var_name] = datetime.strptime(value, '%d/%m/%Y').date()
                else:
                    data[var_name] = value
    return data

def save_data_to_sqlite(data, output_file):
    # Check if the SQLite database file exists
    database_exists = os.path.isfile(output_file)

    # Connect to the SQLite database
    conn = sqlite3.connect(output_file)
    c = conn.cursor()
    saved = False

    # If the database doesn't exist, create the table
    if not database_exists or not table_exists(conn, 'declaraciones_mensuales'):
        # Create the table with appropriate columns
        c.execute('''
            CREATE TABLE declaraciones_mensuales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfc TEXT,
                tipo_declaracion TEXT,
                ejercicio INTEGER,
                periodo TEXT,
                fecha_presentacion DATE,
                numero_operacion INTEGER UNIQUE,
                ingresos_periodos_anteriores INTEGER,
                ingresos_periodo INTEGER,
                compras_gastos_periodos_anteriores INTEGER,
                compras_gastos_periodo INTEGER,
                isr_causado INTEGER,
                pagos_provisionales_periodos_anteriores INTEGER,
                isr_retenido_periodos_anteriores INTEGER,
                isr_retenido_periodo INTEGER,
                isr_a_cargo INTEGER,
                actividades_gravadas_tasa_16 INTEGER,
                iva_cobrado_tasa_16 INTEGER,
                iva_acreditable_periodo INTEGER,
                iva_retenido INTEGER,
                impuesto_valor_agregado_cargo INTEGER,
                impuesto_valor_agregado_favor INTEGER
            )
        ''')
    
    operation = data['NÚMERO DE OPERACIÓN']
    c.execute("SELECT numero_operacion FROM declaraciones_mensuales WHERE numero_operacion = ?", (operation,))
    existing_operation = c.fetchone()

    if existing_operation is None:
        # Insert the data into the table
        c.execute('''
            INSERT INTO declaraciones_mensuales (
                rfc, tipo_declaracion, ejercicio, periodo, fecha_presentacion, numero_operacion,
                ingresos_periodos_anteriores, ingresos_periodo,
                compras_gastos_periodos_anteriores, compras_gastos_periodo, isr_causado,
                pagos_provisionales_periodos_anteriores, isr_retenido_periodos_anteriores,
                isr_retenido_periodo, isr_a_cargo, actividades_gravadas_tasa_16,
                iva_cobrado_tasa_16, iva_acreditable_periodo, iva_retenido,
                impuesto_valor_agregado_cargo, impuesto_valor_agregado_favor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['RFC'], data['TIPO DE DECLARACIÓN'], data['EJERCICIO'],
            data['PERIODO'], data['FECHA Y HORA DE PRESENTACIÓN'], data['NÚMERO DE OPERACIÓN'],
            data['INGRESOS DE PERIODOS ANTERIORES'], data['INGRESOS DEL PERIODO'],
            data['COMPRAS Y GASTOS DE PERIODOS ANTERIORES'], data['COMPRAS Y GASTOS DEL PERIODO'],
            data['ISR CAUSADO'], data['PAGOS PROVISIONALES DE PERIODOS ANTERIORES'],
            data['ISR RETENIDO DE PERIODOS ANTERIORES'],
            data.get('ISR RETENIDO DEL PERIODO', 0), data['ISR A CARGO'],
            data['ACTIVIDADES GRAVADAS A LA TASA DEL 16%'], data['IVA COBRADO DEL PERIODO A LA TASA DEL 16%'],
            data['IVA ACREDITABLE DEL PERIODO'], data['IVA RETENIDO'],
            data.get('IMPUESTO AL VALOR AGREGADO A CARGO', 0), data.get('IMPUESTO AL VALOR AGREGADO A FAVOR', 0)
        ))
        print("Data saved to SQLite successfully!")
        saved = True
    else:
        print("Operation {} already exists".format(operation))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    return saved

def table_exists(conn, table_name):
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",
               (table_name,))
    return c.fetchone() is not None

# pdf_file_path = '../../2022/declaracion_mensual_202202.pdf'
# extracted_text = extract_text_from_pdf(pdf_file_path)
#print(extracted_text)
# extracted_data = extract_data_from_text(extracted_text)
# for key, value in extracted_data.items():
#     print(key + ":", value)
# output_file = "../declaraciones.sqlite"  # SQLite database file name
# save_data_to_sqlite(extracted_data, output_file)
