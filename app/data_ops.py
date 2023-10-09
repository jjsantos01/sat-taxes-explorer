import sqlite3


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