import csv
import os
import sqlite3
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

format_var = None  # Declare format_var as a global variable
exported_file_path = ""  # Track the path of the exported file
CLIENT_RFC = os.getenv("CLIENT_RFC")
DATABASE_FILE = os.getenv("DATABASE_FILE")
folder_path = os.path.dirname(DATABASE_FILE)
if not os.path.exists(folder_path):
    os.makedirs(folder_path, exist_ok=True)


def get_data_cfdi(file_path, client_rfc=None):
    tree = ET.parse(file_path)
    root = tree.getroot()
    version = root.attrib.get("Version", "")
    if version[0] == "4":
        return get_data_cfdi_4_0(root, client_rfc)
    elif version[0] == "3":
        return get_data_cfdi_3_3(root, client_rfc)
    else:
        return None

def get_data_cfdi_4_0(root, client_rfc=None):
    # Parse the XML file
    version = root.attrib.get("Version", "")
    if version[0] != "4":
        print("Skipping XML with version different than 4")
        return None

    # Get the namespace used in the XML
    namespace = "{http://www.sat.gob.mx/cfd/4}"

    # Get the UUID
    complemento = root.find(namespace + "Complemento")
    timbre_fiscal_digital = complemento.find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
    uuid = timbre_fiscal_digital.attrib['UUID']

    # Retrieve the data from the invoice
    fecha = root.attrib.get("Fecha", "")
    tipoComprobante = root.attrib.get("TipoDeComprobante", "")
    subtotal = float(root.attrib.get("SubTotal", 0))
    total = float(root.attrib.get("Total", 0))

    emisor = root.find(namespace + "Emisor")
    emisorRFC = emisor.attrib.get("Rfc", "")
    emisorNombre = emisor.attrib.get("Nombre", "")

    receptor = root.find(namespace + "Receptor")
    receptorRFC = receptor.attrib.get("Rfc", "")
    receptorNombre = receptor.attrib.get("Nombre", "")

    impuestoTotalTraslado = 0
    impuestoTotalRetenido = 0
    isrRetenido = 0
    ivaRetenido = 0
    ivaTrasladado = 0

    impuestos = root.find(namespace + "Impuestos")
    if impuestos is not None:
        impuestoTotalTraslado = float(impuestos.attrib.get("TotalImpuestosTrasladados",
                                                            0))

        retenciones = impuestos.find(namespace + "Retenciones")
        if retenciones is not None:
            for retencion in retenciones:
                impuesto = retencion.attrib.get("Impuesto", "")
                importe = float(retencion.attrib.get("Importe", 0))

                if impuesto == "001":
                    isrRetenido = importe
                elif impuesto == "002":
                    ivaRetenido = importe

        traslados = impuestos.find(namespace + "Traslados")
        if traslados is not None:
            for traslado in traslados:
                impuesto = traslado.attrib.get("Impuesto", "")
                importe = float(traslado.attrib.get("Importe", 0))

                if impuesto == "002":
                    ivaTrasladado = importe

    tipo = ""
    if client_rfc:
        if client_rfc == receptorRFC:
            tipo = "gasto"
        elif client_rfc == emisorRFC:
            tipo = "ingreso"
        else:
            return None

    currency = root.attrib.get("Moneda", "")
    exchange_rate = float(root.attrib.get("TipoCambio", "1"))

    # Convert amounts to MXN if currency is foreign
    if currency != "MXN":
        subtotal = round(subtotal * exchange_rate, 2)
        total = round(total * exchange_rate, 2)
        impuestoTotalTraslado = round(impuestoTotalTraslado * exchange_rate, 2)
        impuestoTotalRetenido = round(impuestoTotalRetenido * exchange_rate, 2)
        isrRetenido = round(isrRetenido * exchange_rate, 2)
        ivaRetenido = round(ivaRetenido * exchange_rate, 2)
        ivaTrasladado = round(ivaTrasladado * exchange_rate, 2)

    # Create a dictionary with the extracted data
    data = {
        "uuid": uuid,
        "fecha": fecha,
        "tipoComprobante": tipoComprobante,
        "subtotal": subtotal,
        "total": total,
        "emisorRFC": emisorRFC,
        "emisorNombre": emisorNombre,
        "receptorRFC": receptorRFC,
        "receptorNombre": receptorNombre,
        "impuestoTotalTraslado": impuestoTotalTraslado,
        "impuestoTotalRetenido": impuestoTotalRetenido,
        "isrRetenido": isrRetenido,
        "ivaRetenido": ivaRetenido,
        "ivaTrasladado": ivaTrasladado,
        "tipo": tipo,
        "version": version
    }

    return data

def get_data_cfdi_3_3(root, client_rfc=None):
    version = root.attrib.get("Version", "")
    if version[0] != "3":
        print("Skipping XML with version different than 3")
        return None

    # Get the namespace used in the XML
    namespace = "{http://www.sat.gob.mx/cfd/3}"

    # Get the UUID
    timbre_fiscal_digital = root.find(".//tfd:TimbreFiscalDigital", {"tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"})
    uuid = timbre_fiscal_digital.attrib['UUID']

    # Retrieve the data from the invoice
    fecha = root.attrib.get("Fecha", "")
    tipoComprobante = root.attrib.get("TipoDeComprobante", "")
    subtotal = float(root.attrib.get("SubTotal", 0))
    total = float(root.attrib.get("Total", 0))

    emisor = root.find(namespace + "Emisor")
    emisorRFC = emisor.attrib.get("Rfc", "")
    emisorNombre = emisor.attrib.get("Nombre", "")

    receptor = root.find(namespace + "Receptor")
    receptorRFC = receptor.attrib.get("Rfc", "")
    receptorNombre = receptor.attrib.get("Nombre", "")

    impuestoTotalTraslado = 0
    impuestoTotalRetenido = 0
    isrRetenido = 0
    ivaRetenido = 0
    ivaTrasladado = 0

    impuestos = root.find(namespace + "Impuestos")
    if impuestos is not None:
        impuestoTotalTraslado = float(impuestos.attrib.get("TotalImpuestosTrasladados", 0))
        impuestoTotalRetenido = float(impuestos.attrib.get("TotalImpuestosRetenidos", 0))

        retenciones = impuestos.find(namespace + "Retenciones")
        if retenciones is not None:
            for retencion in retenciones:
                impuesto = retencion.attrib.get("Impuesto", "")
                importe = float(retencion.attrib.get("Importe", 0))

                if impuesto == "001":
                    isrRetenido = importe
                elif impuesto == "002":
                    ivaRetenido = importe

        traslados = impuestos.find(namespace + "Traslados")
        if traslados is not None:
            for traslado in traslados:
                impuesto = traslado.attrib.get("Impuesto", "")
                importe = float(traslado.attrib.get("Importe", 0))

                if impuesto == "002":
                    ivaTrasladado = importe

    tipo = ""
    if client_rfc:
        if client_rfc == receptorRFC:
            tipo = "gasto"
        elif client_rfc == emisorRFC:
            tipo = "ingreso"
        else:
            return None

    # Create a dictionary with the extracted data
    data = {
        "uuid": uuid,
        "fecha": fecha,
        "tipoComprobante": tipoComprobante,
        "subtotal": subtotal,
        "total": total,
        "emisorRFC": emisorRFC,
        "emisorNombre": emisorNombre,
        "receptorRFC": receptorRFC,
        "receptorNombre": receptorNombre,
        "impuestoTotalTraslado": impuestoTotalTraslado,
        "impuestoTotalRetenido": impuestoTotalRetenido,
        "isrRetenido": isrRetenido,
        "ivaRetenido": ivaRetenido,
        "ivaTrasladado": ivaTrasladado,
        "tipo": tipo,
        "version": version
    }

    return data

def get_cfdi_data_from_folder(folder_path):
    data_list = []

    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if the file is an XML file
        if filename.endswith(".xml"):
            # Retrieve data from the XML file using get_data_cfdi function
            data = get_data_cfdi_4_0(file_path, client_rfc=CLIENT_RFC)

            # Append the data to the data_list
            if data:
                data_list.append(data)

    return data_list

def export_data_to_csv(data_list, output_file):
    # Define the field names for the CSV file
    field_names = data_list[0].keys()

    # Write the data to the CSV file
    with open(output_file, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(data_list)

    print("Data exported to CSV successfully!")

def export_data_to_excel(data_list, output_file):
    from openpyxl import Workbook
    # Create a new workbook and select the active sheet
    workbook = Workbook()
    sheet = workbook.active

    # Define the headers for the columns
    headers = list(data_list[0].keys())
    # Write the headers to the worksheet
    sheet.append(headers)

    # Write the data to the worksheet
    for data in data_list:
        sheet.append(list(data.values()))

    # Save the workbook to the output file
    workbook.save(output_file)

    print("Data exported to Excel successfully!")

def export_data_to_sqlite(data_list, output_file):
    # Check if the SQLite database file exists
    database_exists = os.path.isfile(output_file)

    # Connect to the SQLite database
    conn = sqlite3.connect(output_file)
    c = conn.cursor()

    # If the database doesn't exist, create the table
    if not database_exists or not table_exists(conn, 'cfdi'):
        # Create the table with appropriate columns
        c.execute('''
            CREATE TABLE cfdi (
                uuid TEXT PRIMARY KEY,
                fecha TEXT,
                tipoComprobante TEXT,
                subtotal REAL,
                total REAL,
                emisorRFC TEXT,
                emisorNombre TEXT,
                receptorRFC TEXT,
                receptorNombre TEXT,
                impuestoTotalTraslado REAL,
                impuestoTotalRetenido REAL,
                isrRetenido REAL,
                ivaRetenido REAL,
                ivaTrasladado REAL,
                tipo TEXT,
                version TEXT
            )
        ''')
    exported_data = 0
    # Insert the data into the table if the UUID doesn't already exist
    for data in data_list:
        uuid = data["uuid"]
        c.execute("SELECT uuid FROM cfdi WHERE uuid = ?", (uuid,))
        existing_uuid = c.fetchone()

        if existing_uuid is None:
            c.execute('''
                INSERT INTO cfdi (
                    uuid, fecha, tipoComprobante, subtotal, total, emisorRFC,
                    emisorNombre, receptorRFC, receptorNombre,
                    impuestoTotalTraslado, impuestoTotalRetenido, isrRetenido,
                    ivaRetenido, ivaTrasladado, tipo, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                uuid, data['fecha'], data['tipoComprobante'], data['subtotal'],
                data['total'], data['emisorRFC'], data['emisorNombre'],
                data['receptorRFC'], data['receptorNombre'],
                data['impuestoTotalTraslado'], data['impuestoTotalRetenido'],
                data['isrRetenido'], data['ivaRetenido'], data['ivaTrasladado'],
                data['tipo'], data['version']
            ))
            exported_data += 1
        else:
            print(f"Skipping duplicate UUID: {uuid}")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"{exported_data} records exported successfully!")
    return exported_data

def table_exists(conn, table_name):
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return c.fetchone() is not None
