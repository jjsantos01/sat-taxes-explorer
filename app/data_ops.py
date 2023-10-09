import sqlite3
import os

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
        SELECT periodo,
               pagos_provisionales_periodos_anteriores,
               impuesto_valor_agregado_favor
        FROM declaraciones_mensuales
        WHERE ejercicio = ? AND periodo = ?""", (ejercicio, periodo))
    rows = c.fetchone()

    # Get the column names
    column_names = [description[0] for description in c.description]

    # Close the connection
    conn.close()

    return rows, column_names

def fetch_declaraciones_from_sqlite(database_file):
    conn = sqlite3.connect(database_file)
    c = conn.cursor()
    c.execute("SELECT * FROM declaraciones_mensuales ORDER BY fecha_presentacion ASC")
    rows = c.fetchall()
    column_names = [description[0] for description in c.description]
    conn.close()
    return rows, column_names

def delete_selected_rows_from_db(selected_uuids, output_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(output_file)
    cursor = conn.cursor()

    try:
        # Loop through the selected IDs and delete corresponding rows
        for selected_id in selected_uuids:
            cursor.execute('DELETE FROM cfdi WHERE uuid=?', (selected_id,))
        
        # Commit the changes
        conn.commit()
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

    finally:
        # Close the connection
        conn.close()

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

def save_declaracion_to_sqlite(data, output_file):
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
