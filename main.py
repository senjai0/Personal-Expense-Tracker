import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# -----------------------------
# OOP-Based Database Class
# -----------------------------
class ExpenseDB:
    def __init__(self, db_name="expenses.db"):
        self.db_name = db_name
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        with self.connect() as conn:
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

    def add_expense(self, category, amount, date):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (category, amount, date)
                VALUES (?, ?, ?)
            """, (category, round(amount, 2), date))
            conn.commit()

    def get_expenses(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
            return cursor.fetchall()

    def update_expense(self, id, category, amount, date):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE expenses SET category = ?, amount = ?, date = ? WHERE id = ?
            """, (category, round(amount, 2), date, id))
            conn.commit()

    def delete_expense(self, id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (id,))
            deleted = cursor.fetchone()
            if deleted:
                cursor.execute("DELETE FROM expenses WHERE id = ?", (id,))
                conn.commit()
            return deleted

    def search_expenses(self, query):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE category LIKE ?", ('%' + query + '%',))
            return cursor.fetchall()

    def sort_expenses(self, by, reverse=False):
        order = "DESC" if reverse else "ASC"
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM expenses ORDER BY {by} {order}")
            return cursor.fetchall()

    def get_total_expenses(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
            totals = cursor.fetchall()
            cursor.execute("SELECT SUM(amount) FROM expenses")
            total_sum = cursor.fetchone()[0] or 0
            return totals, total_sum


# -----------------------------
# Streamlit UI Functions
# -----------------------------
def display_expenses(expenses):
    df = pd.DataFrame(expenses, columns=["ID", "Category", "Amount", "Date"])
    df["Amount"] = df["Amount"].apply(lambda x: round(x, 2))
    st.table(df)


def display_deleted_expenses():
    if st.session_state["deleted_expenses"]:
        df = pd.DataFrame(st.session_state["deleted_expenses"], columns=["ID", "Category", "Amount", "Date"])
        df["Amount"] = df["Amount"].apply(lambda x: round(x, 2))
        st.table(df)
    else:
        st.write("No deleted expenses.")


def display_total_expenses(totals, total):
    st.header("Total Expenses")
    st.write(f"**Overall Total Expenses**: ₱{round(total, 2)}")

    st.subheader("Expenses per Category")
    df = pd.DataFrame(totals, columns=["Category", "Total Amount"])
    df["Total Amount"] = df["Total Amount"].apply(lambda x: round(x, 2))
    st.table(df)


# -----------------------------
# Main Application
# -----------------------------
db = ExpenseDB()

if "deleted_expenses" not in st.session_state:
    st.session_state["deleted_expenses"] = []

if "show_deleted_expenses" not in st.session_state:
    st.session_state["show_deleted_expenses"] = False

st.title("Personal Expense Tracker")
st.sidebar.header("Expense Management")

with st.sidebar.expander("Add Expense"):
    categories = ["Food", "Transportation Fare", "House Rent", "Clothing"]
    category = st.selectbox("Category", categories)
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    date = st.date_input("Date", value=datetime.now().date())

    if st.button("Add Expense"):
        if category and amount > 0:
            db.add_expense(category, amount, date.strftime("%Y-%m-%d"))
            st.success("Expense added!")
        else:
            if not category:
                st.error("Please select a valid category.")
            if amount <= 0:
                st.error("Please enter a valid amount greater than 0.")

# Show Expenses
st.header("Expenses")
expenses = db.get_expenses()
if expenses:
    display_expenses(expenses)

    with st.expander("Update/Delete Expense"):
        index = st.number_input("Select Index to Update/Delete", min_value=0, max_value=len(expenses)-1)
        selected = expenses[index]
        new_cat = st.text_input("New Category", value=selected[1])
        new_amt = st.number_input("New Amount", min_value=0.0, format="%.2f", value=selected[2])
        new_date = st.date_input("New Date", value=datetime.strptime(selected[3], "%Y-%m-%d").date())

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Expense"):
                db.update_expense(selected[0], new_cat, new_amt, new_date.strftime("%Y-%m-%d"))
                st.success("Expense updated!")
        with col2:
            if st.button("Delete Expense"):
                deleted = db.delete_expense(selected[0])
                st.session_state["deleted_expenses"].append(deleted)
                st.success("Expense deleted!")
else:
    st.write("No expenses recorded.")

# Show/Hide Deleted
if st.button("Show/Hide Deleted Expenses History"):
    st.session_state["show_deleted_expenses"] = not st.session_state["show_deleted_expenses"]

if st.session_state["show_deleted_expenses"]:
    display_deleted_expenses()

# Search
st.header("Search Expenses")
query = st.text_input("Search by Category")
if st.button("Search"):
    results = db.search_expenses(query)
    if results:
        display_expenses(results)
    else:
        st.write("No results found.")

# Sort
st.header("Sort Expenses")
col1, col2 = st.columns(2)
with col1:
    sort_by = st.selectbox("Sort By", ["Category", "Amount", "Date"])
with col2:
    order = st.selectbox("Order", ["Ascending", "Descending"])

if st.button("Sort"):
    sorted_exp = db.sort_expenses(sort_by.lower(), reverse=(order == "Descending"))
    display_expenses(sorted_exp)
    st.success("Expenses sorted!")

# Totals
total_per_cat, total = db.get_total_expenses()
display_total_expenses(total_per_cat, total)
