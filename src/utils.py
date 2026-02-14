import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


ACCOUNT_STATUSES = ["active", "frozen", "closed"]


class AbstractAccount(ABC):
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
        Deposit funds to account.
        """
        pass


    @abstractmethod
    def withdraw(self, amount):
        """
        Withdraw funds from account.
        """
        pass


    @abstractmethod
    def get_account_info(self):
        """
        Get acoount info.
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


@dataclass
class BankAccount(AbstractAccount):
    SUPPORTED_CURRENCIES = {'RUB', 'USD', 'EUR', 'KZT', 'CNY'}

    def __init__(
        self,
        owner_data: dict,
        currency: str,
        account_id: str = None,
        acc_balance: int = 0,
        status: str = "active"
    ):
        AbstractAccount.__init__(self, owner_data, account_id, acc_balance, status)
        self.currency = currency
        self.acc_type = "bank_account"
        # Валидация валюты
        if self.currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {self.currency}")

        # Валидируем owner_data
        if not isinstance(self.owner_data, dict):
            raise TypeError("Owner data must be a dictionary.")

        # Генерация короткого UUID, если не передан id
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
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number.")
        if amount <= 0:
            raise ValueError("Amount must be positive.")


    def _validate_status(self):
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
        if new_status not in ACCOUNT_STATUSES:
            raise ValueError("Invalid status type.")
        self.status = new_status
        print(f"Account status changed to {self.status}")