import random
import time
from datetime import date, datetime, timedelta
from collections import defaultdict, Counter
from decimal import Decimal
from bank import Client, Bank
from utils import BankAccount, PremiumAccount
from transaction import Transaction, TransactionProcessor, \
    TransactionQueue, TransactionType
from audit import AuditLog, LogLevel, RiskAnalyzer
from report import ReportBuilder


def create_bank_with_clients_and_accounts():
    """
    Creates a Bank instance populated
    with a random number of clients and accounts.

    - Generates between 5 and 10 clients 
        with random birth dates (18 to ~70 years old) and contacts.
    - Creates between 10 and 15 bank accounts linked to these clients.
    - Each account can be a regular 
        BankAccount or a PremiumAccount (30% chance).
    - Balances and overdraft limits are randomly assigned.
    
    Returns:
        dict: A dictionary containing:
            - "bank": the Bank instance
            - "clients": dict mapping client_id to Client objects
            - "accounts": 
                dict mapping account_id to BankAccount or PremiumAccount
    """
    # Creating a bank
    bank = Bank()

    # Supported currencies
    currencies = list(BankAccount.SUPPORTED_CURRENCIES)

    # Clients list
    clients = {}

    # Number of clients
    n_clients = random.randint(5, 10)

    today = date.today()

    # Функция генерации даты рождения >= 18 лет
    def random_birth_date():
        """
        Generates random birth date

        Returns:
            datetime.date: date object
        """
        age_years = random.randint(18, 70)
        # Отнять возраст от сегодняшней даты, плюс рандом день в году
        bd = today.replace(year=today.year - age_years)
        # Date shift for dates variety
        shift_days = random.randint(-365, -1)
        try:
            bd = bd + timedelta(days=shift_days)
        except ValueError:
            # В случае выхода за февраль 29, поправим в простой день
            bd = bd.replace(day=28)
        return bd

    # Функция генерации контактов
    def random_contacts():
        """
        Generates random contact data

        Returns:
            dict:
                - "phone" (str)
                - "email" (str)
        """
        phone = f"+7{random.randint(9000000000, 9999999999)}"
        email = f"user{random.randint(1,1000)}@example.com"
        return {"phone": phone, "email": email}

    # Client generation
    for _ in range(n_clients):
        fio = f"Client_{random.randint(1000,9999)}"
        birth_date = random_birth_date()
        contacts = random_contacts()
        # Adding client to a bank
        client_id = bank.add_client(fio, birth_date, contacts)
        clients[client_id] = bank.clients[client_id]

    # Creating 10-15 accounts
    n_accounts = random.randint(10, 15)
    accounts = {}

    client_ids = list(clients.keys())

    for _ in range(n_accounts):
        # Choosing random client
        client_id = random.choice(client_ids)
        owner_data = {
            "fio": clients[client_id].fio,
            "client_id": client_id
        }
        currency = random.choice(currencies)
        acc_balance = random.randint(0, 1_000_000)
        # Account type distribution: 30% of PremiumAccount
        if random.random() < 0.3:
            overdraft_limit = random.randint(0, 100_000)
            premium_fee = Decimal(
                random.uniform(1.0, 10.0)).quantize(Decimal("0.01")
            )
            account = PremiumAccount(
                owner_data,
                currency,
                overdraft_limit=overdraft_limit,
                premium_fixed_fee=premium_fee,
                acc_balance=acc_balance
            )
        else:
            account = BankAccount(
                owner_data,
                currency,
                acc_balance=acc_balance
            )
        # Opening account in a bank
        account_id = bank.open_account(client_id, account)
        accounts[account_id] = account

    print(bank)

    return {
        "bank": bank,
        "clients": clients,
        "accounts": accounts
    }


def simulate_transactions(bank_dict):
    """
    Simulates random transactions based on the provided bank data.

    Performs the following:
    - Randomly selects 30 to 50 transactions between accounts.
    - Marks about 20% of accounts as "frozen" to simulate error cases.
    - Chooses transaction type (internal or external) with some probability.
    - Allows some transactions to exceed
        the sender's balance to simulate failures.
    - Adds transactions to a processing queue with priority and delay.
    - Processes the transaction queue, logging attempts and outcomes.

    Args:
        bank_dict (dict): A dictionary with bank data

    Returns:
        dict: An extended dictionary including:
            - all original keys and values from bank_dict
            - "transactions": dict of Transaction objects created
            - "txn_queue": TransactionQueue instance used
            - "txn_processor": TransactionProcessor instance used
            - "frozen_accounts": list of accounts marked as frozen
    """
    bank = bank_dict["bank"]
    clients = bank_dict["clients"]
    accounts = bank_dict["accounts"]

    txn_processor = TransactionProcessor()
    txn_queue = TransactionQueue()

    all_accounts = list(accounts.values())
    n_txns = random.randint(30, 50)

    transactions = {}

    # Freeze 20% of the accounts 
    frozen_accounts = random.sample(all_accounts, k=max(1, int(len(all_accounts)*0.2)))
    for acc in frozen_accounts:
        acc.status = "frozen"

    def random_account(exclude_frozen=False):
        if exclude_frozen:
            non_frozen = [acc for acc in all_accounts if acc.status != "frozen"]
            return random.choice(non_frozen) if non_frozen else random.choice(all_accounts)
        else:
            return random.choice(all_accounts)

    for _ in range(n_txns):
        # Random choice of sender and receiver account (same or another user)
        sender = random_account()
        # 10% chance of INTERNAL transaction inside one client
        if random.random() < 0.1:
            # Looking for the same client but different account
            same_client_accounts = [
                acc for acc in all_accounts
                if acc.owner_data["client_id"] == sender.owner_data["client_id"]
                and acc.account_id != sender.account_id]
            if same_client_accounts:
                receiver = random.choice(same_client_accounts)
            else:
                receiver = random_account(exclude_frozen=True)
            txn_type = TransactionType.INTERNAL
        else:
            receiver = random_account(exclude_frozen=True)
            txn_type = TransactionType.EXTERNAL \
                if sender.owner_data["client_id"] != receiver.owner_data["client_id"] \
                    else TransactionType.INTERNAL

        # Value from 10 to 500_000
        amount = round(random.uniform(10, 500_000), 2)

        # 15% chance the amount higher than the balance to cause an error
        if random.random() < 0.15:
            # 15% chance the amount higher than the balance + overdraft + 1000
            min_amount = sender.acc_balance + random.randint(1000, 50000)
            amount = round(min_amount + random.uniform(0, 10000), 2)

        # Creating transaction
        txn = Transaction(
            txn_type=txn_type,
            amount=amount,
            currency=sender.currency,
            sender_account=sender,
            receiver_account=receiver,
            commission=0.0
        )
        transactions[txn.id] = txn

        # Managing the transaction queue (priority by tx type)
        priority = 0 if txn_type == TransactionType.INTERNAL else 1

        # Chance of delay
        delayed = (random.random() < 0.1)

        # Log addition to a queue
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Adding transaction {txn.id[:8]} to queue, "
              f"priority={priority}, delayed={delayed}")
        txn_queue.add(txn, priority=priority, delayed=delayed)

    # Queue processing with demonstrating logs
    while not txn_queue.is_empty():
        txn = txn_queue.pop()
        if txn is None:
            break

        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Processing transaction {txn.id[:8]}")

        success = txn_processor.process(txn)

        if not success:
            pass

    return {
        **bank_dict,
        "transactions": transactions,
        "txn_queue": txn_queue,
        "txn_processor": txn_processor,
        "frozen_accounts": frozen_accounts,
    }


def show_client_accounts(bank_dict, client_id):
    """
    Prints the list of accounts
    belonging to a specific client.

    Args:
        bank_dict (dict): Dictionary with bank_data.
        client_id (str): Unique id of the client.

    Output:
        Prints account ID, balance, currency, and status
        for each account belonging to the client.
        If the client has no accounts,
        prints a corresponding message.
    """
    accounts = bank_dict.get("accounts", {}).values()
    client_accounts = [
        acc for acc in accounts if acc.owner_data.get("client_id") == client_id
    ]
    if not client_accounts:
        print(f"Client {client_id} has no accounts.")
        return
    print(f"Accounts of client {client_id}:")
    for acc in client_accounts:
        print(f"- Account ID: {acc.account_id}, Balance: {acc.acc_balance} "
              f"{acc.currency}, Status: {acc.status}")


def show_client_transaction_history(transactions_dict, client_id):
    """
    Prints the transaction history for a given client,
    including both sent and received transactions.

    Args:
        transactions_dict (dict): Dictionary of transactions.
        client_id (str): Unique id of the client.

    Output:
        Prints each transaction's date/time,
        direction (Sent/Received), ID, amount with currency, and status.
        Prints a message if no transactions are found.
    """
    txns = transactions_dict.values()
    filtered = [
        txn for txn in txns
        if txn.sender_account.owner_data.get("client_id") == client_id
        or txn.receiver_account.owner_data.get("client_id") == client_id
    ]
    if not filtered:
        print(f"No transactions found for client {client_id}.")
        return
    print(f"Transaction history for client {client_id}:")
    for txn in filtered:
        direction = "Sent" if txn.sender_account.owner_data.get("client_id") == client_id else "Received"
        ts = txn.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(
            txn, "created_at") else "Unknown"
        print(f"- {ts} | {direction} | ID: {txn.id[:8]} | Amount: "
              f"{txn.amount} {txn.currency} | Status: {txn.status.name}")


def analyze_and_report_suspicious_operations(transactions_dict):
    """
    Analyzes transactions for suspicious
    activity and prints risk reports.

    - Uses a RiskAnalyzer and AuditLog to identify and log suspicious txs.
    - Prints reports summarizing suspicious txs and client risk profiles.

    Args:
        transactions_dict (dict): Dictionary of transactions to analyze.
    """
    audit_log = AuditLog(level=LogLevel.INFO)
    risk_analyzer = RiskAnalyzer(audit_log)

    for txn in transactions_dict.values():
        risk_analyzer.analyze_transaction(txn)

    # Reports:
    risk_analyzer.report_suspicious_operations()
    risk_analyzer.report_risk_profile()


def report_top_clients_by_volume(transactions_dict, top_n=3):
    """
    Reports the top N clients ranked
    by total outgoing transaction volume.

    Args:
        transactions_dict (dict): Dictionary of Transaction objects.
        top_n (int, optional): Number of top clients to display. Default is 3.

    Output:
        Prints a ranked list of clients with their total amount sent.
    """
    client_sums = Counter()
    for txn in transactions_dict.values():
        client_id = txn.sender_account.owner_data.get("client_id")
        if client_id:
            client_sums[client_id] += txn.amount

    print(f"\n--- Top {top_n} Clients by Outgoing Transaction Volume ---")
    for client_id, total in client_sums.most_common(top_n):
        print(f"Client {client_id}: Total Sent Amount = {total:.2f}")


def report_transaction_statistics(transactions_dict):
    """
    Prints overall statistics on the transactions.

    - Total number of transactions.
    - Counts and sums of transactions by status.
    - Total sums by currency.

    Args:
        transactions_dict (dict): Dictionary of Transaction objects.
    """
    total = len(transactions_dict)
    status_counts = Counter()
    amount_by_status = Counter()
    amount_by_currency = Counter()

    for txn in transactions_dict.values():
        status_counts[txn.status.name] += 1
        amount_by_status[txn.status.name] += txn.amount
        amount_by_currency[txn.currency] += txn.amount

    print("\n--- Transaction Statistics ---")
    print(f"Total transactions: {total}")
    for status, count in status_counts.items():
        print(f"{status}: {count} (Sum: {amount_by_status[status]:.2f})")
    print("Amounts by currency:")
    for currency, amount in amount_by_currency.items():
        print(f"{currency}: {amount:.2f}")


def report_overall_balance(accounts_dict):
    """
    Prints combined balances of all accounts, aggregated by currency.

    Args:
        accounts_dict (dict): Dictionary of bank accounts.

    Output:
        Displays total balance per currency across all accounts.
    """
    balance_by_currency = Counter()
    for acc in accounts_dict.values():
        balance_by_currency[acc.currency] += acc.acc_balance

    print("\n--- Overall Account Balances by Currency ---")
    for currency, balance in balance_by_currency.items():
        print(f"{currency}: {balance:.2f}")


if __name__ == '__main__':
    bank_dict = create_bank_with_clients_and_accounts()
    transactions_dict = simulate_transactions(bank_dict)
    rand_client = next(iter(transactions_dict["clients"]))
    analyze_and_report_suspicious_operations(transactions_dict["transactions"])
    time.sleep(3)
    show_client_accounts(transactions_dict, rand_client)
    time.sleep(3)
    show_client_transaction_history(transactions_dict["transactions"], rand_client)
    time.sleep(3)
    report_top_clients_by_volume(transactions_dict["transactions"], top_n=3)
    time.sleep(3)
    report_transaction_statistics(transactions_dict["transactions"])
    time.sleep(3)
    report_overall_balance(transactions_dict["accounts"])

    report_builder = ReportBuilder(
        bank_data=bank_dict,
        transactions=transactions_dict["transactions"]
    )

    # Text report for client
    print(report_builder.report_client(
        next(iter(bank_dict["clients"].keys())))
    )
    time.sleep(3)
    # Text report for bank
    print(report_builder.report_bank())
    time.sleep(3)
    # Text report for risks
    print(report_builder.report_risks())
    time.sleep(3)
    # JSON export client_data
    clients_data = [
        { "id": cid, 
          "fio": c.fio, 
          "birth_date": 
          str(c.birth_date), 
          "contacts": c.contacts }
        for cid, c in bank_dict["clients"].items()
    ]
    report_builder.export_to_json(clients_data, "clients.json")

    # CSV export of an account data
    accounts_data = [{
        "account_id": acc.account_id,
        "client_id": acc.owner_data["client_id"],
        "balance": acc.acc_balance,
        "currency": acc.currency,
        "status": acc.status
    } for acc in bank_dict["accounts"].values()]
    fieldnames = ["account_id", "client_id", "balance", "currency", "status"]
    report_builder.export_to_csv(accounts_data, fieldnames, "accounts.csv")

    # Saving charts
    report_builder.save_charts()