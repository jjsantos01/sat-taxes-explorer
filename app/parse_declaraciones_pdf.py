from datetime import datetime
import os
import PyPDF2
import re
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
