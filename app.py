import streamlit as st
import pandas as pd
import database_manager as db
import hashlib # For basic password hashing (for demo purposes)
from mysql.connector import Error
from decimal import Decimal # For precise financial calculations
import plotly.express as px # For visualizations

# --- DIAGNOSTIC LINE ---
st.write("Streamlit app is running!")
# --- END DIAGNOSTIC LINE ---

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Wealth Management System")

# --- Admin Credentials (for demo purposes - in a real app, manage securely) ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password" # This will be hashed and stored in DB

# --- Helper Functions ---
def hash_password(password):
    """Hashes a password using SHA256 for basic security (for demo)."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, user_password):
    """Checks if a given password matches the hashed password."""
    return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

def load_data(user_id, user_role):
    """Loads all necessary data for the dashboard and management sections based on user role."""
    # Initialize all relevant dataframes to empty DataFrames to prevent AttributeError
    st.session_state['accounts_df'] = pd.DataFrame()
    st.session_state['portfolios_df'] = pd.DataFrame()
    st.session_state['asset_types_df'] = pd.DataFrame()
    st.session_state['assets_df'] = pd.DataFrame()
    st.session_state['investments_df'] = pd.DataFrame()
    st.session_state['transactions_df'] = pd.DataFrame()
    st.session_state['portfolio_summary'] = {'total_account_balance': Decimal('0.00'), 'total_investment_value': Decimal('0.00'), 'total_portfolio_value': Decimal('0.00')}
    st.session_state['all_users_df'] = pd.DataFrame()
    st.session_state['all_accounts_df'] = pd.DataFrame()
    st.session_state['all_investments_df'] = pd.DataFrame()
    st.session_state['all_transactions_df'] = pd.DataFrame()


    # Load common data for all roles
    st.session_state['accounts_df'] = db.get_account_balances_df(user_id)
    st.session_state['portfolios_df'] = db.get_portfolios_df(user_id)
    st.session_state['asset_types_df'] = db.get_asset_types_df()
    st.session_state['assets_df'] = db.get_assets_df()

    if user_role == 'admin':
        st.session_state['all_users_df'] = pd.DataFrame(db.get_all_users())
        st.session_state['all_accounts_df'] = db.get_account_balances_df(user_id=None)
        st.session_state['all_investments_df'] = db.get_investments_df(user_id=None)
        st.session_state['all_transactions_df'] = db.get_transactions_df(user_id=None)
    else: # Regular user
        st.session_state['investments_df'] = db.get_investments_df(user_id)
        st.session_state['transactions_df'] = db.get_transactions_df(user_id)
        st.session_state['portfolio_summary'] = db.get_portfolio_summary(user_id)

def refresh_data():
    """Refreshes all data after a modification."""
    if 'user_id' in st.session_state and st.session_state.user_id and \
       'user_role' in st.session_state and st.session_state.user_role:
        load_data(st.session_state.user_id, st.session_state.user_role)
    else:
        st.warning("Please log in to refresh data.")

# --- Authentication Section ---
def show_auth_section():
    st.sidebar.title("Authentication")
    auth_choice = st.sidebar.radio("Choose an option", ["Login", "Register"], key="auth_choice_radio")

    if auth_choice == "Login":
        st.sidebar.subheader("Login")
        username = st.sidebar.text_input("Username", key="login_username_input")
        password = st.sidebar.text_input("Password", type="password", key="login_password_input")
        if st.sidebar.button("Login", key="login_button"):
            user_data = db.get_user_by_username(username)
            if user_data:
                user = user_data[0]
                if check_password(user['password'], password):
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['user_id']
                    st.session_state.username = user['username']
                    st.session_state.user_role = user['role'] # Store user role
                    refresh_data() # Load data on successful login
                    st.sidebar.success(f"Welcome, {st.session_state.username} ({st.session_state.user_role})!")
                    st.rerun()
                else:
                    st.sidebar.error("Incorrect password.")
            else:
                st.sidebar.error("Username not found.")
    else: # Register
        st.sidebar.subheader("Register")
        new_username = st.sidebar.text_input("New Username", key="reg_username_input")
        new_password = st.sidebar.text_input("New Password", type="password", key="reg_password_input")
        new_email = st.sidebar.text_input("Email (Optional)", key="reg_email_input")
        
        # Default role for new registrations is 'user'
        # Admin registration is handled by pre-populating DB or a separate admin-only registration
        
        if st.sidebar.button("Register", key="register_button"):
            if new_username and new_password:
                email_to_db = new_email if new_email.strip() != '' else None
                hashed_pass = hash_password(new_password)
                try:
                    user_id = db.add_user(new_username, hashed_pass, email_to_db, role='user') # Default role 'user'
                    if user_id:
                        st.sidebar.success(f"User '{new_username}' registered successfully! Please login.")
                    else:
                        st.sidebar.error("Error registering user. Please try again with different details.")
                except Error as e:
                    if e.errno == 1062:
                        if "username" in str(e).lower():
                            st.sidebar.error("Registration failed: Username already exists. Please choose a different one.")
                        elif "email" in str(e).lower():
                            st.sidebar.error("Registration failed: Email already registered. Please use a different email.")
                        else:
                            st.sidebar.error(f"Registration failed: Duplicate entry error. Details: {e}")
                    else:
                        st.sidebar.error(f"A database error occurred during registration: {e}")
            else:
                st.warning("Username and Password are required.")

# --- Dashboard Section (User) ---
def show_dashboard():
    st.title(f"📊 Dashboard for {st.session_state.username}")

    summary = st.session_state.portfolio_summary

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Account Balance", f"${summary['total_account_balance']:.2f}")
    with col2:
        st.metric("Total Investment Value", f"${summary['total_investment_value']:.2f}")
    with col3:
        st.metric("Total Portfolio Value", f"${summary['total_portfolio_value']:.2f}")

    st.subheader("Your Portfolios")
    if not st.session_state.portfolios_df.empty:
        st.dataframe(st.session_state.portfolios_df[['portfolio_name', 'description', 'creation_date']], use_container_width=True)
    else:
        st.info("No portfolios added yet. Go to 'Manage Portfolios' to add one.")

    st.subheader("Account Balances")
    if not st.session_state.accounts_df.empty:
        st.dataframe(st.session_state.accounts_df[['account_name', 'account_type', 'current_balance', 'currency']], use_container_width=True)
    else:
        st.info("No accounts added yet. Go to 'Manage Accounts' to add one.")

    st.subheader("Your Investments Overview")
    if not st.session_state.investments_df.empty:
        # Display dynamically calculated current_value
        st.dataframe(st.session_state.investments_df[['investment_name', 'symbol', 'asset_name', 'asset_category_name', 'quantity', 'current_unit_price', 'current_value']], use_container_width=True)
    else:
        st.info("No investments added yet. Go to 'Manage Investments' or 'Buy Assets' to add one.")

    # Visualizations for User Dashboard
    st.subheader("Investment & Transaction Insights")
    vis_col1, vis_col2 = st.columns(2)

    with vis_col1:
        st.markdown("#### Investment Allocation by Category")
        if not st.session_state.investments_df.empty:
            # Ensure 'current_value' is numeric for summing
            st.session_state.investments_df['current_value'] = pd.to_numeric(st.session_state.investments_df['current_value'], errors='coerce')
            investment_by_category = st.session_state.investments_df.groupby('asset_category_name')['current_value'].sum().reset_index()
            # Filter out categories with zero or NaN values if any after conversion
            investment_by_category = investment_by_category[investment_by_category['current_value'].notna() & (investment_by_category['current_value'] > 0)]

            if not investment_by_category.empty:
                fig_pie = px.pie(
                    investment_by_category,
                    values='current_value',
                    names='asset_category_name',
                    title='Your Investment Allocation by Category',
                    hole=0.3 # Creates a donut chart
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No investments with a value to display in the pie chart yet.")
        else:
            st.info("No investments to display in the pie chart yet.")

    with vis_col2:
        st.markdown("#### Transactions Over Time")
        if not st.session_state.transactions_df.empty:
            # Ensure 'amount' is numeric and 'transaction_date' is datetime
            transactions_df_copy = st.session_state.transactions_df.copy()
            transactions_df_copy['amount'] = pd.to_numeric(transactions_df_copy['amount'], errors='coerce')
            transactions_df_copy['transaction_date'] = pd.to_datetime(transactions_df_copy['transaction_date'])

            # Filter out rows with NaN amounts or invalid dates
            transactions_df_copy = transactions_df_copy.dropna(subset=['amount', 'transaction_date'])
            transactions_df_copy = transactions_df_copy[transactions_df_copy['amount'] > 0]

            if not transactions_df_copy.empty:
                # Sort by date for proper time series visualization
                transactions_df_copy = transactions_df_copy.sort_values(by='transaction_date')

                fig_line = px.line(
                    transactions_df_copy,
                    x='transaction_date',
                    y='amount',
                    color='transaction_type', # Differentiate lines by transaction type
                    title='Transactions Amount Over Time',
                    labels={'transaction_date': 'Date', 'amount': 'Amount ($)', 'transaction_type': 'Transaction Type'}
                )
                fig_line.update_xaxes(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(count=1, label="YTD", step="year", stepmode="todate"),
                            dict(count=1, label="1y", step="year", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(visible=True),
                    type="date"
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No transactions with valid amounts and dates to display in the chart yet.")
        else:
            st.info("No transactions to display in the chart yet.")


    st.subheader("Recent Transactions")
    if not st.session_state.transactions_df.empty:
        st.dataframe(st.session_state.transactions_df[['transaction_date', 'transaction_type', 'amount', 'quantity', 'asset_name', 'account_name', 'description']].head(10), use_container_width=True)
    else:
        st.info("No transactions recorded yet. Add one in 'Manage Transactions' or 'Buy Assets'.")

# --- Admin Dashboard Section ---
def show_admin_dashboard():
    st.title("👑 Admin Dashboard")

    st.subheader("All Registered Users")
    if not st.session_state.all_users_df.empty:
        st.dataframe(st.session_state.all_users_df, use_container_width=True)
    else:
        st.info("No users registered yet.")

    st.subheader("All Account Balances")
    if not st.session_state.all_accounts_df.empty:
        st.dataframe(st.session_state.all_accounts_df, use_container_width=True)
    else:
        st.info("No accounts found.")

    st.subheader("All Investments (User Portfolios)")
    if not st.session_state.all_investments_df.empty:
        st.dataframe(st.session_state.all_investments_df[['username', 'portfolio_name', 'investment_name', 'asset_name', 'quantity', 'current_unit_price', 'current_value', 'currency']], use_container_width=True)
    else:
        st.info("No investments found across all users.")

    st.subheader("Full Transaction History")
    if not st.session_state.all_transactions_df.empty:
        st.dataframe(st.session_state.all_transactions_df[['transaction_date', 'username', 'transaction_type', 'amount', 'quantity', 'asset_name', 'account_name', 'description']], use_container_width=True)
    else:
        st.info("No transactions recorded yet.")

    st.subheader("Manage Asset Prices")
    if not st.session_state.assets_df.empty:
        current_assets_df = st.session_state.assets_df
        st.dataframe(current_assets_df, use_container_width=True)

        asset_names = current_assets_df['name'].tolist()
        selected_asset_name = st.selectbox("Select Asset to Update Price", asset_names, key="admin_asset_price_select")

        if selected_asset_name:
            selected_asset = current_assets_df[current_assets_df['name'] == selected_asset_name].iloc[0]
            asset_id_to_update = int(selected_asset['asset_id'])
            current_price = float(selected_asset['unit_price'])

            new_price = st.number_input(
                f"New Unit Price for {selected_asset_name} ({selected_asset['unit_type']})",
                value=current_price,
                min_value=0.01, # Prices should be positive
                format="%.4f",
                key="admin_new_asset_price_input"
            )

            if st.button(f"Update Price for {selected_asset_name}", key="admin_update_asset_price_button"):
                if new_price <= 0:
                    st.error("Asset price must be a positive value.")
                else:
                    try:
                        if db.update_asset_price(asset_id_to_update, Decimal(str(new_price))):
                            st.success(f"Price of '{selected_asset_name}' updated to ${new_price:.4f}!")
                            refresh_data() # Refresh all data to reflect new values
                            st.rerun() # Force rerun to update all displayed values
                        else:
                            st.error("Failed to update asset price. Database operation failed.")
                    except Error as e:
                        st.error(f"Database error updating price: {e}")
    else:
        st.info("No pre-defined assets found. Add some to the 'assets' table in your database.")

    st.subheader("Delete User")
    if not st.session_state.all_users_df.empty:
        # Filter out the current admin user from the deletion list
        users_to_delete_df = st.session_state.all_users_df[
            (st.session_state.all_users_df['role'] != 'admin') |
            (st.session_state.all_users_df['user_id'] != st.session_state.user_id)
        ]
        
        if not users_to_delete_df.empty:
            user_display_names = [f"{row['username']} (ID: {row['user_id']})" for index, row in users_to_delete_df.iterrows()]
            selected_user_display = st.selectbox("Select User to Delete", user_display_names, key="admin_delete_user_select")

            if selected_user_display:
                # Extract user_id from the display string
                selected_user_id_str = selected_user_display.split('(ID: ')[1][:-1]
                user_id_to_delete = int(selected_user_id_str)
                selected_username = selected_user_display.split(' (ID:')[0]

                st.warning(f"WARNING: Deleting user '{selected_username}' will permanently remove ALL their associated data (accounts, portfolios, investments, transactions). This action cannot be undone.")
                confirm_delete = st.checkbox(f"I understand and want to permanently delete user '{selected_username}'", key="confirm_user_delete_checkbox")

                if confirm_delete and st.button(f"Confirm Delete User '{selected_username}'", key="admin_confirm_delete_user_button"):
                    try:
                        if db.delete_user_and_all_data(user_id_to_delete):
                            st.success(f"User '{selected_username}' and all their data successfully deleted!")
                            refresh_data() # Refresh all data for admin dashboard
                            st.rerun()
                        else:
                            st.error(f"Failed to delete user '{selected_username}'. No records were affected.")
                    except Error as e:
                        st.error(f"Database error during user deletion: {e}. Please check database logs for details.")
                    except Exception as e:
                        st.error(f"An unexpected error occurred during user deletion: {e}")
        else:
            st.info("No non-admin users available for deletion.")
    else:
        st.info("No users registered to delete.")


# --- Buy Assets System (User) ---
def buy_assets():
    st.title("🛒 Buy Assets")

    st.subheader("Available Assets")
    if not st.session_state.assets_df.empty:
        st.dataframe(st.session_state.assets_df, use_container_width=True)
    else:
        st.warning("No assets available for purchase. Please contact admin.")
        return

    st.subheader("Your Accounts (for payment)")
    if not st.session_state.accounts_df.empty:
        st.dataframe(st.session_state.accounts_df[['account_name', 'current_balance', 'currency']], use_container_width=True)
    else:
        st.warning("You need at least one account to buy assets. Go to 'Manage Accounts' to add one.")
        return

    with st.form("buy_asset_form", clear_on_submit=True):
        # Select Account for payment
        account_options = ["None"]
        if not st.session_state.accounts_df.empty:
            account_options = ["None"] + st.session_state.accounts_df['account_name'].tolist()

        selected_account_name = st.selectbox("Select Account for Payment", account_options, key="buy_asset_account_select")
        selected_account_id = None
        current_account_balance = Decimal('0.00')
        if selected_account_name != "None":
            selected_account_row = st.session_state.accounts_df[st.session_state.accounts_df['account_name'] == selected_account_name].iloc[0]
            selected_account_id = int(selected_account_row['account_id'])
            current_account_balance = Decimal(str(selected_account_row['current_balance']))
            st.info(f"Selected Account Balance: ${current_account_balance:.2f}")
        else:
            st.warning("Please select an account.")

        # Select Asset to buy
        asset_options = st.session_state.assets_df['name'].tolist()
        selected_asset_name = st.selectbox("Select Asset to Buy", asset_options, key="buy_asset_select")
        selected_asset_id = None
        selected_asset_unit_price = Decimal('0.00')
        selected_asset_unit_type = ""
        if selected_asset_name:
            selected_asset_row = st.session_state.assets_df[st.session_state.assets_df['name'] == selected_asset_name].iloc[0]
            selected_asset_id = int(selected_asset_row['asset_id'])
            selected_asset_unit_price = Decimal(str(selected_asset_row['unit_price']))
            selected_asset_unit_type = selected_asset_row['unit_type']
            st.info(f"Unit Price: ${selected_asset_unit_price:.4f} per {selected_asset_unit_type}")
        else:
            st.warning("Please select an asset.")

        quantity_to_buy = st.number_input(
            f"Quantity to Buy ({selected_asset_unit_type})",
            min_value=1.0, # Minimum quantity to buy
            format="%.4f",
            key="buy_asset_quantity_input"
        )

        # Convert quantity_to_buy to Decimal before multiplication
        total_cost = Decimal(str(quantity_to_buy)) * selected_asset_unit_price
        st.info(f"Calculated Total Cost: ${total_cost:.2f}")

        submitted = st.form_submit_button("Confirm Purchase")

        if submitted:
            if not selected_account_id:
                st.error("Please select an account to make the purchase.")
                return
            if not selected_asset_id:
                st.error("Please select an asset to purchase.")
                return
            if quantity_to_buy <= 0:
                st.error("Quantity to buy must be greater than zero.")
                return
            if total_cost > current_account_balance:
                st.error(f"Insufficient balance! You need ${total_cost:.2f} but only have ${current_account_balance:.2f} in '{selected_account_name}'.")
                return

            try:
                # 1. Deduct total from account
                new_account_balance = current_account_balance - total_cost
                if not db.update_account_balance(selected_account_id, new_account_balance):
                    raise Exception("Failed to update account balance.")

                # 2. Update/Add quantity to user's investment portfolio
                # Check if user already holds this asset in any portfolio
                user_investments = db.get_investments_by_user(st.session_state.user_id)
                existing_investment = next((inv for inv in user_investments if inv['asset_id'] == selected_asset_id), None)

                if existing_investment:
                    # Update existing investment quantity
                    new_quantity = Decimal(str(existing_investment['quantity'])) + Decimal(str(quantity_to_buy))
                    if not db.update_investment(existing_investment['investment_id'], quantity=new_quantity):
                        raise Exception("Failed to update existing investment quantity.")
                    st.success(f"Updated holdings of '{selected_asset_name}' in your portfolio.")
                else:
                    # Add new investment (requires selecting a portfolio and asset_category)
                    st.warning("You don't have this asset in any portfolio yet. Please select a portfolio and asset category for the new investment.")
                    
                    # Provide options to add to an existing portfolio or create a new one
                    portfolio_options = st.session_state.portfolios_df['portfolio_name'].tolist() if not st.session_state.portfolios_df.empty else []
                    new_investment_portfolio_name = st.selectbox("Select Portfolio for New Investment", portfolio_options, key="new_inv_portfolio_select")

                    asset_category_options = st.session_state.asset_types_df['type_name'].tolist() if not st.session_state.asset_types_df.empty else []
                    new_investment_asset_category_name = st.selectbox("Select Asset Category for New Investment", asset_category_options, key="new_inv_asset_category_select")

                    if new_investment_portfolio_name and new_investment_asset_category_name:
                        new_portfolio_id = int(st.session_state.portfolios_df[st.session_state.portfolios_df['portfolio_name'] == new_investment_portfolio_name].iloc[0]['portfolio_id'])
                        new_asset_category_id = int(st.session_state.asset_types_df[st.session_state.asset_types_df['type_name'] == new_investment_asset_category_name].iloc[0]['asset_type_id'])

                        # Use the asset's name as investment name, or prompt for a custom one
                        investment_name_for_new = f"{selected_asset_name} Holdings"
                        symbol_for_new = selected_asset_row['symbol'] if 'symbol' in selected_asset_row else None # Assets table might not have symbol
                        
                        new_investment_id = db.add_investment(
                            st.session_state.user_id,
                            new_portfolio_id,
                            new_asset_category_id,
                            selected_asset_id,
                            investment_name_for_new,
                            symbol_for_new,
                            total_cost, # Initial investment amount is the total cost of this first purchase
                            pd.to_datetime('today').date(), # Purchase date
                            Decimal(str(quantity_to_buy)), # Ensure quantity is Decimal here
                            selected_account_row['currency'],
                            f"Initial purchase of {selected_asset_name}"
                        )
                        if not new_investment_id:
                            raise Exception("Failed to add new investment.")
                        st.success(f"Added '{selected_asset_name}' as a new investment to your portfolio.")
                    else:
                        st.error("Please select a portfolio and asset category to add this new investment.")
                        return # Stop execution if not selected

                # 3. Log transaction
                transaction_description = f"Bought {quantity_to_buy:.4f} {selected_asset_unit_type} of {selected_asset_name}"
                transaction_id = db.add_transaction(
                    st.session_state.user_id,
                    account_id=selected_account_id,
                    asset_id=selected_asset_id,
                    transaction_type='Buy',
                    amount=total_cost,
                    quantity=Decimal(str(quantity_to_buy)), # Ensure quantity is Decimal for transaction log
                    unit_price_at_transaction=selected_asset_unit_price,
                    description=transaction_description
                )
                if not transaction_id:
                    raise Exception("Failed to log transaction.")

                st.success(f"Successfully purchased {quantity_to_buy:.4f} {selected_asset_unit_type} of {selected_asset_name} for ${total_cost:.2f}!")
                refresh_data() # Refresh all data after successful transaction
                st.rerun() # Force rerun to update dashboard and forms
            except Error as e:
                st.error(f"Transaction failed due to a database error: {e}")
            except Exception as e:
                st.error(f"Transaction failed: {e}")


# --- Portfolio Management Section ---
def manage_portfolios():
    st.title("💼 Manage Portfolios")

    st.subheader("Your Portfolios")
    if not st.session_state.portfolios_df.empty:
        st.dataframe(st.session_state.portfolios_df, use_container_width=True)
    else:
        st.info("You don't have any portfolios yet.")

    st.subheader("Add New Portfolio")
    with st.form("add_portfolio_form", clear_on_submit=True):
        portfolio_name = st.text_input("Portfolio Name", placeholder="e.g., My Growth Portfolio, Retirement Fund")
        description = st.text_area("Description (Optional)")
        submitted = st.form_submit_button("Add Portfolio")
        if submitted:
            if portfolio_name:
                try:
                    portfolio_id = db.add_portfolio(st.session_state.user_id, portfolio_name, description)
                    if portfolio_id:
                        st.success(f"Portfolio '{portfolio_name}' added successfully!")
                        refresh_data()
                        st.session_state['last_selected_portfolio_name'] = portfolio_name
                        st.rerun()
                    else:
                        st.error("Failed to add portfolio. This might be due to a database error or no rows affected.")
                except Error as e:
                    if e.errno == 1062:
                        st.error("Failed to add portfolio: A portfolio with this name already exists for you.")
                    else:
                        st.error(f"Failed to add portfolio: Database error - {e}")
            else:
                st.warning("Portfolio Name is required.")

    st.subheader("Update Portfolio")
    if not st.session_state.portfolios_df.empty:
        portfolio_names = st.session_state.portfolios_df['portfolio_name'].tolist()
        default_update_index = 0
        if 'last_selected_portfolio_name' in st.session_state and st.session_state['last_selected_portfolio_name'] in portfolio_names:
            default_update_index = portfolio_names.index(st.session_state['last_selected_portfolio_name'])
        
        portfolio_to_update = st.selectbox(
            "Select Portfolio to Update",
            portfolio_names,
            index=default_update_index,
            key="update_portfolio_select"
        )
        
        if portfolio_to_update:
            selected_portfolio_row = st.session_state.portfolios_df[st.session_state.portfolios_df['portfolio_name'] == portfolio_to_update].iloc[0]
            portfolio_id_to_update = int(selected_portfolio_row['portfolio_id'])
            original_portfolio_name = selected_portfolio_row['portfolio_name']
            original_description = selected_portfolio_row['description'] or ''

            with st.form("update_portfolio_form", clear_on_submit=False):
                new_portfolio_name = st.text_input("New Portfolio Name", value=original_portfolio_name)
                new_description = st.text_area("New Description", value=original_description)
                update_submitted = st.form_submit_button("Update Portfolio")
                if update_submitted:
                    if not new_portfolio_name:
                        st.warning("Portfolio Name cannot be empty.")
                    else:
                        if new_portfolio_name == original_portfolio_name and new_description == original_description:
                            st.info("No changes detected to update.")
                        else:
                            try:
                                if db.update_portfolio(portfolio_id_to_update, new_portfolio_name, new_description):
                                    st.success(f"Portfolio '{new_portfolio_name}' updated successfully!")
                                    refresh_data()
                                    st.session_state['last_selected_portfolio_name'] = new_portfolio_name
                                    st.rerun()
                                else:
                                    st.error("Failed to update portfolio. No changes were applied or a database error occurred.")
                            except Error as e:
                                if e.errno == 1062:
                                    st.error("Failed to update portfolio: A portfolio with this name already exists for you.")
                                else:
                                    st.error(f"Failed to update portfolio: Database error - {e}")
    else:
        st.info("No portfolios to update.")


    st.subheader("Delete Portfolio")
    if not st.session_state.portfolios_df.empty:
        portfolio_names = st.session_state.portfolios_df['portfolio_name'].tolist()
        default_delete_index = 0
        if 'last_selected_portfolio_name' in st.session_state and st.session_state['last_selected_portfolio_name'] in portfolio_names:
            default_delete_index = portfolio_names.index(st.session_state['last_selected_portfolio_name'])
        
        portfolio_to_delete = st.selectbox(
            "Select Portfolio to Delete",
            portfolio_names,
            index=default_delete_index,
            key="delete_portfolio_select"
        )
        
        if portfolio_to_delete:
            portfolio_id_to_delete = int(st.session_state.portfolios_df[st.session_state.portfolios_df['portfolio_name'] == portfolio_to_delete].iloc[0]['portfolio_id'])
            if st.button(f"Delete '{portfolio_to_delete}'", key="delete_portfolio_button"):
                try:
                    if db.delete_portfolio(portfolio_id_to_delete):
                        st.success(f"Portfolio '{portfolio_to_delete}' deleted successfully!")
                        refresh_data()
                        if 'last_selected_portfolio_name' in st.session_state and st.session_state['last_selected_portfolio_name'] == portfolio_to_delete:
                            del st.session_state['last_selected_portfolio_name']
                        st.rerun()
                    else:
                        st.error("Failed to delete portfolio. No rows were affected or a database error occurred.")
                except Error as e:
                    st.error(f"Failed to delete portfolio: {e}. Ensure no investments are linked to this portfolio, or update them first.")
    else:
        st.info("No portfolios to delete.")

# --- Account Management Section ---
def manage_accounts():
    st.title("💰 Manage Accounts")

    st.subheader("Your Accounts")
    if not st.session_state.accounts_df.empty:
        st.dataframe(st.session_state.accounts_df, use_container_width=True)
    else:
        st.info("You don't have any accounts yet.")

    st.subheader("Add New Account")
    with st.form("add_account_form", clear_on_submit=True):
        account_name = st.text_input("Account Name", placeholder="e.g., My Savings, Brokerage A")
        account_type = st.selectbox("Account Type", ["Savings", "Checking", "Brokerage", "Retirement", "Credit Card", "Other"])
        initial_balance = st.number_input("Initial Balance", value=0.00, format="%.2f")
        currency = st.text_input("Currency", value="USD", max_chars=10)
        submitted = st.form_submit_button("Add Account")
        if submitted:
            if account_name and account_type:
                try:
                    account_id = db.add_account(st.session_state.user_id, account_name, account_type, initial_balance, currency)
                    if account_id:
                        st.success(f"Account '{account_name}' added successfully!")
                        refresh_data()
                        st.rerun()
                    else:
                        st.error("Failed to add account. No rows were affected or a database error occurred.")
                except Error as e:
                    if e.errno == 1062:
                        st.error("Failed to add account: An account with this name already exists for you.")
                    else:
                        st.error(f"Failed to add account: Database error - {e}")
            else:
                st.warning("Account Name and Type are required.")

    st.subheader("Update Account Balance")
    if not st.session_state.accounts_df.empty:
        account_to_update = st.selectbox(
            "Select Account to Update Balance",
            st.session_state.accounts_df['account_name'].tolist(),
            key="update_account_select"
        )
        if account_to_update:
            selected_account_row = st.session_state.accounts_df[st.session_state.accounts_df['account_name'] == account_to_update].iloc[0]
            account_id = selected_account_row['account_id']

            new_balance = st.number_input(
                f"New Balance for {account_to_update} (Current: ${selected_account_row['current_balance']:.2f})",
                value=float(selected_account_row['current_balance']),
                format="%.2f",
                key="new_balance_input"
            )
            if st.button("Update Balance", key="update_balance_button"):
                try:
                    if db.update_account_balance(int(account_id), new_balance):
                        st.success(f"Balance for '{account_to_update}' updated to ${new_balance:.2f}!")
                        refresh_data()
                        st.rerun()
                    else:
                        st.error("Failed to update account balance. No rows were affected or a database error occurred.")
                except Error as e:
                    st.error(f"Failed to update account balance: Database error - {e}")
    else:
        st.info("No accounts to update.")


    st.subheader("Delete Account")
    if not st.session_state.accounts_df.empty:
        account_to_delete = st.selectbox(
            "Select Account to Delete",
            st.session_state.accounts_df['account_name'].tolist(),
            key="delete_account_select"
        )
        if account_to_delete:
            account_id_to_delete = int(st.session_state.accounts_df[st.session_state.accounts_df['account_name'] == account_to_delete].iloc[0]['account_id'])
            if st.button(f"Delete '{account_to_delete}'", key="delete_account_button"):
                try:
                    if db.delete_account(account_id_to_delete):
                        st.success(f"Account '{account_to_delete}' deleted successfully!")
                        refresh_data()
                        st.rerun()
                    else:
                        st.error("Failed to delete account. No rows were affected or a database error occurred.")
                except Error as e:
                    st.error(f"Failed to delete account: {e}. Ensure no transactions or investments are linked to this account.")
    else:
        st.info("No accounts to delete.")

# --- Investment Management (User/Admin) ---
def manage_investments():
    st.title("📈 Manage Investments")

    # Determine which DataFrame to use based on role
    if st.session_state.user_role == 'admin':
        display_df = st.session_state.all_investments_df
        st.subheader("All Investments Across Users")
        if not display_df.empty:
            st.dataframe(display_df[['username', 'portfolio_name', 'investment_name', 'symbol', 'asset_name', 'asset_category_name', 'quantity', 'current_unit_price', 'current_value', 'currency']], use_container_width=True)
        else:
            st.info("No investments found across all users.")
        # Admin does not have direct forms to add/update/delete individual user investments here.
        # This page is primarily for viewing all investments.
        # If admin needs to modify, it would be a more complex UI (e.g., select user, then investment).
        st.info("Admin can view all investments here. To manage specific asset prices, go to 'Admin Dashboard'.")

    else: # Regular user
        display_df = st.session_state.investments_df
        st.subheader("Your Investments")
        if not display_df.empty:
            st.dataframe(display_df[['investment_name', 'symbol', 'asset_name', 'asset_category_name', 'quantity', 'current_unit_price', 'current_value', 'currency']], use_container_width=True)
        else:
            st.info("You don't have any investments yet. Use 'Buy Assets' to add one.")

        st.subheader("Add New Investment (Manually)")
        st.info("It's recommended to use the 'Buy Assets' feature for adding new assets. This section is for manually adding or adjusting existing investment records not tied to a direct purchase transaction.")
        with st.form("add_investment_form", clear_on_submit=True):
            investment_name = st.text_input("Investment Name", placeholder="e.g., Apple Stock, My House, Bitcoin")
            symbol = st.text_input("Symbol (Optional, e.g., AAPL, BTC)")

            # Select Portfolio
            portfolio_options = st.session_state.portfolios_df['portfolio_name'].tolist() if not st.session_state.portfolios_df.empty else []
            selected_portfolio_name = st.selectbox("Select Portfolio", portfolio_options, key="add_investment_portfolio_select")
            portfolio_id = None
            if selected_portfolio_name:
                portfolio_id = int(st.session_state.portfolios_df[st.session_state.portfolios_df['portfolio_name'] == selected_portfolio_name].iloc[0]['portfolio_id'])
            else:
                st.warning("Please create a portfolio first in 'Manage Portfolios' to add investments.")

            # Select Asset Category
            asset_type_options = st.session_state.asset_types_df['type_name'].tolist() if not st.session_state.asset_types_df.empty else []
            selected_asset_type_name = st.selectbox("Select Asset Category", asset_type_options, key="add_investment_asset_type_select")
            asset_category_id = None
            if selected_asset_type_name:
                asset_category_id = int(st.session_state.asset_types_df[st.session_state.asset_types_df['type_name'] == selected_asset_type_name].iloc[0]['asset_type_id'])
            else:
                st.warning("No asset categories found. Please ensure asset types are in the database.")

            # Select Specific Asset
            asset_options = st.session_state.assets_df['name'].tolist() if not st.session_state.assets_df.empty else []
            selected_asset_name = st.selectbox("Select Specific Asset (e.g., Gold, Bitcoin)", asset_options, key="add_investment_asset_select")
            asset_id = None
            if selected_asset_name:
                asset_id = int(st.session_state.assets_df[st.session_state.assets_df['name'] == selected_asset_name].iloc[0]['asset_id'])
            else:
                st.warning("No specific assets found. Please contact admin to add assets.")


            initial_investment_amount = st.number_input("Initial Investment Amount", value=0.00, format="%.2f")
            purchase_date = st.date_input("Purchase Date")
            quantity = st.number_input("Quantity (e.g., shares, units)", value=0.00, format="%.4f")
            currency = st.text_input("Currency", value="USD", max_chars=10)
            notes = st.text_area("Notes (Optional)")

            submitted = st.form_submit_button("Add Investment")
            if submitted:
                if investment_name and portfolio_id is not None and asset_category_id is not None and asset_id is not None:
                    try:
                        investment_id = db.add_investment(st.session_state.user_id, portfolio_id, asset_category_id, asset_id, investment_name, symbol, initial_investment_amount, purchase_date, quantity, currency, notes)
                        if investment_id:
                            st.success(f"Investment '{investment_name}' added successfully!")
                            refresh_data()
                            st.rerun()
                        else:
                            st.error("Failed to add investment. No rows were affected or a database error occurred.")
                    except Error as e:
                        if e.errno == 1062:
                            st.error("Failed to add investment: An investment with this name/symbol already exists for you.")
                        else:
                            st.error(f"Failed to add investment: Database error - {e}")
                else:
                    st.warning("Investment Name, Portfolio, Asset Category, and Specific Asset are required.")
                    if portfolio_id is None:
                        st.error("Please select a valid Portfolio.")
                    if asset_category_id is None:
                        st.error("Please select a valid Asset Category.")
                    if asset_id is None:
                        st.error("Please select a valid Specific Asset.")


        st.subheader("Update Investment")
        if not display_df.empty: # Use display_df for consistency
            investment_to_update_name = st.selectbox(
                "Select Investment to Update",
                display_df['investment_name'].tolist(),
                key="update_investment_select"
            )
            if investment_to_update_name:
                selected_investment_row = display_df[display_df['investment_name'] == investment_to_update_name].iloc[0]
                investment_id = int(selected_investment_row['investment_id'])

                with st.form("update_investment_form", clear_on_submit=False):
                    new_investment_name = st.text_input("Investment Name", value=selected_investment_row['investment_name'])
                    new_symbol = st.text_input("Symbol", value=selected_investment_row['symbol'] or '')

                    # Select Portfolio for update
                    portfolio_options = st.session_state.portfolios_df['portfolio_name'].tolist() if not st.session_state.portfolios_df.empty else []
                    current_portfolio_name = selected_investment_row['portfolio_name']
                    default_portfolio_index = portfolio_options.index(current_portfolio_name) if current_portfolio_name in portfolio_options else 0
                    new_selected_portfolio_name = st.selectbox("Select Portfolio", portfolio_options, index=default_portfolio_index, key="update_investment_portfolio_select")
                    new_portfolio_id = None
                    if new_selected_portfolio_name:
                        new_portfolio_id = int(st.session_state.portfolios_df[st.session_state.portfolios_df['portfolio_name'] == new_selected_portfolio_name].iloc[0]['portfolio_id'])


                    # Select Asset Category for update
                    asset_type_options = st.session_state.asset_types_df['type_name'].tolist() if not st.session_state.asset_types_df.empty else []
                    current_asset_category_name = selected_investment_row['asset_category_name']
                    default_asset_type_index = asset_type_options.index(current_asset_category_name) if current_asset_category_name in asset_type_options else 0
                    new_selected_asset_category_name = st.selectbox("Select Asset Category", asset_type_options, index=default_asset_type_index, key="update_investment_asset_type_select")
                    new_asset_category_id = None
                    if new_selected_asset_category_name:
                        new_asset_category_id = int(st.session_state.asset_types_df[st.session_state.asset_types_df['type_name'] == new_selected_asset_category_name].iloc[0]['asset_type_id'])

                    # Select Specific Asset for update
                    asset_options = st.session_state.assets_df['name'].tolist() if not st.session_state.assets_df.empty else []
                    current_asset_name = selected_investment_row['asset_name']
                    default_asset_index = asset_options.index(current_asset_name) if current_asset_name in asset_options else 0
                    new_selected_asset_name = st.selectbox("Select Specific Asset", asset_options, index=default_asset_index, key="update_investment_specific_asset_select")
                    new_asset_id = None
                    if new_selected_asset_name:
                        new_asset_id = int(st.session_state.assets_df[st.session_state.assets_df['name'] == new_selected_asset_name].iloc[0]['asset_id'])


                    new_initial_investment_amount = st.number_input("Initial Investment Amount", value=float(selected_investment_row['initial_investment_amount'] or 0.00), format="%.2f")
                    new_purchase_date = st.date_input("Purchase Date", value=selected_investment_row['purchase_date'])
                    new_quantity = st.number_input("Quantity", value=float(selected_investment_row['quantity']), format="%.4f")
                    new_currency = st.text_input("Currency", value=selected_investment_row['currency'], max_chars=10)
                    new_notes = st.text_area("Notes", value=selected_investment_row['notes'])

                    update_submitted = st.form_submit_button("Update Investment")
                    if update_submitted:
                        if new_investment_name and new_portfolio_id is not None and new_asset_category_id is not None and new_asset_id is not None:
                            try:
                                if db.update_investment(
                                    investment_id,
                                    new_investment_name,
                                    new_symbol,
                                    new_initial_investment_amount,
                                    new_purchase_date,
                                    new_quantity,
                                    new_currency,
                                    new_notes,
                                    new_portfolio_id,
                                    new_asset_category_id,
                                    new_asset_id
                                ):
                                    st.success(f"Investment '{new_investment_name}' updated successfully!")
                                    refresh_data()
                                    st.rerun()
                                else:
                                    st.error("Failed to update investment. No rows were affected or a database error occurred.")
                            except Error as e:
                                if e.errno == 1062:
                                    st.error("Failed to update investment: An investment with this name/symbol already exists for you.")
                                else:
                                    st.error(f"Failed to update investment: Database error - {e}")
                        else:
                            st.warning("Investment Name, Portfolio, Asset Category, and Specific Asset are required for update.")
        else:
            st.info("No investments to update.")

        st.subheader("Delete Investment")
        if not display_df.empty: # Use display_df for consistency
            investment_to_delete_name = st.selectbox(
                "Select Investment to Delete",
                display_df['investment_name'].tolist(),
                key="delete_investment_select"
            )
            if investment_to_delete_name:
                investment_id_to_delete = int(display_df[display_df['investment_name'] == investment_to_delete_name].iloc[0]['investment_id'])
                if st.button(f"Delete '{investment_to_delete_name}'", key="delete_investment_button"):
                    try:
                        if db.delete_investment(investment_id_to_delete):
                            st.success(f"Investment '{investment_to_delete_name}' deleted successfully!")
                            refresh_data()
                            st.rerun()
                        else:
                            st.error("Failed to delete investment. No rows were affected or a database error occurred.")
                    except Error as e:
                        st.error(f"Failed to delete investment: {e}. Ensure no transactions are linked to this investment.")
        else:
            st.info("No investments to delete.")

# --- Transaction Management Section ---
def manage_transactions():
    st.title("💸 Manage Transactions")

    # Determine which DataFrame to use based on role
    if st.session_state.user_role == 'admin':
        display_df = st.session_state.all_transactions_df
        st.subheader("All Transactions Across Users")
        if not display_df.empty:
            st.dataframe(display_df[['transaction_date', 'username', 'transaction_type', 'amount', 'quantity', 'asset_name', 'account_name', 'description']], use_container_width=True)
        else:
            st.info("No transactions recorded across all users.")
        # Admin does not have direct forms to add/update/delete individual user transactions here.
        # This page is primarily for viewing all transactions.
    else: # Regular user
        display_df = st.session_state.transactions_df
        st.subheader("Your Transactions")
        if not display_df.empty:
            # Display asset_name and quantity for asset-related transactions
            st.dataframe(display_df[['transaction_date', 'transaction_type', 'amount', 'quantity', 'asset_name', 'account_name', 'description']], use_container_width=True)
        else:
            st.info("You don't have any transactions yet. Please add an account or make a purchase to see transactions.")

        st.subheader("Add New Transaction (Manual Entry)")
        st.info("This section is for manual transaction entries (e.g., deposits, withdrawals, or other specific transactions not covered by 'Buy Assets').")
        with st.form("add_transaction_form", clear_on_submit=True):
            transaction_type = st.selectbox("Transaction Type", ["Deposit", "Withdrawal", "Buy", "Sell", "Dividend", "Interest", "Fee", "Transfer", "Other"])
            amount = st.number_input("Amount", value=0.00, format="%.2f")
            description = st.text_area("Description (Optional)")

            # Safely get account options
            account_options = ["None"]
            if not st.session_state.accounts_df.empty:
                account_options = ["None"] + st.session_state.accounts_df['account_name'].tolist()
            
            selected_account_name = st.selectbox("Link to Account", account_options, key="add_trans_account_select")
            account_id = None
            if selected_account_name != "None":
                account_id = int(st.session_state.accounts_df[st.session_state.accounts_df['account_name'] == selected_account_name].iloc[0]['account_id'])

            # Optional: Link to an existing investment and/or asset for manual 'Buy'/'Sell' type transactions
            investment_options = ["None"]
            if not st.session_state.investments_df.empty:
                investment_options = ["None"] + st.session_state.investments_df['investment_name'].tolist()

            selected_investment_name = st.selectbox("Link to Existing Investment (Optional)", investment_options, key="add_trans_investment_select")
            investment_id = None
            if selected_investment_name != "None":
                investment_id = int(st.session_state.investments_df[st.session_state.investments_df['investment_name'] == selected_investment_name].iloc[0]['investment_id'])
            
            asset_options = ["None"]
            if not st.session_state.assets_df.empty:
                asset_options = ["None"] + st.session_state.assets_df['name'].tolist()

            selected_asset_name = st.selectbox("Link to Specific Asset (Optional)", asset_options, key="add_trans_asset_select")
            asset_id = None
            if selected_asset_name != "None":
                asset_id = int(st.session_state.assets_df[st.session_state.assets_df['name'] == selected_asset_name].iloc[0]['asset_id'])

            # Quantity and Unit Price at Transaction for manual Buy/Sell
            manual_quantity = st.number_input("Quantity (for Buy/Sell transactions)", value=0.00, format="%.4f", key="manual_trans_quantity")
            manual_unit_price = st.number_input("Unit Price at Transaction (for Buy/Sell)", value=0.00, format="%.4f", key="manual_trans_unit_price")

            submitted = st.form_submit_button("Add Transaction")
            if submitted:
                if transaction_type and amount is not None:
                    try:
                        transaction_id = db.add_transaction(
                            st.session_state.user_id,
                            account_id=account_id,
                            investment_id=investment_id,
                            asset_id=asset_id, # Pass asset_id
                            transaction_type=transaction_type,
                            amount=amount,
                            quantity=manual_quantity, # Pass quantity
                            unit_price_at_transaction=manual_unit_price, # Pass unit price
                            description=description
                        )
                        if transaction_id:
                            st.success(f"Transaction added successfully!")
                            refresh_data()
                            st.rerun()
                        else:
                            st.error("Failed to add transaction. No rows were affected or a database error occurred.")
                    except Error as e:
                        st.error(f"Failed to add transaction: Database error - {e}")
                else:
                    st.warning("Transaction Type and Amount are required.")

        st.subheader("Delete Transaction")
        if not display_df.empty: # Use display_df for consistency
            transaction_display_options_with_ids = [
                (f"{row['transaction_date'].strftime('%Y-%m-%d %H:%M')} - {row['transaction_type']} {row['amount']:.2f} ({row['description'] or 'No description'})", row['transaction_id'])
                for index, row in display_df.iterrows()
            ]
            transaction_display_strings = [item[0] for item in transaction_display_options_with_ids]

            selected_transaction_display = st.selectbox(
                "Select Transaction to Delete",
                transaction_display_strings,
                key="delete_transaction_select"
            )
            if selected_transaction_display:
                transaction_id_to_delete = next((item[1] for item in transaction_display_options_with_ids if item[0] == selected_transaction_display), None)

                if transaction_id_to_delete is not None:
                    if st.button(f"Delete Selected Transaction", key="delete_transaction_button"):
                        try:
                            if db.delete_transaction(int(transaction_id_to_delete)):
                                st.success(f"Transaction deleted successfully!")
                                refresh_data()
                                st.rerun()
                            else:
                                st.error("Failed to delete transaction. No rows were affected or a database error occurred.")
                        except Error as e:
                            st.error(f"Failed to delete transaction: Database error - {e}")
                else:
                    st.error("Selected transaction not found for deletion.")
        else:
            st.info("No transactions to delete.")


# --- Main Application Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None # Initialize user role

# Check and add admin user on first run if not exists
admin_user_data = db.get_user_by_username(ADMIN_USERNAME)
if not admin_user_data:
    try:
        db.add_user(ADMIN_USERNAME, hash_password(ADMIN_PASSWORD), 'admin@wealth.com', 'admin')
        st.sidebar.success("Admin user created. Please log in as admin.")
    except Exception as e:
        st.sidebar.warning(f"Could not create admin user automatically: {e}")


if not st.session_state.logged_in:
    show_auth_section()
    st.info("Please Login or Register to access the Wealth Management System.")
else:
    st.sidebar.title("Navigation")
    
    # Determine navigation options based on user role
    if st.session_state.user_role == 'admin':
        navigation_options = [
            "Admin Dashboard",
            "Manage Investments", # Admin can view all investments here
            "Manage Transactions", # Admin can view all transactions here
            # Removed "Manage Portfolios" and "Manage Accounts" for admin
        ]
    else: # Regular user
        navigation_options = [
            "Dashboard",
            "Buy Assets",
            "Manage Portfolios",
            "Manage Accounts",
            "Manage Investments",
            "Manage Transactions"
        ]

    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = navigation_options[0] # Default to first option

    # If the current page is not in the new navigation options, reset it to the first option
    if st.session_state['current_page'] not in navigation_options:
        st.session_state['current_page'] = navigation_options[0]
        st.rerun() # Force a rerun to apply the new page selection

    page = st.sidebar.radio(
        "Go to",
        navigation_options,
        index=navigation_options.index(st.session_state['current_page']),
        key="main_navigation_radio"
    )
    
    if page != st.session_state['current_page']:
        st.session_state['current_page'] = page
        st.rerun()

    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.user_role = None
        # Clear all dataframes from session state to ensure fresh load on next login
        for key in list(st.session_state.keys()):
            if key.endswith('_df') or key == 'portfolio_summary' or key.startswith('last_selected_'):
                st.session_state.pop(key, None)
        # Crucially, pop 'current_page' to ensure it resets for the next login
        st.session_state.pop('current_page', None) 
        st.success("Logged out successfully.")
        st.rerun()

    # Load data initially or refresh if needed based on current user and role
    load_data(st.session_state.user_id, st.session_state.user_role)

    # Route to the correct page based on selection and role
    if st.session_state.user_role == 'admin':
        if page == "Admin Dashboard":
            show_admin_dashboard()
        # Removed "Manage Portfolios" and "Manage Accounts" routing for admin
        elif page == "Manage Investments": # Admin's view of all investments
            manage_investments()
        elif page == "Manage Transactions": # Admin's view of all transactions
            manage_transactions()
    else: # Regular user
        if page == "Dashboard":
            show_dashboard()
        elif page == "Buy Assets":
            buy_assets()
        elif page == "Manage Portfolios":
            manage_portfolios()
        elif page == "Manage Accounts":
            manage_accounts()
        elif page == "Manage Investments":
            manage_investments()
        elif page == "Manage Transactions":
            manage_transactions()

    st.sidebar.markdown("---")
    st.sidebar.info(f"Logged in as: **{st.session_state.username}** (Role: **{st.session_state.user_role}**) (ID: {st.session_state.user_id})")
