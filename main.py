import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize the app with a session state
if "expenses" not in st.session_state:
    st.session_state["expenses"] = []

if "deleted_expenses" not in st.session_state:
    st.session_state["deleted_expenses"] = []


# Helper functions
def add_expense(category, amount, date):
    expense = {
        "Category": category,
        "Amount": round(amount, 2),
        "Date": date
    }  # Round the amount here
    st.session_state["expenses"].append(expense)


def update_expense(index, category, amount, date):
    st.session_state["expenses"][index] = {
        "Category": category,
        "Amount": round(amount, 2),
        "Date": date
    }  # Round the amount here


def delete_expense(index):
    deleted_expense = st.session_state["expenses"].pop(
        index)  # Pop the expense and store it in deleted_expenses
    st.session_state["deleted_expenses"].append(deleted_expense)


def search_expenses(query):
    return [
        expense for expense in st.session_state["expenses"]
        if query.lower() in expense["Category"].lower()
    ]


def sort_expenses(by, reverse=False):
    st.session_state["expenses"] = sorted(st.session_state["expenses"],
                                          key=lambda x: x[by],
                                          reverse=reverse)


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

# Update/Delete Expense
st.header("Expenses")
if st.session_state["expenses"]:
    # Formatting amount column to 2 decimal places
    df = pd.DataFrame(st.session_state["expenses"])
    df["Amount"] = df["Amount"].apply(
        lambda x: round(x, 2))  # rounding to 2 decimals
    st.table(df)

    with st.expander("Update/Delete Expense"):
        index = st.number_input("Select Index to Update/Delete",
                                min_value=0,
                                max_value=len(df) - 1)
        new_category = st.text_input(
            "New Category",
            value=st.session_state["expenses"][index]["Category"])
        new_amount = st.number_input(
            "New Amount",
            min_value=0.0,
            format="%.2f",
            value=st.session_state["expenses"][index]["Amount"])
        new_date = st.date_input(
            "New Date",
            value=datetime.strptime(
                st.session_state["expenses"][index]["Date"],
                "%Y-%m-%d").date())

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Expense"):
                update_expense(index, new_category, new_amount,
                               new_date.strftime("%Y-%m-%d"))
                st.success("Expense updated!")
        with col2:
            if st.button("Delete Expense"):
                delete_expense(index)
                st.success("Expense deleted!")
else:
    st.write("No expenses recorded.")

# Button to show Deleted Expenses History
if st.button("Show Deleted Expenses History"):
    if st.session_state["deleted_expenses"]:
        deleted_df = pd.DataFrame(st.session_state["deleted_expenses"])
        deleted_df["Amount"] = deleted_df["Amount"].apply(
            lambda x: round(x, 2))  # rounding to 2 decimals
        st.table(deleted_df)
    else:
        st.write("No deleted expenses.")

# Search Expenses
st.header("Search Expenses")
query = st.text_input("Search by Category")
if st.button("Search"):
    results = search_expenses(query)
    if results:
        # Formatting amount column to 2 decimal places for search results
        search_results_df = pd.DataFrame(results)
        search_results_df["Amount"] = search_results_df["Amount"].apply(
            lambda x: round(x, 2))  # rounding to 2 decimals
        st.table(search_results_df)
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
    sort_expenses(sort_by, reverse=(order == "Descending"))
    st.success("Expenses sorted!")
