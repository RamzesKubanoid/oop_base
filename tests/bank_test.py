from datetime import date
from src.bank import Bank
from src.utils import BankAccount, SavingsAccount, PremiumAccount


def bank_test():
    bank = Bank()

    # Creating clients
    client1_id = bank.add_client(
        fio="Иванов Иван Иванович",
        birth_date=date(1990, 12, 1),
        contacts={"phone": "+7-123-456", "email": "ivanov@mail.com"}
    )
    try:
        client2_id = bank.add_client(
            fio="Петров Петр Петрович",
            birth_date=date(2009, 10, 1),
            contacts={"phone": "+7-987-654", "email": "petrov@mail.com"}
        )  # younger than 18 - error
    except ValueError as e:
        print(e)

    # Correcting age after error
    client2_id = bank.add_client(
        fio="Петров Петр Петрович", 
        birth_date=date(1995, 10, 1), 
        contacts={"phone": "+7-987-654", "email": "petrov@mail.com"})

    # Opening accounts
    account1 = BankAccount(owner_data={"client_id": client1_id},
                           currency="RUB",
                           acc_balance=100000)
    account2 = SavingsAccount(owner_data={"client_id": client1_id},
                              currency="USD",
                              monthly_interest_rate=0.01,
                              min_balance=5000 * 100)
    account3 = PremiumAccount(owner_data={"client_id": client2_id},
                              currency="EUR",
                              overdraft_limit=20000,
                              premium_fixed_fee=0.02)
    account4 = BankAccount(owner_data={"client_id": client2_id},
                           currency="RUB",
                           acc_balance=50000)

    bank.open_account(client1_id, account1)
    bank.open_account(client1_id, account2)
    bank.open_account(client2_id, account3)
    bank.open_account(client2_id, account4)

    # Authentication with errors
    bank.failed_login_attempt(client1_id)
    bank.failed_login_attempt(client1_id)
    bank.failed_login_attempt(client1_id)  # third attempt - block
    try:
        bank.authenticate_client(client1_id)  # Error due to client block
    except Exception as e:
        print(e)

    # Withdraw attempt from frozen account
    bank.freeze_account(account1.account_id)
    try:
        account1.withdraw(1000)
    except Exception as e:
        print(f"Withdraw error, account is frozen: {e}")

    bank.unfreeze_account(account1.account_id)
    account1.withdraw(1000)

    # Clients rating by balance
    ranking = bank.get_clients_ranking()
    for client, bal in ranking:
        print(f"{client.fio}: {bal / 100:.2f}")

    # Total bank balance
    print(f"Total balance of the bank: {bank.get_total_balance() / 100:.2f}")

if __name__ == '__main__':
    bank_test()