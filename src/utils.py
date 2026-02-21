import uuid
from abc import ABC, abstractmethod
from decimal import Decimal


ACCOUNT_STATUSES = ["active", "frozen", "closed"]


class AbstractAccount(ABC):
    """
    Abstract base class representing a generic bank account.

    Class defines the common interface and attributes for all accounts.

    Attributes:
        owner_data (dict): client_id and other info about the account owner.
        account_id (str, optional): Account ID. If None, it will be generated.
        acc_balance (int, optional): Balance of the account. Defaults to 0.
        status (str, optional): Status of the account, defaults to "active".
    """
    def __init__(
        self,
        owner_data: dict,
        account_id: str,
        acc_balance: int = 0,
        status: str = "active"):

        self.owner_data = owner_data
        self.account_id = account_id
        self.acc_balance = acc_balance
        self.status = status


    @abstractmethod
    def deposit(self, amount):
        """
        Deposits funds to the account.
    
        Args:
            amount (int): amount to deposit.
        """
        pass


    @abstractmethod
    def withdraw(self, amount):
        """
        Withdraws funds from the account.
    
        Args:
            amount (int): amount to withdraw.
        """
        pass


    @abstractmethod
    def get_account_info(self):
        """
        Get account info.
        """
        pass


class AccountFrozenError(Exception):
    """
    Error occurs while trying to perform operation
    on a frozen account
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AccountClosedError(Exception):
    """
    Error occurs while trying to perform operation
    on a closed account
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidOperationError(Exception):
    """
    Error occurs while trying to perform
    invalid type of operation
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InsufficientFundsError(Exception):
    """
    Error occurs while trying account
    does not have enough funds
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class BankAccount(AbstractAccount):
    """
    Represents a bank account with an owner, currency, balance, and status.

    Supported currencies are limited to a predefined set.

    Attributes:
        SUPPORTED_CURRENCIES (set): A set of supported currency codes.
        acc_type (str): account type
        owner_data (dict): client_id and other info about the account owner.
        currency (str): Currency code for the account balance.
        account_id (str, optional): Account ID. If None, it will be generated.
        acc_balance (int, optional): Balance of the account. Defaults to 0.
        status (str, optional): Status of the account, defaults to "active".
    """
    SUPPORTED_CURRENCIES = {'RUB', 'USD', 'EUR', 'KZT', 'CNY'}

    def __init__(
        self,
        owner_data: dict,
        currency: str,
        account_id: str = None,
        acc_balance: int = 0,
        status: str = "active"
    ):
        super().__init__(owner_data, account_id, acc_balance, status)
        self.currency = currency
        self.acc_type = "bank_account"
        # Currency validation
        if self.currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {self.currency}")

        # Owner_data validation
        if not isinstance(self.owner_data, dict):
            raise TypeError("Owner data must be a dictionary.")

        # UUID generation if id is None
        if self.account_id is None:
            self.account_id = str(uuid.uuid4())
        elif not isinstance(self.account_id, str):
            raise TypeError("Account ID must be a string.")
    

    def __str__(self):
        return (
            f"acc_type:{self.acc_type}\n"
            f"owner_data:{self.owner_data}\n"
            f"acc_numb_last:{self.account_id[-4:]}\n"
            f"status:{self.status}\n"
            f"balance:{self.acc_balance}\n"
            f"currency:{self.currency}"
        )


    def _validate_amount(self, amount):
        """
        Validates number type for amount.
    
        Args:
            amount (int, float): funds amount.
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number.")
        if amount <= 0:
            raise ValueError("Amount must be positive.")


    def _validate_status(self):
        """
        Validates account status.
        """
        if self.status == "frozen":
            raise AccountFrozenError("Cannot operate on frozen account.")
        if self.status == "closed":
            raise AccountClosedError("Cannot operate on closed account.")


    def deposit(self, amount: int):
        self._validate_amount(amount)
        self._validate_status()
        self.acc_balance += amount
        val_amount = Decimal(amount) / 100
        val_balance = Decimal(self.acc_balance) / 100
        print(
            f"Deposited {val_amount} {self.currency}. "
            f"Balance: {val_balance} {self.currency}"
        )


    def withdraw(self, amount: int):
        self._validate_amount(amount)
        self._validate_status()
        if amount > self.acc_balance:
            raise InsufficientFundsError("Insufficient funds.")
        self.acc_balance -= amount
        val_amount = Decimal(amount) / 100
        val_balance = Decimal(self.acc_balance) / 100
        print(
            f"Withdrawn {val_amount} {self.currency}. "
            f"Balance: {val_balance} {self.currency}"
        )


    def get_account_info(self):
        return {
            'account_id': self.account_id,
            'owner_data': self.owner_data,
            'balance': self.acc_balance,
            'status': self.status,
            'currency': self.currency,
            "acc_type": self.acc_type
        }


    def change_status(self, new_status: str):
        """
        Changes status of the account.
        
        Args:
            status (str): new status.
                Allowed statuses are: active, closed, frozen
        """
        if new_status not in ACCOUNT_STATUSES:
            raise ValueError("Invalid status type.")
        self.status = new_status
        print(f"Account status changed to {self.status}")


class SavingsAccount(BankAccount):
    """
    Represents a savings bank account.

    Adds interest rate and minimum balance.

    Attributes:
        acc_type (str): account type
        owner_data (dict): client_id and other info about the account owner.
        currency (str): Currency code for the account balance.
        account_id (str, optional): Account ID. If None, it will be generated.
        acc_balance (int, optional): Balance of the account. Defaults to 0.
        status (str, optional): Status of the account, defaults to "active".
        min_balance (int): The minimum balance the account must maintain.
        monthly_interest_rate (Decimal): Monthly interest rate of the account.
    """
    def __init__(
        self,
        owner_data: dict,
        currency: str,
        monthly_interest_rate: Decimal,
        account_id: str = None,
        acc_balance: int = 0,
        status: str = "active",
        min_balance: int = 0
    ):
        super().__init__(owner_data,
                         currency,
                         account_id,
                         acc_balance,
                         status)
        self.min_balance = min_balance
        self.acc_type = "savings_account"
        self.monthly_interest_rate = monthly_interest_rate


    def apply_monthly_interest(self):
        """
        Applies monthly status of the account.
        """
        self._validate_status()
        if self.acc_balance >= self.min_balance:
            interest = int(self.acc_balance * self.monthly_interest_rate)
            self.acc_balance += interest
            val_interest = Decimal(interest) / 100
            val_balance = Decimal(self.acc_balance) / 100
            print(
                f"Applied interest: {val_interest} {self.currency}. \
                New balance: {val_balance} {self.currency}"
            )
        else:
            print(
                f"Balance below minimum {self.min_balance/100} \
                {self.currency}. Interest not applied."
            )


    def withdraw(self, amount: int):
        self._validate_amount(amount)
        self._validate_status()
        if self.acc_balance - amount < self.min_balance:
            raise ValueError(
                f"Cannot withdraw {Decimal(amount)/100} "
                f"{self.currency}. Minimum balance "
                f"{Decimal(self.min_balance)/100} "
                f"{self.currency} must be maintained.")
        if amount > self.acc_balance:
            raise InsufficientFundsError("Insufficient funds.")
        self.acc_balance -= amount
        val_amount = Decimal(amount) / 100
        val_balance = Decimal(self.acc_balance) / 100
        print(
            f"Withdrawn {val_amount} {self.currency}. "
            f"Balance: {val_balance} {self.currency}"
        )


    def get_account_info(self):
        info = super().get_account_info()
        info["acc_type"] = self.acc_type
        info["min_balance"] = self.min_balance
        info["monthly_interest_rate"] = self.monthly_interest_rate

        return info

    def __str__(self):
        base_str = super().__str__()
        return (
            f"{base_str}\n"
            f"min_balance:{Decimal(self.min_balance)/100} {self.currency}\n"
            f"monthly_interest_rate:{self.monthly_interest_rate}%"
        )


class PremiumAccount(BankAccount):
    """
    Represents a premium bank account with overdraft facility, fixed fees, 
        and withdrawal limits.

    Attributes:
        acc_type (str): account type
        owner_data (dict): client_id and other info about the account owner.
        currency (str): Currency code for the account balance.
        account_id (str, optional): Account ID. If None, it will be generated.
        acc_balance (int, optional): Balance of the account. Defaults to 0.
        status (str, optional): Status of the account, defaults to "active".
        overdraft_limit (int): Maximum overdraft amount allowed 
            (in smallest currency units).
        premium_fixed_fee (Decimal): Fixed fee percentage charged to the account.
        withdraw_limit (int, optional): Maximum allowable withdrawal 
            per transaction (default 50_000).
    """
    def __init__(
        self,
        owner_data: dict,
        currency: str,
        overdraft_limit: int,
        premium_fixed_fee: Decimal,
        withdraw_limit: int = 50_000,
        account_id: str = None,
        acc_balance: int = 0,
        status: str = "active",
    ):
        super().__init__(owner_data,
                         currency,
                         account_id,
                         acc_balance,
                         status)
        self.overdraft_limit = overdraft_limit
        self.premium_fixed_fee = premium_fixed_fee
        self.withdraw_limit = withdraw_limit
        self.acc_type = "premium_account"

    def withdraw(self, amount: int):
        self._validate_amount(amount)
        self._validate_status()
        if amount > self.withdraw_limit:
            raise ValueError(
                f"Withdraw amount {Decimal(amount)/100} "
                f"{self.currency} exceeds limit "
                f"{Decimal(self.withdraw_limit)/100} {self.currency}."
            )

        if self.acc_balance - amount < -self.overdraft_limit:
            raise InsufficientFundsError(
                f"Insufficient funds including overdraft limit "
                f"(balance: {Decimal(self.acc_balance)/100} {self.currency}, "
                f"overdraft limit: {Decimal(self.overdraft_limit)/100} "
                f"{self.currency})."
            )
        self.acc_balance -= amount
        val_amount = Decimal(amount) / 100
        val_balance = Decimal(self.acc_balance) / 100
        print(
            f"Withdrawn {val_amount} {self.currency}. "
            f"Balance: {val_balance} {self.currency}"
        )

    def get_account_info(self):
        info = super().get_account_info()
        info["overdraft_limit"] = self.overdraft_limit
        info["premium_fixed_fee"] = self.premium_fixed_fee
        info["withdraw_limit"] = self.withdraw_limit

        return info

    def __str__(self):
        base_str = super().__str__()
        return (
            f"{base_str}\n"
            f"overdraft_limit: {self.overdraft_limit}\n"
            f"fixed_fee: {Decimal(self.premium_fixed_fee)}%\n"
            f"withdraw_limit: {Decimal(self.withdraw_limit)}"
        )


class InvestmentAccount(BankAccount):
    """
    Represents an investment bank account holding a portfolio of assets.

    Attributes:
        owner_data (dict): client_id and other info about the account owner.
        currency (str): Currency code for the account balance.
        account_id (str, optional): Account ID. If None, it will be generated.
        acc_balance (int, optional): Balance of the account. Defaults to 0.
        status (str, optional): Status of the account. Defaults to "active".
        acc_type (str): account type
        portfolio (dict): Dictionary representing investment holdings.
            Each value is a dictionary intended to hold asset details.
    """
    def __init__(
        self,
        owner_data: dict,
        currency: str,
        account_id: str = None,
        acc_balance: int = 0,
        status: str = "active",
    ):
        super().__init__(owner_data, currency, account_id, acc_balance, status)
        self.acc_type = "investment_account"
        self.portfolio = {
            'stocks': {},
            'bonds': {},
            'etf': {}
        }
    

    def add_asset():
        """
        tbd method to buy a virtual asset
        """
        pass

    def sell_asset():
        """
        tbd method to sell a virtual asset
        """
        pass


    def get_assets_sum(self):
        """
        Get equity sum for all assets
        """
        total = 0
        for sub_dict in self.portfolio.values():
            total += sum(sub_dict.values())
        
        return total


    def project_yearly_growth(self, growth_rates: dict) -> float:
        """
        Calculate yearly portfolio growth

        Args:
            growth_rates dict: assets growth rates dict
        """
        total_value = 0
        for asset_type, assets in self.portfolio.items():
            total_qty = sum(assets.values())
            rate = growth_rates.get(asset_type, 0)
            total_value += total_qty * (1 + rate)
        total_value += self.acc_balance / 100
        return total_value


    def withdraw(self, amount: int):
        self._validate_amount(amount)
        self._validate_status()
        if amount > self.acc_balance:
            raise InsufficientFundsError("Insufficient funds.")
        self.acc_balance -= amount
        val_amount = Decimal(amount) / 100
        val_balance = Decimal(self.acc_balance) / 100
        print(
            f"Withdrawn {val_amount} {self.currency}. "
            f"Balance: {val_balance} {self.currency} "
            f"Assets balance {self.get_assets_sum()} {self.currency}"
        )


    def get_account_info(self):
        info = super().get_account_info()
        info['portfolio'] = self.portfolio
        return info


    def __str__(self):
        base_str = super().__str__()
        portfolio_str = "\nPortfolio:\n"
        for asset_type, assets in self.portfolio.items():
            portfolio_str += f"  {asset_type}:\n"
            if assets:
                for symbol, qty in assets.items():
                    portfolio_str += f"    {symbol}: {qty}\n"
            else:
                portfolio_str += "    <empty>\n"
        return base_str + portfolio_str


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


def savings_account_tests():
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

    # Попытка операций над замороженным счётом
    try:
        frozen_account.deposit(1000)
    except AccountFrozenError as e:
        print(e)
    try:
        frozen_account.withdraw(1000)
    except AccountFrozenError as e:
        print(e)
    
    # Попытка операций над активным счётом
    active_account.deposit(1000)
    active_account.withdraw(200)

    # Попытка вывода ниже предела
    try:
        active_account.withdraw(500)
    except ValueError as e:
        print(e)
    # Попытка вывода в пределах минимума
    try:
        active_account.withdraw(250)
    except ValueError as e:
        print(e)

def premium_account_tests():
    # 2 PremiumAccount
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

    # 2.2 Попытка операций над замороженным счётом
    try:
        frozen_account.deposit(1000)
    except AccountFrozenError as e:
        print(e)
    try:
        frozen_account.withdraw(1000)
    except AccountFrozenError as e:
        print(e)
    
    # Попытка операций над активным счётом
    active_account.deposit(1000)
    active_account.withdraw(200)

    # Попытка вывода ниже предела
    try:
        active_account.withdraw(1200)
    except ValueError as e:
        print(e)
    # Попытка вывода в пределах минимума
    try:
        active_account.withdraw(1000)
    except (ValueError, InsufficientFundsError) as e:
        print(e)
    # Попытка вывода больше лимита
    try:
        active_account.deposit(70000)
        active_account.withdraw(70000)
    except (ValueError, InsufficientFundsError) as e:
        print(e)


def investment_account_tests():
    # 1 Создание активного и замороженного счетов
    owner_info = {'name': 'Иван Иванов'}
    active_account = InvestmentAccount(owner_data=owner_info,
                                       currency='RUB',
                                       status='active')
    print(active_account.get_account_info())

    frozen_account = InvestmentAccount(owner_data=owner_info,
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
    print(active_account)

if __name__ == '__main__':
    investment_account_tests()