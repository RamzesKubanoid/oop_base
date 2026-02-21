from datetime import date
from src.bank import Client
from src.utils import BankAccount, PremiumAccount
from src.transaction import Transaction, TransactionQueue, \
    TransactionProcessor, TransactionType, TransactionStatus


def transaction_test():
    # Creating clients
    client_1 = Client(fio="Иван Иванов", 
                      client_id="id_1", 
                      birth_date=date(1995,10,10), 
                      contacts={"phone": "+7-987-654"})
    client_2 = Client(fio="Пётр Петров", 
                      client_id="id_2", 
                      birth_date=date(1997,11,11), 
                      contacts={"phone": "+7-987-142"})

    # Accounts
    acc_1 = BankAccount(account_id="acc1",
                        owner_data={"phone":client_1.contacts},
                        acc_balance=1000,
                        currency="USD",
                        status="active")
    acc_2 = BankAccount(account_id="acc2",
                        owner_data={"phone":client_1.contacts},
                        acc_balance=500,
                        currency="USD",
                        status="frozen")
    acc_3 = PremiumAccount(account_id="acc3",
                           owner_data={"phone":client_2.contacts},
                           acc_balance=3000,
                           currency="EUR",
                           status="active",
                           overdraft_limit=1000,
                           premium_fixed_fee=1.0)
    acc_4 = BankAccount(account_id="acc4",
                        owner_data={"phone":client_2.contacts},
                        acc_balance=10,
                        currency="USD")

    # Transactions queue
    queue = TransactionQueue()
    processor = TransactionProcessor()

    # Creating 10 transactions with different conditions
    txns = [
        Transaction(TransactionType.INTERNAL, 100, "USD", acc_1, acc_3),
        # with currency conversion
        Transaction(TransactionType.EXTERNAL, 50, "USD", acc_3, acc_4),
        # negative balance not premium
        Transaction(TransactionType.INTERNAL, 2000, "USD", acc_1, acc_2),
        # insufficient funds
        Transaction(TransactionType.INTERNAL, 100, "USD", acc_4, acc_1),
        # sender account frozen
        Transaction(TransactionType.INTERNAL, 10, "USD", acc_2, acc_1),
        Transaction(TransactionType.EXTERNAL, 500, "EUR", acc_3, acc_1),
        Transaction(TransactionType.INTERNAL, 5, "USD", acc_1, acc_4),
        # comission
        Transaction(TransactionType.EXTERNAL, 20, "USD", acc_4, acc_3),
        Transaction(TransactionType.INTERNAL, 300, "USD", acc_1, acc_4),
        # negative balance premium
        Transaction(TransactionType.INTERNAL, 700, "USD", acc_3, acc_1),
    ]

    # Adding all transactions in the queue with different priority
    priorities = [0, 1, 0, 0, 1, 1, 0, 1, 0, 0]
    for txn, prio in zip(txns, priorities):
        queue.add(txn, priority=prio)

    print("Starting queue processing...")
    while not queue.is_empty():
        txn = queue.pop()
        if not txn:
            break
        success = processor.process(txn)
        if not success and txn.status == TransactionStatus.PENDING:
            # If attempt failed, but status PENDING — postpone for retry
            queue.add(txn, priority=0, delayed=True)

    print("All transactions processed.")


if __name__ == "__main__":
    transaction_test()