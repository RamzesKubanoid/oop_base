from datetime import date, datetime, time, timedelta
from src.utils import BankAccount
from src.bank import Client
from src.transaction import Transaction, TransactionType
from src.audit import AuditLog, LogLevel, RiskAnalyzer


def audit_test():
    # Creating test clients
    client1 = Client(
        fio="Иванов Иван Иванович",
        client_id="client_001",
        birth_date=date(1990, 5, 15),
        contacts={"phone": "+79161234567", "email": "ivanov@example.com"}
    )

    client2 = Client(
        fio="Петрова Мария Сергеевна",
        client_id="client_002",
        birth_date=date(2005, 7, 20),
        contacts={"phone": "+79261234567", "email": "petrova@example.com"}
    )

    print("Is client 1 adult?", client1.is_adult())
    print("Is client 1 adult?", client2.is_adult())

    # Creating bank_accounts for clients
    account1 = BankAccount(
        owner_data={"client_id": client1.client_id, "fio": client1.fio},
        currency="RUB",
        acc_balance=500_000
    )

    account2 = BankAccount(
        owner_data={"client_id": client2.client_id, "fio": client2.fio},
        currency="USD",
        acc_balance=100_000
    )

    client1.add_account(account1.account_id)
    client2.add_account(account2.account_id)

    print(account1)
    print(account2)

    # Example of transaction
    transaction = Transaction(
        txn_type=TransactionType.INTERNAL,
        amount=150_000,
        currency="RUB",
        sender_account=account1,
        receiver_account=account2,
        commission=500
    )

    print(transaction)

    # Example of using RiskAnalyzer
    audit_log = AuditLog(level=LogLevel.INFO)
    risk_analyzer = RiskAnalyzer(audit_log=audit_log)

    risk_level = risk_analyzer.analyze_transaction(transaction)
    print(f"Transaction 1 risk: {risk_level.value}")

    # Adding few more txs to check for operations frequency and new receivers
    # Second tx (from the same client to new receiver)
    account3 = BankAccount(
        owner_data={"client_id": client1.client_id, "fio": client1.fio},
        currency="RUB",
        acc_balance=200_000
    )
    client1.add_account(account3.account_id)

    transaction2 = Transaction(
        txn_type=TransactionType.INTERNAL,
        amount=200_000,
        currency="RUB",
        sender_account=account1,
        receiver_account=account3,
        commission=0
    )

    risk_level2 = risk_analyzer.analyze_transaction(transaction2)
    print(f"Transaction 2 risk: {risk_level2.value}")

    # Transaction at night
    transaction.created_at = datetime.combine(datetime.today(), time(2, 30))
    risk_level_night = risk_analyzer.analyze_transaction(transaction)
    print(f"Risk of transaction at night: {risk_level_night.value}")

    # LOW RISK operation: small sum, daytime, known recipient
    transaction_low = Transaction(
        txn_type=TransactionType.INTERNAL,
        amount=500,
        currency="RUB",
        sender_account=account1,
        receiver_account=account2,
        commission=0
    )
    transaction_low.created_at = datetime.now().replace(hour=14, minute=0)
    client_id = transaction_low.sender_account.owner_data.get("client_id")
    risk_analyzer.client_txn_times[client_id].clear()
    risk_analyzer.client_known_recipients[client_id].add(
        transaction_low.receiver_account.account_id)

    risk_level_low = risk_analyzer.analyze_transaction(transaction_low)
    print(f"Low risk transaction: {risk_level_low.value}")

    # Consecutive operations for MEDIUM RISK due to frequency

    # Operation 1
    transaction_freq_1 = Transaction(
        txn_type=TransactionType.INTERNAL,
        amount=4000_00,
        currency="RUB",
        sender_account=account1,
        receiver_account=account3,
        commission=0
    )
    transaction_freq_1.created_at = datetime.now().replace(minute=0, second=0)  

    # Operation 2 (after 20 min)
    transaction_freq_2 = Transaction(
        txn_type=TransactionType.INTERNAL,
        amount=3000_00,
        currency="RUB",
        sender_account=account1,
        receiver_account=account3,
        commission=0
    )
    transaction_freq_2.created_at = transaction_freq_1.created_at + timedelta(minutes=20)

    # Operation 3 (after 40 min)
    transaction_freq_3 = Transaction(
        txn_type=TransactionType.INTERNAL,
        amount=3500_00,
        currency="RUB",
        sender_account=account1,
        receiver_account=account3,
        commission=0
    )
    transaction_freq_3.created_at = transaction_freq_1.created_at + timedelta(minutes=40)

    # Checking operations risk level
    for i, txn in enumerate([transaction_freq_1, transaction_freq_2, transaction_freq_3], start=1):
        risk = risk_analyzer.analyze_transaction(txn)
        print(f"Frequency transaction {i} risk: {risk.value}")

    # MEDIUM RISK operation because of sum slightly lower the threshold (10000 default)
    transaction_medium_sum = Transaction(
        txn_type=TransactionType.INTERNAL,
        amount=9500_00,
        currency="RUB",
        sender_account=account1,
        receiver_account=account3,
        commission=1000
    )

    transaction_medium_sum.created_at = datetime.now().replace(hour=11, minute=0)

    risk_medium_sum = risk_analyzer.analyze_transaction(transaction_medium_sum)
    print(f"Medium risk due to amount close to threshold: {risk_medium_sum.value}")


if __name__ == '__main__':
    audit_test()