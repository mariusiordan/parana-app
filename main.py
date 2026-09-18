import sqlite3
import os

DATABASE_PATH = "parana.db"


def connect_to_database(db_path=DATABASE_PATH):
    """Open a connection to the Parana database"""
    if not os.path.exists(db_path):
        print(f"Error: database file '{db_path}' was not found.")
        return None

    try:
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection
    except sqlite3.Error as error:
        print(f"Error connecting to the database: {error}")
        return None

def get_shopper(connection):
    """Prompt for a shopper_id and look it up in the shoppers table"""
    entered_id = input("Please enter your shopper id: ").strip()

    if not entered_id.isdigit():
        print("Error: the shopper id must be a whole number.")
        return None

    query = """
        SELECT shopper_id, shopper_first_name, shopper_surname
        FROM shoppers
        WHERE shopper_id = ?
    """

    shopper = connection.execute(query, (int(entered_id),)).fetchone()

    if shopper is None:
        print(f"Error: no shopper was found with id {entered_id}.")
        return None

    print(f"\nWelcome {shopper['shopper_first_name']} {shopper['shopper_surname']}!")
    return shopper




if __name__ == "__main__":
    conn = connect_to_database()

    if conn is None:
        exit(1)

    current_shopper = get_shopper(conn)

    if current_shopper is None:
        conn.close()
        exit(1)

    
    conn.close()