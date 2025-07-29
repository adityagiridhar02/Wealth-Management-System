# 💰 Wealth Management System

A Python-based GUI(Streamlit) based application to help users manage their financial investments, including stocks, mutual funds, and insurance. This system allows users to add, delete, view, and update financial assets while storing all records securely in an SQLite database.

---

## 🚀 Features

* 📈 **Investment Tracking**: Manage assets across three categories:

  * Stocks
  * Mutual Funds
  * Insurance
* 🗂️ **CRUD Operations**: Add, delete, update, and retrieve investment records.
* 📈 **Aggregated Statistics**: Display total invested amount by category.
* 🛠️ **Modular Design**: Built with separation between database operations and user interface logic.
* 📂 **Local Persistence**: Uses SQLite for storing user data.

---

## 🏗️ Project Structure

```
Wealth-Management-System/
├── app.py                  # Main application
├── database_manager.py     # Database abstraction and logic
├── Table-Schemas.txt       # SQL schema for initial database setup
└── README.md               # Project documentation
```

---

## 🧰 Prerequisites

* Python 3.7+
* SQLite (comes bundled with Python standard library)

---

## ⚙️ Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone https://github.com/adityagiridhar02/Wealth-Management-System.git
   cd Wealth-Management-System
   ```

2. **Set Up the Database**
   Run the SQL statements from `Table-Schemas.txt` using SQLite:

   ```bash
   sqlite3 wealth_management.db < Table-Schemas.txt
   ```

3. **Run the Application**

   ```bash
   python app.py
   ```

---

## 📟 Table Schemas (from `Table-Schemas.txt`)

* `Stocks(id INTEGER PRIMARY KEY, name TEXT, units INTEGER, price REAL)`
* `MutualFunds(id INTEGER PRIMARY KEY, name TEXT, units INTEGER, price REAL)`
* `Insurance(id INTEGER PRIMARY KEY, name TEXT, premium REAL, term INTEGER)`

---

## 🖥️ Usage Guide

Once the app is running, it will prompt you with a menu of options:

* View Investments
* Add Investment
* Delete Investment
* Update Investment
* Show Total Investment by Category
* Exit

Navigate by entering the number corresponding to your choice.

---

## 📈 Sample Commands (internal logic examples)

* `add_investment(category, name, units, price)`
* `delete_investment(category, id)`
* `update_investment(category, id, units, price)`
* `fetch_investments(category)`

These are implemented in `database_manager.py`.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE) - feel free to use and modify.
