from src.utils import BankAccount, AccountFrozenError

def first_tests():
    # 1 Создание активного и замороженного счетов
    owner_info = {'name': 'Иван Иванов'}
    active_account = BankAccount(owner_data=owner_info,
                                 currency='RUB',
                                 status='active')
    print(active_account.get_account_info())

    frozen_account = BankAccount(owner_data=owner_info,
                                 currency='USD',
                                 status='frozen')
    print(frozen_account.get_account_info())

    # 2 Попытка операций над замороженным счётом
    try:
        frozen_account.deposit(1000)
    except AccountFrozenError as e:
        print(e)
    try:
        frozen_account.withdraw(1000)
    except AccountFrozenError as e:
        print(e)

    # 3 Попытка операций над замороженным счётом
    active_account.deposit(1000)
    active_account.withdraw(200)

if __name__ == '__main__':
    first_tests()