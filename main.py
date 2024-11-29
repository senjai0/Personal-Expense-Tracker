import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime


# 1. Database Helper Functions
def create_connection():
    """Create and return a database connection."""
    return sqlite3.connect("expenses.db")


def create_table():
    """Create the expenses table if it doesn't exist."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


def add_expense(category, amount, date):
    """Insert a new expense into the database."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
    INSERT INTO expenses (category, amount, date) 
    VALUES (?, ?, ?)
    """, (category, round(amount, 2), date))
    conn.commit()
    conn.close()


def get_expenses():
    """Fetch all expenses from the database."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    expenses = cursor.fetchall()
    conn.close()
    return expenses


def update_expense(id, category, amount, date):
    """Update an existing expense in the database."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
    UPDATE expenses SET category = ?, amount = ?, date = ? WHERE id = ?
    """, (category, round(amount, 2), date, id))
    conn.commit()
    conn.close()


def delete_expense(id):
    """Delete an expense from the database and return it."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE id = ?", (id, ))
    deleted_expense = cursor.fetchone()
    if deleted_expense:
        cursor.execute("DELETE FROM expenses WHERE id = ?", (id, ))
        conn.commit()
    conn.close()
    return deleted_expense


def search_expenses(query):
    """Search for expenses by category."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE category LIKE ?",
                   ('%' + query + '%', ))
    expenses = cursor.fetchall()
    conn.close()
    return expenses


def sort_expenses(by, reverse=False):
    """Sort expenses based on a given column and order."""
    conn = create_connection()
    cursor = conn.cursor()
    order = "DESC" if reverse else "ASC"
    cursor.execute(f"SELECT * FROM expenses ORDER BY {by} {order}")
    expenses = cursor.fetchall()
    conn.close()
    return expenses


# 2. Streamlit UI Helper Functions
def display_expenses(expenses):
    """Helper function to display expenses as a table."""
    df = pd.DataFrame(expenses, columns=["ID", "Category", "Amount", "Date"])
    df["Amount"] = df["Amount"].apply(
        lambda x: round(x, 2))  # Round to 2 decimals
    st.table(df)


def display_deleted_expenses():
    """Display deleted expenses history."""
    if st.session_state["deleted_expenses"]:
        deleted_df = pd.DataFrame(st.session_state["deleted_expenses"],
                                  columns=["ID", "Category", "Amount", "Date"])
        deleted_df["Amount"] = deleted_df["Amount"].apply(
            lambda x: round(x, 2))
        st.table(deleted_df)
    else:
        st.write("No deleted expenses.")


# 3. Main Streamlit Application
# Initialize the app with a session state for deleted expenses and show/hide toggle state
if "deleted_expenses" not in st.session_state:
    st.session_state["deleted_expenses"] = []

if "show_deleted_expenses" not in st.session_state:
    st.session_state["show_deleted_expenses"] = False

# Create the table in the database if it doesn't exist
create_table()

# Streamlit app layout
st.title("Personal Expense Tracker")
st.sidebar.header("Expense Management")

# Add Expense
with st.sidebar.expander("Add Expense"):
    category = st.text_input("Category")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    date = st.date_input("Date", value=datetime.now().date())
    if st.button("Add Expense"):
        add_expense(category, amount, date.strftime("%Y-%m-%d"))
        st.success("Expense added!")
    else st.button("Add Expense"):
        add_expense(category, amount, date.strftime("%Y-%m-%d"))
        st.success("Invalid!")

# Update/Delete Expense
st.header("Expenses")
expenses = get_expenses()
if expenses:
    display_expenses(expenses)

    with st.expander("Update/Delete Expense"):
        index = st.number_input("Select Index to Update/Delete",
                                min_value=0,
                                max_value=len(expenses) - 1)
        selected_expense = expenses[index]
        new_category = st.text_input("New Category", value=selected_expense[1])
        new_amount = st.number_input("New Amount",
                                     min_value=0.0,
                                     format="%.2f",
                                     value=selected_expense[2])
        new_date = st.date_input("New Date",
                                 value=datetime.strptime(
                                     selected_expense[3], "%Y-%m-%d").date())

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Expense"):
                update_expense(selected_expense[0], new_category, new_amount,
                               new_date.strftime("%Y-%m-%d"))
                st.success("Expense updated!")
        with col2:
            if st.button("Delete Expense"):
                deleted_expense = delete_expense(selected_expense[0])
                st.session_state["deleted_expenses"].append(deleted_expense)
                st.success("Expense deleted!")
else:
    st.write("No expenses recorded.")

# Show/Hide Deleted Expenses History with Toggle Button
if st.button("Show/Hide Deleted Expenses History"):
    # Toggle the visibility state of deleted expenses
    st.session_state["show_deleted_expenses"] = not st.session_state[
        "show_deleted_expenses"]

# Conditionally display the deleted expenses history
if st.session_state["show_deleted_expenses"]:
    display_deleted_expenses()

# Search Expenses
st.header("Search Expenses")
query = st.text_input("Search by Category")
if st.button("Search"):
    results = search_expenses(query)
    if results:
        display_expenses(results)
    else:
        st.write("No results found.")

# Sort Expenses
st.header("Sort Expenses")
col1, col2 = st.columns(2)

with col1:
    sort_by = st.selectbox("Sort By", ["Category", "Amount", "Date"])
with col2:
    order = st.selectbox("Order", ["Ascending", "Descending"])

if st.button("Sort"):
    sorted_expenses = sort_expenses(sort_by.lower(),
                                    reverse=(order == "Descending"))
    display_expenses(sorted_expenses)
    st.success("Expenses sorted!")
