import csv
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET

format_var = None  # Declare format_var as a global variable
exported_file_path = ""  # Track the path of the exported file

def get_data_cfdi(file_path):
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Get the namespace used in the XML
    namespace = "{http://www.sat.gob.mx/cfd/4}"

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

    # Create a dictionary with the extracted data
    data = {
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
        "ivaTrasladado": ivaTrasladado
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
            data = get_data_cfdi(file_path)

            # Append the data to the data_list
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

def open_exported_file():
    if exported_file_path:
        try:
            # Open the file using the default application
            subprocess.Popen(['open', exported_file_path])
            dialog.destroy()  # Close the dialog window
        except OSError as e:
            messagebox.showerror("Error", f"Failed to open the file: {e}")
    else:
        messagebox.showinfo("No File", "No exported file found.")

def select_folder():
    global exported_file_path  # Declare exported_file_path as a global variable
    folder_path = filedialog.askdirectory()
    if folder_path:
        format_selection = format_var.get()
        if format_selection == "CSV":
            data_list = get_cfdi_data_from_folder(folder_path)
            output_file = filedialog.asksaveasfilename(defaultextension=".csv",
                                                        filetypes=[
                                                            ("CSV Files", "*.csv")]
                                                            )
            if output_file:
                export_data_to_csv(data_list, output_file)
                exported_file_path = output_file  # Track the path of the exported file
                show_open_exported_file_dialog()
        elif format_selection == "Excel":
            data_list = get_cfdi_data_from_folder(folder_path)
            output_file = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                        filetypes=[
                                                            ("Excel Files", "*.xlsx")]
                                                            )
            if output_file:
                export_data_to_excel(data_list, output_file)
                exported_file_path = output_file  # Track the path of the exported file
                show_open_exported_file_dialog()
        else:
            messagebox.showerror("Invalid Format",
                                  "Please select a valid export format!")

def show_open_exported_file_dialog():
    global dialog 
    dialog = tk.Toplevel()
    dialog.title("Export Successful")
    dialog.geometry("300x100")
    label = tk.Label(dialog, text="Data exported successfully!")
    label.pack(pady=10)
    button = tk.Button(dialog, text="Open Exported Data", command=open_exported_file)
    button.pack()

def main():
    global format_var  # Declare format_var as a global variable

    # Create the main window
    window = tk.Tk()
    window.title("XML File Selection")
    window.geometry("400x150")

    # Create a label
    label = tk.Label(window, text="Select the folder with XML files")
    label.pack(pady=10)

    # Create a button to select the folder
    button = tk.Button(window, text="Select Folder", command=select_folder)
    button.pack()

    # Create radio buttons for format selection
    format_var = tk.StringVar()
    format_var.set("CSV")

    csv_radio = tk.Radiobutton(window, text="CSV", variable=format_var, value="CSV")
    csv_radio.pack(anchor=tk.W)

    excel_radio = tk.Radiobutton(window, text="Excel", variable=format_var,
                                  value="Excel")
    excel_radio.pack(anchor=tk.W)

    # Run the main window's event loop
    window.mainloop()

if __name__ == "__main__":
    main()
