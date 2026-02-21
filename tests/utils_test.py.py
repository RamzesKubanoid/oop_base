from src.utils import BankAccount, SavingsAccount, PremiumAccount, \
    InvestmentAccount, InsufficientFundsError, AccountFrozenError


def first_tests():
    # 1 Creating active and frozen account
    owner_info = {'name': 'Иван Иванов'}
    active_account = BankAccount(owner_data=owner_info,
                                 currency='RUB',
                                 status='active')
    print(active_account.get_account_info())

    frozen_account = BankAccount(owner_data=owner_info,
                                 currency='USD',
                                 status='frozen')
    print(frozen_account.get_account_info())

    # 2 Attempt to perform operation on a frozen account
    try:
        frozen_account.deposit(1000)
    except AccountFrozenError as e:
        print(e)
    try:
        frozen_account.withdraw(1000)
    except AccountFrozenError as e:
        print(e)

    # 3 Perform operation on an active account
    active_account.deposit(1000)
    active_account.withdraw(200)


def savings_account_tests():
    # 1 Creating active and frozen account
    owner_info = {'name': 'Павел Павлов'}
    active_account = SavingsAccount(owner_data=owner_info,
                                    currency='RUB',
                                    status='active',
                                    monthly_interest_rate=1.5,
                                    min_balance=500
                                    )
    print(active_account.get_account_info())

    frozen_account = SavingsAccount(owner_data=owner_info,
                                    currency='RUB',
                                    status='frozen',
                                    monthly_interest_rate=1.5
                                    )
    print(frozen_account.get_account_info())

    # 2 Attempt to perform operation on a frozen account
    try:
        frozen_account.deposit(1000)
    except AccountFrozenError as e:
        print(e)
    try:
        frozen_account.withdraw(1000)
    except AccountFrozenError as e:
        print(e)
    
    # 3 Perform operation on an active account
    active_account.deposit(1000)
    active_account.withdraw(200)

    # 4 Attempt to withdraw above threshold
    try:
        active_account.withdraw(500)
    except ValueError as e:
        print(e)
    # 5 Attempt to withdraw within the minimum
    try:
        active_account.withdraw(250)
    except ValueError as e:
        print(e)

def premium_account_tests():
    # 1 Creating active and frozen account
    owner_info = {'name': 'Андрей Андреев'}
    active_account = PremiumAccount(owner_data=owner_info,
                                    currency='RUB',
                                    status='active',
                                    premium_fixed_fee=1.2,
                                    overdraft_limit=1000
                                    )
    print(active_account.get_account_info())

    frozen_account = PremiumAccount(owner_data=owner_info,
                                    currency='RUB',
                                    status='active',
                                    premium_fixed_fee=1.2,
                                    overdraft_limit=1000
                                    )
    print(frozen_account.get_account_info())

    # 2 Attempt to perform operation on a frozen account
    try:
        frozen_account.deposit(1000)
    except AccountFrozenError as e:
        print(e)
    try:
        frozen_account.withdraw(1000)
    except AccountFrozenError as e:
        print(e)
    
    # 3 Perform operation on an active account
    active_account.deposit(1000)
    active_account.withdraw(200)

    # 4 Attempt to withdraw above threshold
    try:
        active_account.withdraw(1200)
    except ValueError as e:
        print(e)
    # 5 Attempt to withdraw within the minimum
    try:
        active_account.withdraw(1000)
    except (ValueError, InsufficientFundsError) as e:
        print(e)
    # 5 Attempt to withdraw more than a limit
    try:
        active_account.deposit(70000)
        active_account.withdraw(70000)
    except (ValueError, InsufficientFundsError) as e:
        print(e)


def investment_account_tests():
    # 1 Creating active and frozen account
    owner_info = {'name': 'Иван Иванов'}
    active_account = InvestmentAccount(owner_data=owner_info,
                                       currency='RUB',
                                       status='active')
    print(active_account.get_account_info())

    frozen_account = InvestmentAccount(owner_data=owner_info,
                                       currency='USD',
                                       status='frozen')
    print(frozen_account.get_account_info())

    # 2 Attempt to perform operation on a frozen account
    try:
        frozen_account.deposit(1000)
    except AccountFrozenError as e:
        print(e)
    try:
        frozen_account.withdraw(1000)
    except AccountFrozenError as e:
        print(e)

    # 3 Perform operation on an active account
    active_account.deposit(1000)
    active_account.withdraw(200)
    print(active_account)

if __name__ == '__main__':
    first_tests()
    savings_account_tests()
    premium_account_tests()
    investment_account_tests()