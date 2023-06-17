import tkinter as tk
import subprocess
from tkinter import filedialog, messagebox
from parse_cfdi4_facturas import get_cfdi_data_from_folder, export_data_to_csv,\
      export_data_to_excel, export_data_to_sqlite
from parse_cfdi4_facturas import DATABASE_FILE

def open_exported_file():
    if exported_file_path.endswith(".sqlite"):
        messagebox.showinfo("Sqlite File",
                             "Open the SQLite file using a SQLite browser.")
        dialog.destroy() 
    elif exported_file_path:
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
    output_file = None

    if folder_path:
        format_selection = format_var.get()
        data_list = get_cfdi_data_from_folder(folder_path)
        if format_selection == "CSV":
            output_file = filedialog.asksaveasfilename(defaultextension=".csv",
                                                        filetypes=[
                                                            ("CSV Files", "*.csv")]
                                                            )
            if output_file:
                export_data_to_csv(data_list, output_file)
                exported_file_path = output_file  # Track the path of the exported file
                show_open_exported_file_dialog()
        elif format_selection == "Excel":
            output_file = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                        filetypes=[
                                                            ("Excel Files", "*.xlsx")]
                                                            )
            if output_file:
                export_data_to_excel(data_list, output_file)
                exported_file_path = output_file  # Track the path of the exported file
                show_open_exported_file_dialog()
        elif format_selection == "sqlite":
            exported_file_path = DATABASE_FILE
            if DATABASE_FILE:
                export_data_to_sqlite(data_list, DATABASE_FILE)
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

    sqlite_radio = tk.Radiobutton(window, text="sqlite", variable=format_var,
                                  value="sqlite")
    sqlite_radio.pack(anchor=tk.W)

    # Run the main window's event loop
    window.mainloop()

if __name__ == "__main__":
    main()
