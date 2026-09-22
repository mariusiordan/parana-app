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

    print(f"\nWelcome {shopper['shopper_first_name']} {shopper['shopper_surname']}!\n")
    return shopper

def get_current_basket(connection, shopper_id):
    """Find the shopper's most recent basket created today, if one exists"""
    query = """
        SELECT basket_id
        FROM shopper_baskets
        WHERE shopper_id = ?
        AND DATE(basket_created_date_time) = DATE('now')
        ORDER BY basket_created_date_time DESC
        LIMIT 1
    """

    basket = connection.execute(query, (shopper_id,)).fetchone()

    if basket is None:
        return None

    return basket["basket_id"]

def display_menu():
    """Print the main menu and return the option number chosen by the user."""
    print("\n================================")
    print("--- Parana Shopper Main Menu ---")
    print("================================")
    print("[1] Display your order history")
    print("[2] Add an item to your basket")
    print("[3] View your basket")
    print("[4] Change the quantity of an item in your basket")
    print("[5] Remove an item from your basket")
    print("[6] Checkout")
    print("[7] Exit")

    while True:
        choice = input("\nEnter the number against the menu option you want to choose (1-7): ").strip()
        if choice in ("1", "2", "3", "4", "5", "6", "7"):
            return int(choice)
        print("Please enter a number between 1 and 7.")


def display_order_history(connection, shopper_id):
    """Display every order placed by the shopper, most recent first"""
    query = """
        SELECT so.order_id,
               so.order_date,
               p.product_description,
               se.seller_name,
               op.price,
               op.quantity,
               op.ordered_product_status
        FROM shopper_orders so
        JOIN ordered_products op ON so.order_id = op.order_id
        JOIN products p          ON op.product_id = p.product_id
        JOIN sellers se          ON op.seller_id = se.seller_id
        WHERE so.shopper_id = ?
        ORDER BY so.order_date DESC, so.order_id DESC
    """

    orders = connection.execute(query, (shopper_id,)).fetchall()

    if not orders:
        print("\nNo orders placed by this customer")
        return

    # Column widths, used for both the headings and the data rows
    widths = [10, 12, 45, 22, 10, 5, 10]
    headings = ["Order ID", "Order Date", "Product Description",
                "Seller", "Price", "Qty", "Status"]

    # Title, underlined to the width of the title itself
    title = "Order History"
    print(f"\n{title}")
    print("-" * len(title))

    # Column headings, each underlined with dashes matching its own width
    heading_line = ""
    dashes_line = ""
    for heading, width in zip(headings, widths):
        heading_line += f"{heading:<{width}}"
        dashes_line += f"{'-' * len(heading):<{width}}"

    print(f"\n{heading_line}")
    print(dashes_line)

    # Data rows
    for row in orders:
        price = f"£{row['price']:.2f}"
        line = ""
        line += f"{row['order_id']:<{widths[0]}}"
        line += f"{row['order_date']:<{widths[1]}}"
        line += f"{row['product_description'][:widths[2] - 2]:<{widths[2]}}"
        line += f"{row['seller_name'][:widths[3] - 2]:<{widths[3]}}"
        line += f"{price:<{widths[4]}}"
        line += f"{row['quantity']:<{widths[5]}}"
        line += f"{row['ordered_product_status']:<{widths[6]}}"
        print(line)

    print()

def _display_options(all_options, title, type):
    """Display a numbered list of options and return the id of the one selected"""
    option_num = 1
    option_list = []

    print("\n", title, "\n")

    for option in all_options:
        code = option[0]
        desc = option[1]
        print("{0}.\t{1}".format(option_num, desc))
        option_num = option_num + 1
        option_list.append(code)

    selected_option = 0

    while selected_option > len(option_list) or selected_option <= 0:
        prompt = "Enter the number against the " + type + " you want to choose: "
        try:
            selected_option = int(input(prompt))
            if selected_option > len(option_list) or selected_option <= 0:
                print("Please enter a number between 1 and", len(option_list))
        except ValueError:
            print("Please enter a valid number.")
            selected_option = 0

    return option_list[selected_option - 1]

def add_item_to_basket(connection, shopper_id, current_basket_id):
    """Add a product to the shopper's basket. """

    # Display product categories in alphabetical order
    categories = connection.execute("""
        SELECT category_id, category_description
        FROM categories
        ORDER BY category_description
    """).fetchall()

    category_id = _display_options(categories, "Product Categories", "category")

    # Display available products in the chosen category
    products = connection.execute("""
        SELECT product_id, product_description
        FROM products
        WHERE category_id = ?
        AND product_status = 'Available'
        ORDER BY product_description
    """, (category_id,)).fetchall()

    if not products:
        print("\nThere are no available products in this category.")
        return current_basket_id

    product_id = _display_options(products, "Products", "product")

    # Display sellers for the chosen product, with their prices
    sellers = connection.execute("""
        SELECT ps.seller_id,
               se.seller_name || ' - £' || printf('%.2f', ps.price)
        FROM product_sellers ps
        JOIN sellers se ON ps.seller_id = se.seller_id
        WHERE ps.product_id = ?
        ORDER BY se.seller_name
    """, (product_id,)).fetchall()

    if not sellers:
        print("\nThere are no sellers for this product.")
        return current_basket_id

    seller_id = _display_options(sellers, "Sellers", "seller")

    # Prompt for the quantity, which must be greater than zero
    quantity = 0
    while quantity <= 0:
        try:
            quantity = int(input("Enter the quantity of the selected product: "))
            if quantity <= 0:
                print("The quantity must be greater than 0")
        except ValueError:
            print("The quantity must be greater than 0")
            quantity = 0

    # Get the price charged by the chosen seller
    price_row = connection.execute("""
        SELECT price
        FROM product_sellers
        WHERE product_id = ? AND seller_id = ?
    """, (product_id, seller_id)).fetchone()

    price = price_row["price"]

    #  Create a new basket if the shopper does not have one
    if current_basket_id is None:
        next_id_row = connection.execute("""
            SELECT seq
            FROM sqlite_sequence
            WHERE name = 'shopper_baskets'
        """).fetchone()

        # If no baskets have ever been created, start at 1
        current_basket_id = (next_id_row["seq"] + 1) if next_id_row else 1

        connection.execute("""
            INSERT INTO shopper_baskets (basket_id, shopper_id, basket_created_date_time)
            VALUES (?, ?, datetime('now'))
        """, (current_basket_id, shopper_id))

        # Keep sqlite_sequence in step, as the id was supplied explicitly
        connection.execute("""
            UPDATE sqlite_sequence
            SET seq = ?
            WHERE name = 'shopper_baskets'
        """, (current_basket_id,))

    # Add the product to the basket
    connection.execute("""
        INSERT INTO basket_contents (basket_id, product_id, seller_id, quantity, price)
        VALUES (?, ?, ?, ?, ?)
    """, (current_basket_id, product_id, seller_id, quantity, price))

    # Commit the transaction
    connection.commit()

    # Confirm to the user what has been added
    product_row = connection.execute("""
        SELECT product_description
        FROM products
        WHERE product_id = ?
    """, (product_id,)).fetchone()

    seller_row = connection.execute("""
        SELECT seller_name
        FROM sellers
        WHERE seller_id = ?
    """, (seller_id,)).fetchone()

    total = price * quantity

    print("\nItem added to your basket")
    print(f"   Product:  {product_row['product_description']}")
    print(f"   Seller:   {seller_row['seller_name']}")
    print(f"   Quantity: {quantity} X £{price:.2f}")
    print(f"   Subtotal: £{total:.2f}")

    return current_basket_id

def display_basket(connection, basket_id):
    """Display the contents of the current basket with a total cost """

    # No basket has been created
    if basket_id is None:
        print("\nYour basket is empty")
        return []

    query = """
        SELECT bc.product_id,
               bc.seller_id,
               p.product_description,
               se.seller_name,
               bc.quantity,
               bc.price
        FROM basket_contents bc
        JOIN products p ON bc.product_id = p.product_id
        JOIN sellers se ON bc.seller_id = se.seller_id
        WHERE bc.basket_id = ?
        ORDER BY p.product_description
    """

    items = connection.execute(query, (basket_id,)).fetchall()

    # The basket exists but every item has been removed
    if not items:
        print("\nYour basket is empty")
        return []

    # Column widths, used for the headings, underlines and data rows
    widths = [13, 45, 22, 6, 12, 12]
    headings = ["Basket Item", "Product Description", "Seller Name",
                "Qty", "Price", "Total"]

    title = "Basket Contents"
    print(f"\n{title}")
    print("-" * len(title))

    heading_line = ""
    dashes_line = ""
    for heading, width in zip(headings, widths):
        heading_line += f"{heading:<{width}}"
        dashes_line += f"{'-' * len(heading):<{width}}"

    print(f"\n{heading_line}")
    print(dashes_line)

    basket_total = 0

    # Number each item from 1 and add its cost to the running total
    for item_no, item in enumerate(items, start=1):
        line_total = item["price"] * item["quantity"]
        basket_total += line_total

        line = ""
        line += f"{item_no:<{widths[0]}}"
        line += f"{item['product_description'][:widths[1] - 2]:<{widths[1]}}"
        line += f"{item['seller_name'][:widths[2] - 2]:<{widths[2]}}"
        line += f"{item['quantity']:<{widths[3]}}"
        line += f"{'£' + format(item['price'], '.2f'):<{widths[4]}}"
        line += f"{'£' + format(line_total, '.2f'):<{widths[5]}}"
        print(line)

    # Basket total, aligned under the Total column
    label_width = sum(widths[:5])
    print(f"\n{'Basket Total':>{label_width - 2}}  £{basket_total:,.2f}")

    return items

def checkout_basket(connection, shopper_id, basket_id):
    """Convert the current basket into an order"""

    # Nothing to checkout if the basket is empty
    # Display the basket and total, reusing option 3
    items = display_basket(connection, basket_id)

    if not items:
        print("There is nothing to check out.")
        return basket_id

    # Ask the shopper to confirm, accepting only Y or N
    while True:
        answer = input("\nDo you wish to proceed with the checkout? (Y or N): ").strip().upper()
        if answer in ("Y", "N"):
            break
        print("Please enter Y or N.")

    if answer == "N":
        print("Checkout cancelled.")
        return basket_id

    try:
        # Create the order; order_id is generated by AUTOINCREMENT
        cursor = connection.execute("""
            INSERT INTO shopper_orders (shopper_id, order_date, order_status)
            VALUES (?, DATE('now'), 'Placed')
        """, (shopper_id,))

        order_id = cursor.lastrowid

        # Copy every basket item into ordered_products
        for item in items:
            connection.execute("""
                INSERT INTO ordered_products
                    (order_id, product_id, seller_id, quantity, price, ordered_product_status)
                VALUES (?, ?, ?, ?, ?, 'Placed')
            """, (order_id, item["product_id"], item["seller_id"],
                  item["quantity"], item["price"]))

        # Delete the basket, contents first, as they reference the basket
        connection.execute("DELETE FROM basket_contents WHERE basket_id = ?", (basket_id,))
        connection.execute("DELETE FROM shopper_baskets WHERE basket_id = ?", (basket_id,))

        # Save all the changes together
        connection.commit()

    except sqlite3.Error as error:
        # Undo every change made since the transaction began
        connection.rollback()
        print(f"\nThe checkout could not be completed and no changes were saved: {error}")
        return basket_id

    # Confirm success
    print(f"\nCheckout complete, your order has been placed (order id {order_id})")

    # The basket has been deleted, so there is no longer a current basket
    return None

def remove_item_from_basket(connection, basket_id):
    """Remove an item from the current basket"""

    # Display the basket, the function shows 'Your basket is empty' itself
    items = display_basket(connection, basket_id)

    if not items:
        return

    # Only ask which item if there is more than one to choose from
    if len(items) == 1:
        selected_item = items[0]
        print("\nThere is only one item in your basket, so this is the one that will be removed.")
    else:
        while True:
            entered = input(f"\nEnter the basket item no. you want to remove (1-{len(items)}): ").strip()
            if entered.isdigit() and 1 <= int(entered) <= len(items):
                selected_item = items[int(entered) - 1]
                break
            print("The basket item no. you have entered is invalid")

    # Confirm before deleting anything, accepting only Y or N
    while True:
        answer = input(f"\nAre you sure you want to remove {selected_item['product_description']}? (Y or N): ").strip().upper()
        if answer in ("Y", "N"):
            break
        print("Please enter Y or N.")

    if answer == "N":
        print("\nThe item has not been removed.")
        display_basket(connection, basket_id)
        return

    # Delete the selected row from the current basket
    connection.execute("""
        DELETE FROM basket_contents
        WHERE basket_id = ? AND product_id = ? AND seller_id = ?
    """, (basket_id, selected_item["product_id"], selected_item["seller_id"]))

    connection.commit()

    print(f"\n{selected_item['product_description']} has been removed from your basket")

    # Display the basket again, it shows 'Your basket is empty' if nothing remains
    display_basket(connection, basket_id)

def change_item_quantity(connection, basket_id):
    """Change the quantity of an item in the current basket"""

    # Display the basket, the function shows 'Your basket is empty' itself
    items = display_basket(connection, basket_id)

    if not items:
        return

    # Only ask which item if there is more than one to choose from
    if len(items) == 1:
        selected_item = items[0]
        print("\nThere is only one item in your basket, so this is the one that will be changed.")
    else:
        while True:
            entered = input(f"\nEnter the basket item no. you want to update (1-{len(items)}): ").strip()
            if entered.isdigit() and 1 <= int(entered) <= len(items):
                selected_item = items[int(entered) - 1]
                break
            print("The basket item no. you have entered is invalid")

    # Prompt for the new quantity, which must be greater than zero
    new_quantity = 0
    while new_quantity <= 0:
        try:
            new_quantity = int(input("Enter the new quantity for this item: "))
            if new_quantity <= 0:
                print("The quantity must be greater than 0")
        except ValueError:
            print("The quantity must be greater than 0")
            new_quantity = 0

    # Update the row for this basket, product and seller
    connection.execute("""
        UPDATE basket_contents
        SET quantity = ?
        WHERE basket_id = ? AND product_id = ? AND seller_id = ?
    """, (new_quantity, basket_id, selected_item["product_id"], selected_item["seller_id"]))

    connection.commit()

    print(f"\nThe quantity for {selected_item['product_description']} has been changed to {new_quantity}")

    # Display the basket again with the recalculated total
    display_basket(connection, basket_id)


if __name__ == "__main__":
    conn = connect_to_database()

    if conn is None:
        exit(1)

    current_shopper = get_shopper(conn)

    if current_shopper is None:
        conn.close()
        exit(1)

    shopper_id = current_shopper["shopper_id"]
    current_basket_id = get_current_basket(conn, shopper_id)

    if current_basket_id is None:
        print("You have no basket from today. A new one will be created when you add an item.")
    else:
        print(f"Resuming your basket from today (basket id {current_basket_id}).")

    while True:
        option = display_menu()

        if option == 1:
            display_order_history(conn, shopper_id)
        elif option == 2:
            current_basket_id = add_item_to_basket(conn, shopper_id, current_basket_id)
        elif option == 3:
            display_basket(conn, current_basket_id)
        elif option == 4:
            change_item_quantity(conn, current_basket_id)
        elif option == 5:
            remove_item_from_basket(conn, current_basket_id)
        elif option == 6:
            current_basket_id = checkout_basket(conn, shopper_id, current_basket_id)
        elif option == 7:
            print("\nThank you for using Parana. Goodbye.")
            break
       
    conn.close()