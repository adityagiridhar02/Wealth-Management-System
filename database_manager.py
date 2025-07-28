import mysql.connector
from mysql.connector import Error
import pandas as pd
from decimal import Decimal

# --- Database Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'database': 'wealth_management',
    'user': 'root',
    'password': 'root'
}

def create_connection():
    """Establishes a connection to the MySQL database."""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """Executes a SQL query and optionally fetches results.
    Raises mysql.connector.Error on database operation failure.
    Returns:
        - List of dicts if fetch=True
        - lastrowid for INSERT queries
        - True for successful UPDATE/DELETE queries (if rows affected)
        - False if no rows affected by UPDATE/DELETE
        - None if connection fails (propagated from create_connection)
    """
    connection = create_connection()
    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            if query.strip().upper().startswith("INSERT"):
                return cursor.lastrowid
            elif query.strip().upper().startswith(("UPDATE", "DELETE")):
                return cursor.rowcount > 0
            return True
    except Error as e:
        connection.rollback()
        print(f"Error executing query: {e}")
        raise e # Re-raise the exception for app.py to catch
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# --- User Management ---
def add_user(username, password, email=None, role='user'):
    """Adds a new user to the database with a specified role."""
    query = "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)"
    return execute_query(query, (username, password, email, role))

def get_user_by_username(username):
    """Retrieves a user by username."""
    query = "SELECT * FROM users WHERE username = %s"
    return execute_query(query, (username,), fetch=True)

def get_user_by_id(user_id):
    """Retrieves a user by ID."""
    query = "SELECT * FROM users WHERE user_id = %s"
    return execute_query(query, (user_id,), fetch=True)

def get_user_role(user_id):
    """Retrieves the role of a user."""
    query = "SELECT role FROM users WHERE user_id = %s"
    result = execute_query(query, (user_id,), fetch=True)
    return result[0]['role'] if result else None

def get_all_users():
    """Retrieves all registered users."""
    query = "SELECT user_id, username, email, role, created_at FROM users"
    return execute_query(query, fetch=True)

def delete_user_and_all_data(user_id):
    """
    Deletes a user and all associated data (transactions, investments, accounts, portfolios).
    This function handles cascading deletions manually due to ON DELETE RESTRICT constraints.
    Returns True on success, False on failure.
    Raises mysql.connector.Error if a database error occurs during any step.
    """
    connection = None
    try:
        connection = create_connection()
        if connection is None:
            return False

        cursor = connection.cursor()
        
        # Start a transaction
        connection.start_transaction()

        # 1. Delete user's transactions
        cursor.execute("DELETE FROM transactions WHERE user_id = %s", (user_id,))
        print(f"Deleted {cursor.rowcount} transactions for user {user_id}")

        # 2. Delete user's investments
        cursor.execute("DELETE FROM investments WHERE user_id = %s", (user_id,))
        print(f"Deleted {cursor.rowcount} investments for user {user_id}")

        # 3. Delete user's accounts
        cursor.execute("DELETE FROM accounts WHERE user_id = %s", (user_id,))
        print(f"Deleted {cursor.rowcount} accounts for user {user_id}")

        # 4. Delete user's portfolios
        cursor.execute("DELETE FROM portfolios WHERE user_id = %s", (user_id,))
        print(f"Deleted {cursor.rowcount} portfolios for user {user_id}")

        # 5. Delete the user itself
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        print(f"Deleted {cursor.rowcount} user record for user {user_id}")
        
        connection.commit()
        return True
    except Error as e:
        if connection:
            connection.rollback() # Rollback on error
        print(f"Error deleting user {user_id} and their data: {e}")
        raise e # Re-raise the error for app.py to handle
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- Portfolio Management ---
def add_portfolio(user_id, portfolio_name, description=None):
    """Adds a new portfolio for a user."""
    query = "INSERT INTO portfolios (user_id, portfolio_name, description) VALUES (%s, %s, %s)"
    return execute_query(query, (user_id, portfolio_name, description))

def get_portfolios_by_user(user_id):
    """Retrieves all portfolios for a given user."""
    query = "SELECT * FROM portfolios WHERE user_id = %s"
    return execute_query(query, (user_id,), fetch=True)

def update_portfolio(portfolio_id, portfolio_name=None, description=None):
    """Updates an existing portfolio."""
    updates = []
    params = []
    if portfolio_name is not None:
        updates.append("portfolio_name = %s")
        params.append(portfolio_name)
    if description is not None:
        updates.append("description = %s")
        params.append(description)

    if not updates:
        return False

    query = f"UPDATE portfolios SET {', '.join(updates)} WHERE portfolio_id = %s"
    params.append(portfolio_id)
    return execute_query(query, tuple(params))

def delete_portfolio(portfolio_id):
    """Deletes a portfolio by its ID."""
    query = "DELETE FROM portfolios WHERE portfolio_id = %s"
    return execute_query(query, (portfolio_id,))

# --- Account Management ---
def add_account(user_id, account_name, account_type, initial_balance=0.00, currency='USD'):
    """Adds a new account for a user."""
    query = "INSERT INTO accounts (user_id, account_name, account_type, current_balance, currency) VALUES (%s, %s, %s, %s, %s)"
    return execute_query(query, (user_id, account_name, account_type, initial_balance, currency))

def get_accounts_by_user(user_id):
    """Retrieves all accounts for a given user."""
    query = "SELECT * FROM accounts WHERE user_id = %s"
    return execute_query(query, (user_id,), fetch=True)

def get_all_accounts():
    """Retrieves account balances of all users."""
    query = "SELECT a.*, u.username FROM accounts a JOIN users u ON a.user_id = u.user_id"
    return execute_query(query, fetch=True)

def update_account_balance(account_id, new_balance):
    """Updates the current balance of an account."""
    query = "UPDATE accounts SET current_balance = %s WHERE account_id = %s"
    return execute_query(query, (new_balance, account_id))

def delete_account(account_id):
    """Deletes an account by its ID."""
    query = "DELETE FROM accounts WHERE account_id = %s"
    return execute_query(query, (account_id,))

# --- Asset Type Management (Categories like Stock, Crypto) ---
def get_asset_types():
    """Retrieves all available asset types (categories)."""
    query = "SELECT * FROM asset_types ORDER BY type_name"
    return execute_query(query, fetch=True)

def add_asset_type(type_name, description=None):
    """Adds a new asset type (category)."""
    query = "INSERT INTO asset_types (type_name, description) VALUES (%s, %s)"
    return execute_query(query, (type_name, description))

# --- Asset Management (Specific assets like Gold, Bitcoin) ---
def add_asset(name, unit_price, unit_type):
    """Adds a new pre-defined asset."""
    query = "INSERT INTO assets (name, unit_price, unit_type) VALUES (%s, %s, %s)"
    return execute_query(query, (name, unit_price, unit_type))

def get_all_assets():
    """Retrieves all pre-defined assets."""
    query = "SELECT * FROM assets ORDER BY name"
    return execute_query(query, fetch=True)

def get_asset_by_id(asset_id):
    """Retrieves a specific asset by its ID."""
    query = "SELECT * FROM assets WHERE asset_id = %s"
    result = execute_query(query, (asset_id,), fetch=True)
    return result[0] if result else None

def update_asset_price(asset_id, new_unit_price):
    """Updates the unit price of an asset."""
    query = "UPDATE assets SET unit_price = %s WHERE asset_id = %s"
    return execute_query(query, (new_unit_price, asset_id))

# --- Investment Management (User's holdings of assets) ---
def add_investment(user_id, portfolio_id, asset_category_id, asset_id, investment_name, symbol, initial_investment_amount, purchase_date, quantity, currency='USD', notes=None):
    """Adds a new investment for a user, linked to a specific asset."""
    query = """
    INSERT INTO investments (user_id, portfolio_id, asset_category_id, asset_id, investment_name, symbol, initial_investment_amount, purchase_date, quantity, currency, notes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (user_id, portfolio_id, asset_category_id, asset_id, investment_name, symbol, initial_investment_amount, purchase_date, quantity, currency, notes)
    return execute_query(query, params)

def get_investments_by_user(user_id):
    """Retrieves all investments for a given user, including portfolio, asset category, and current asset price."""
    query = """
    SELECT
        i.investment_id,
        i.user_id,
        i.portfolio_id,
        p.portfolio_name,
        i.asset_category_id,
        at.type_name AS asset_category_name,
        i.asset_id,
        a.name AS asset_name,
        a.unit_price AS current_unit_price, -- Get current price from assets table
        a.unit_type,
        i.investment_name,
        i.symbol,
        i.initial_investment_amount,
        i.purchase_date,
        i.quantity,
        (i.quantity * a.unit_price) AS current_value, -- Dynamically calculate current_value
        i.currency,
        i.notes
    FROM investments i
    JOIN portfolios p ON i.portfolio_id = p.portfolio_id
    JOIN asset_types at ON i.asset_category_id = at.asset_type_id
    JOIN assets a ON i.asset_id = a.asset_id
    WHERE i.user_id = %s
    """
    return execute_query(query, (user_id,), fetch=True)

def get_all_investments_detailed():
    """Retrieves all investments for all users, with detailed asset info and dynamic value."""
    query = """
    SELECT
        i.investment_id,
        i.user_id,
        u.username,
        i.portfolio_id,
        p.portfolio_name,
        i.asset_category_id,
        at.type_name AS asset_category_name,
        i.asset_id,
        a.name AS asset_name,
        a.unit_price AS current_unit_price,
        a.unit_type,
        i.investment_name,
        i.symbol,
        i.initial_investment_amount,
        i.purchase_date,
        i.quantity,
        (i.quantity * a.unit_price) AS current_value,
        i.currency,
        i.notes
    FROM investments i
    JOIN users u ON i.user_id = u.user_id
    JOIN portfolios p ON i.portfolio_id = p.portfolio_id
    JOIN asset_types at ON i.asset_category_id = at.asset_type_id
    JOIN assets a ON i.asset_id = a.asset_id
    ORDER BY u.username, p.portfolio_name, i.investment_name
    """
    return execute_query(query, fetch=True)


def update_investment(investment_id, investment_name=None, symbol=None, initial_investment_amount=None, purchase_date=None, quantity=None, currency=None, notes=None, portfolio_id=None, asset_category_id=None, asset_id=None):
    """Updates an existing investment."""
    updates = []
    params = []
    if investment_name is not None:
        updates.append("investment_name = %s")
        params.append(investment_name)
    if symbol is not None:
        updates.append("symbol = %s")
        params.append(symbol)
    if initial_investment_amount is not None:
        updates.append("initial_investment_amount = %s")
        params.append(initial_investment_amount)
    if purchase_date is not None:
        updates.append("purchase_date = %s")
        params.append(purchase_date)
    if quantity is not None:
        updates.append("quantity = %s")
        params.append(quantity)
    # current_value is now dynamically calculated, so it's not updated directly
    if currency is not None:
        updates.append("currency = %s")
        params.append(currency)
    if notes is not None:
        updates.append("notes = %s")
        params.append(notes)
    if portfolio_id is not None:
        updates.append("portfolio_id = %s")
        params.append(portfolio_id)
    if asset_category_id is not None:
        updates.append("asset_category_id = %s")
        params.append(asset_category_id)
    if asset_id is not None:
        updates.append("asset_id = %s")
        params.append(asset_id)

    if not updates:
        return False

    query = f"UPDATE investments SET {', '.join(updates)} WHERE investment_id = %s"
    params.append(investment_id)
    return execute_query(query, tuple(params))

def delete_investment(investment_id):
    """Deletes an investment by its ID."""
    query = "DELETE FROM investments WHERE investment_id = %s"
    return execute_query(query, (investment_id,))

# --- Transaction Management ---
def add_transaction(user_id, account_id=None, investment_id=None, asset_id=None, transaction_type=None, amount=None, quantity=None, unit_price_at_transaction=None, description=None):
    """Adds a new transaction, supporting both account-based and asset-based transactions."""
    query = """
    INSERT INTO transactions (user_id, account_id, investment_id, asset_id, transaction_type, amount, quantity, unit_price_at_transaction, description)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (user_id, account_id, investment_id, asset_id, transaction_type, amount, quantity, unit_price_at_transaction, description)
    return execute_query(query, params)

def get_transactions_by_user(user_id):
    """Retrieves all transactions for a given user, including account, investment, and asset names."""
    query = """
    SELECT
        t.transaction_id,
        t.user_id,
        t.account_id,
        a.account_name,
        t.investment_id,
        i.investment_name,
        t.asset_id,
        ast.name AS asset_name, -- Alias for asset name from assets table
        t.transaction_type,
        t.amount,
        t.quantity,
        t.unit_price_at_transaction,
        t.description,
        t.transaction_date
    FROM transactions t
    LEFT JOIN accounts a ON t.account_id = a.account_id
    LEFT JOIN investments i ON t.investment_id = i.investment_id
    LEFT JOIN assets ast ON t.asset_id = ast.asset_id -- Join with assets table
    WHERE t.user_id = %s
    ORDER BY t.transaction_date DESC
    """
    return execute_query(query, (user_id,), fetch=True)

def get_all_transactions_detailed():
    """Retrieves full transaction history for all users, all assets."""
    query = """
    SELECT
        t.transaction_id,
        t.user_id,
        u.username,
        t.account_id,
        a.account_name,
        t.investment_id,
        i.investment_name,
        t.asset_id,
        ast.name AS asset_name,
        t.transaction_type,
        t.amount,
        t.quantity,
        t.unit_price_at_transaction,
        t.description,
        t.transaction_date
    FROM transactions t
    JOIN users u ON t.user_id = u.user_id
    LEFT JOIN accounts a ON t.account_id = a.account_id
    LEFT JOIN investments i ON t.investment_id = i.investment_id
    LEFT JOIN assets ast ON t.asset_id = ast.asset_id
    ORDER BY t.transaction_date DESC, u.username
    """
    return execute_query(query, fetch=True)


def delete_transaction(transaction_id):
    """Deletes a transaction by its ID."""
    query = "DELETE FROM transactions WHERE transaction_id = %s"
    return execute_query(query, (transaction_id,))

# --- Dashboard Data Retrieval ---
def get_portfolio_summary(user_id):
    """Retrieves a summary of the user's portfolio, dynamically calculating investment value."""
    summary = {}

    # Total Account Balance
    account_balances = execute_query(
        "SELECT SUM(current_balance) AS total_balance FROM accounts WHERE user_id = %s",
        (user_id,), fetch=True
    )
    summary['total_account_balance'] = account_balances[0]['total_balance'] if account_balances and account_balances[0]['total_balance'] is not None else Decimal('0.00')

    # Total Investment Value (dynamically calculated)
    # Summing (quantity * current_unit_price) for all investments of the user
    investment_values = execute_query(
        """
        SELECT SUM(i.quantity * a.unit_price) AS total_investment_value
        FROM investments i
        JOIN assets a ON i.asset_id = a.asset_id
        WHERE i.user_id = %s
        """,
        (user_id,), fetch=True
    )
    summary['total_investment_value'] = investment_values[0]['total_investment_value'] if investment_values and investment_values[0]['total_investment_value'] is not None else Decimal('0.00')

    summary['total_portfolio_value'] = summary['total_account_balance'] + summary['total_investment_value']

    return summary

def get_account_balances_df(user_id=None):
    """Retrieves account balances as a pandas DataFrame.
    If user_id is None, retrieves for all users (for admin)."""
    if user_id:
        accounts = get_accounts_by_user(user_id)
    else:
        accounts = get_all_accounts() # New function for admin view
    if accounts:
        return pd.DataFrame(accounts)
    return pd.DataFrame()

def get_investments_df(user_id=None):
    """Retrieves investments as a pandas DataFrame.
    If user_id is None, retrieves for all users (for admin)."""
    if user_id:
        investments = get_investments_by_user(user_id)
    else:
        investments = get_all_investments_detailed() # New function for admin view
    if investments:
        return pd.DataFrame(investments)
    return pd.DataFrame()

def get_transactions_df(user_id=None):
    """Retrieves transactions as a pandas DataFrame.
    If user_id is None, retrieves for all users (for admin)."""
    if user_id:
        transactions = get_transactions_by_user(user_id)
    else:
        transactions = get_all_transactions_detailed() # New function for admin view
    if transactions:
        return pd.DataFrame(transactions)
    return pd.DataFrame()

def get_portfolios_df(user_id=None):
    """Retrieves portfolios as a pandas DataFrame.
    If user_id is None, retrieves for all users (for admin)."""
    if user_id:
        portfolios = get_portfolios_by_user(user_id)
    else:
        # For admin, you might want a view of all portfolios or portfolios by user
        # For now, let's keep it user-specific for the main dashboard,
        # and admin will view investments directly.
        # If a full 'all portfolios' view is needed, implement get_all_portfolios()
        portfolios = get_portfolios_by_user(user_id) # Default to user-specific for now
    if portfolios:
        return pd.DataFrame(portfolios)
    return pd.DataFrame()

def get_asset_types_df():
    """Retrieves asset types as a pandas DataFrame."""
    asset_types = get_asset_types()
    if asset_types:
        return pd.DataFrame(asset_types)
    return pd.DataFrame()

def get_assets_df():
    """Retrieves all assets as a pandas DataFrame."""
    assets = get_all_assets()
    if assets:
        return pd.DataFrame(assets)
    return pd.DataFrame()

if __name__ == '__main__':
    # --- Example Usage (for testing the database_manager) ---
    print("--- Testing Database Manager ---")

    # 1. Test Connection
    conn = create_connection()
    if conn:
        conn.close()

    # 2. Add a new user (if not exists)
    try:
        if not get_user_by_username('test_user_new'):
            user_id = add_user('test_user_new', 'secure_password123', 'test_new@example.com', 'user')
            print(f"Added new user with ID: {user_id}")
        else:
            print("User 'test_user_new' already exists.")
            user_data = get_user_by_username('test_user_new')
            if user_data:
                user_id = user_data[0]['user_id']
            else:
                user_id = None

        if not get_user_by_username('admin_user'):
            admin_id = add_user('admin_user', 'admin_password', 'admin@example.com', 'admin')
            print(f"Added new admin user with ID: {admin_id}")
        else:
            print("Admin user 'admin_user' already exists.")
            admin_data = get_user_by_username('admin_user')
            if admin_data:
                admin_id = admin_data[0]['user_id']
            else:
                admin_id = None

    except Error as e:
        print(f"Error during test user creation: {e}")
        user_id = None
        admin_id = None


    if user_id is None:
        print("Could not get user_id for 'test_user_new'. Exiting test.")
    else:
        # 3. Get user details and role
        user = get_user_by_id(user_id)
        print(f"User details: {user}")
        print(f"User role: {get_user_role(user_id)}")

        if admin_id:
            print(f"Admin role: {get_user_role(admin_id)}")
            print("\nAll Users (Admin View):")
            print(pd.DataFrame(get_all_users()))
            print("\nAll Accounts (Admin View):")
            print(pd.DataFrame(get_all_accounts()))
            print("\nAll Investments (Admin View):")
            print(pd.DataFrame(get_all_investments_detailed()))
            print("\nAll Transactions (Admin View):")
            print(pd.DataFrame(get_all_transactions_detailed()))


        # 4. Add an asset type (if not exists)
        asset_types = get_asset_types()
        stock_type_id = None
        if not any(at['type_name'] == 'Stock' for at in asset_types):
            try:
                stock_type_id = add_asset_type('Stock', 'Publicly traded company shares')
                print(f"Added new asset type 'Stock' with ID: {stock_type_id}")
            except Error as e:
                print(f"Error adding asset type: {e}")
                stock_type_id = None
        else:
            print("Asset type 'Stock' already exists.")
            stock_type_id = [at['asset_type_id'] for at in asset_types if at['type_name'] == 'Stock'][0]

        crypto_type_id = None
        if not any(at['type_name'] == 'Crypto' for at in asset_types):
            try:
                crypto_type_id = add_asset_type('Crypto', 'Cryptocurrency assets')
                print(f"Added new asset type 'Crypto' with ID: {crypto_type_id}")
            except Error as e:
                print(f"Error adding asset type: {e}")
                crypto_type_id = None
        else:
            print("Asset type 'Crypto' already exists.")
            crypto_type_id = [at['asset_type_id'] for at in asset_types if at['type_name'] == 'Crypto'][0]


        # 5. Add assets (if not exists)
        assets = get_all_assets()
        gold_asset_id = None
        bitcoin_asset_id = None

        if not any(a['name'] == 'Gold' for a in assets):
            try:
                gold_asset_id = add_asset('Gold', Decimal('70.00'), 'grams')
                print(f"Added new asset 'Gold' with ID: {gold_asset_id}")
            except Error as e:
                print(f"Error adding asset 'Gold': {e}")
                gold_asset_id = None
        else:
            print("Asset 'Gold' already exists.")
            gold_asset_id = [a['asset_id'] for a in assets if a['name'] == 'Gold'][0]

        if not any(a['name'] == 'Bitcoin' for a in assets):
            try:
                bitcoin_asset_id = add_asset('Bitcoin', Decimal('65000.00'), 'BTC')
                print(f"Added new asset 'Bitcoin' with ID: {bitcoin_asset_id}")
            except Error as e:
                print(f"Error adding asset 'Bitcoin': {e}")
                bitcoin_asset_id = None
        else:
            print("Asset 'Bitcoin' already exists.")
            bitcoin_asset_id = [a['asset_id'] for a in assets if a['name'] == 'Bitcoin'][0]

        print("\nAll Assets:")
        print(get_assets_df())

        # 6. Add a portfolio
        portfolios = get_portfolios_by_user(user_id)
        portfolio_id = None
        if not any(p['portfolio_name'] == 'Test Portfolio' for p in portfolios):
            try:
                portfolio_id = add_portfolio(user_id, 'Test Portfolio', 'A portfolio for testing investments')
                print(f"Added new portfolio with ID: {portfolio_id}")
            except Error as e:
                print(f"Error adding portfolio: {e}")
                portfolio_id = None
        else:
            print("Portfolio 'Test Portfolio' already exists.")
            portfolio_id = [p['portfolio_id'] for p in portfolios if p['portfolio_name'] == 'Test Portfolio'][0]

        # 7. Add an account
        accounts = get_accounts_by_user(user_id)
        account_id = None
        if not any(a['account_name'] == 'Test Savings Account' for a in accounts):
            try:
                account_id = add_account(user_id, 'Test Savings Account', 'Savings', Decimal('1000.00'))
                print(f"Added new account with ID: {account_id}")
            except Error as e:
                print(f"Error adding account: {e}")
                account_id = None
        else:
            print("Account 'Test Savings Account' already exists.")
            account_id = [a['account_id'] for a in accounts if a['account_name'] == 'Test Savings Account'][0]


        # 8. Add an investment (linking to a specific asset)
        investments = get_investments_by_user(user_id)
        gold_investment_id = None
        if portfolio_id is not None and stock_type_id is not None and gold_asset_id is not None:
            if not any(i['investment_name'] == 'My Gold Holdings' for i in investments):
                try:
                    gold_investment_id = add_investment(user_id, portfolio_id, stock_type_id, gold_asset_id, 'My Gold Holdings', 'GLD', Decimal('700.00'), '2024-01-01', Decimal('10.0'), 'USD', '10 grams of gold')
                    print(f"Added new gold investment with ID: {gold_investment_id}")
                except Error as e:
                    print(f"Error adding gold investment: {e}")
                    gold_investment_id = None
            else:
                print("Investment 'My Gold Holdings' already exists.")
                gold_investment_id = [i['investment_id'] for i in investments if i['investment_name'] == 'My Gold Holdings'][0]
        else:
            print("Cannot add gold investment: Portfolio, Asset Category, or Asset ID is missing.")

        # 9. Get investments (should show dynamically calculated current_value)
        investments = get_investments_by_user(user_id)
        print(f"\nUser's investments (with dynamic current_value): {investments}")
        print("\nInvestments DataFrame (User View):")
        print(get_investments_df(user_id))

        # 10. Update asset price (simulating admin action)
        if gold_asset_id:
            print(f"\nUpdating Gold price from {get_asset_by_id(gold_asset_id)['unit_price']} to 75.00...")
            if update_asset_price(gold_asset_id, Decimal('75.00')):
                print("Gold price updated successfully.")
                print(f"New Gold price: {get_asset_by_id(gold_asset_id)['unit_price']}")
                # Re-fetch investments to see the effect of price change
                investments_after_price_update = get_investments_df(user_id)
                print("\nInvestments DataFrame (User View) AFTER Gold Price Update:")
                print(investments_after_price_update)
            else:
                print("Failed to update Gold price.")

        # 11. Add a transaction (e.g., buying more Gold)
        if account_id is not None and gold_asset_id is not None and gold_investment_id is not None:
            buy_quantity = Decimal('5.0')
            current_gold_price = get_asset_by_id(gold_asset_id)['unit_price']
            total_buy_cost = buy_quantity * current_gold_price
            print(f"\nBuying {buy_quantity} grams of Gold at ${current_gold_price}/gram for total ${total_buy_cost}...")

            # Simulate deducting from account (you'd need to update account balance in app.py)
            # For testing, just add the transaction
            try:
                transaction_id = add_transaction(user_id, account_id=account_id, asset_id=gold_asset_id,
                                                transaction_type='Buy', amount=total_buy_cost,
                                                quantity=buy_quantity, unit_price_at_transaction=current_gold_price,
                                                description=f"Bought {buy_quantity} grams of Gold")
                if transaction_id:
                    print(f"Added new transaction with ID: {transaction_id}")
                    # Update investment quantity after buy (this would be handled in app.py)
                    # For testing, manually update:
                    # current_gold_holdings = execute_query("SELECT quantity FROM investments WHERE investment_id = %s", (gold_investment_id,), fetch=True)[0]['quantity']
                    # update_investment(gold_investment_id, quantity=current_gold_holdings + buy_quantity)
                else:
                    print("Failed to add transaction.")
            except Error as e:
                print(f"Error adding transaction: {e}")
                transaction_id = None
        else:
            print("Cannot add transaction: Account, Asset, or Investment ID is missing.")
            transaction_id = None

        # 12. Get transactions
        transactions = get_transactions_by_user(user_id)
        print(f"\nUser's transactions: {transactions}")
        print("\nTransactions DataFrame (User View):")
        print(get_transactions_df(user_id))


        # 13. Get Portfolio Summary
        portfolio_summary = get_portfolio_summary(user_id)
        print(f"\nPortfolio Summary (with dynamic investment value): {portfolio_summary}")

        # 14. Get DataFrames
        accounts_df = get_account_balances_df(user_id)
        print("\nAccounts DataFrame:")
        print(accounts_df)

        investments_df = get_investments_df(user_id)
        print("\nInvestments DataFrame:")
        print(investments_df)

        transactions_df = get_transactions_df(user_id)
        print("\nTransactions DataFrame:")
        print(transactions_df)

        portfolios_df = get_portfolios_df(user_id)
        print("\nPortfolios DataFrame:")
        print(portfolios_df)

        asset_types_df = get_asset_types_df()
        print("\nAsset Types DataFrame:")
        print(asset_types_df)

        assets_df = get_assets_df()
        print("\nAssets DataFrame:")
        print(assets_df)

        # Clean up (optional, uncomment to delete test data)
        # print("\n--- Cleaning up test data ---\n")
        # if transaction_id: delete_transaction(transaction_id)
        # if gold_investment_id: delete_investment(gold_investment_id)
        # if account_id: delete_account(account_id)
        # if portfolio_id: delete_portfolio(portfolio_id)
        # if gold_asset_id: execute_query("DELETE FROM assets WHERE asset_id = %s", (gold_asset_id,))
        # if bitcoin_asset_id: execute_query("DELETE FROM assets WHERE asset_id = %s", (bitcoin_asset_id,))
        # if stock_type_id: execute_query("DELETE FROM asset_types WHERE asset_type_id = %s", (stock_type_id,))
        # if crypto_type_id: execute_query("DELETE FROM asset_types WHERE asset_type_id = %s", (crypto_type_id,))
        # if user_id: delete_user_and_all_data(user_id) # Use the new comprehensive delete function
        # if admin_id: delete_user_and_all_data(admin_id) # Use the new comprehensive delete function
        # print("Test data cleaned up.")
