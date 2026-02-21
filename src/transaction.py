import uuid
from datetime import datetime
from collections import deque
from enum import Enum, auto
from typing import Optional, List, Dict


class TransactionStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class TransactionType(Enum):
    INTERNAL = auto()
    EXTERNAL = auto()


class Transaction:
    """
    Represents a financial transaction between two accounts.

    Contains information about the transaction type, amount, currency,
    involved accounts, commission fees, status, timestamps, 
    and failure reason if any.

    Attributes:
        id (str): Unique identifier for the transaction (UUID string).
        type (TransactionType): The transaction type.
        amount (float): The transaction amount.
        currency (str): The currency of the transaction.
        commission (float): Commission fee charged for the transaction.
        sender_account: Reference to the sender's account.
        receiver_account: Reference to the receiver's account.
        status (TransactionStatus): Current status of the transaction.
        fail_reason (str or None): Reason for failure, if transaction failed.
        created_at (datetime): Timestamp when the transaction was created.
        completed_at (datetime or None): Timestamp when the 
            transaction was completed.
    """
    def __init__(
        self,
        txn_type: TransactionType,
        amount: float,
        currency: str,
        sender_account,
        receiver_account,
        commission: float = 0.0,
    ):
        self.id = str(uuid.uuid4())
        self.type = txn_type
        self.amount = amount
        self.currency = currency
        self.commission = commission
        self.sender_account = sender_account
        self.receiver_account = receiver_account
        self.status = TransactionStatus.PENDING
        self.fail_reason = None
        self.created_at = datetime.now()
        self.completed_at = None

    def __str__(self):
        return (
            f"Transaction({self.id[:8]}, {self.type.name}, {self.amount} {self.currency}, "
            f"status={self.status.name})"
        )


class TransactionQueue:
    def __init__(self):
        """
        Initialize an empty TransactionQueue.

        The queue is implemented as a list of deques,
        each representing a priority level.
        Also maintains a dictionary for delayed (postponed) transactions
        and a set for cancelled transaction IDs.
        """
        self.queue: List[deque] = []
        self.delayed: Dict[str, Transaction] = {}  # postponed txs by ID
        self.cancelled_ids = set()


    def add(self, transaction: Transaction, priority: int = 0, delayed: bool = False):
        """
        Add a transaction to the queue 
        with a given priority or mark it as delayed.

        Args:
            transaction (Transaction): The transaction to add.
            priority (int, optional): Priority level of the transaction 
                (0 is highest priority). Defaults to 0.
            delayed (bool, optional): If True, the transaction 
                is added to the delayed queue. Defaults to False.
        """
        while len(self.queue) <= priority:
            self.queue.append(deque())
        if delayed:
            self.delayed[transaction.id] = transaction
        else:
            self.queue[priority].append(transaction)


    def pop(self) -> Optional[Transaction]:
        """
        Remove and return the highest-priority transaction from the queue.

        Skips transactions that have been cancelled.

        Returns:
            Transaction or None: The next available transaction
                or None if queue is empty.
        """
        for q in self.queue:
            while q:
                txn = q.popleft()
                if txn.id in self.cancelled_ids:
                    self.cancelled_ids.remove(txn.id)
                    continue
                return txn
        return None


    def cancel(self, transaction_id: str):
        """
        Cancel a transaction by ID.

        If the transaction is delayed, it is removed from the delayed dict.
        Otherwise, its ID is added to the cancelled_ids set to skip it later.

        Args:
            transaction_id (str): The unique ID of the transaction to cancel.
        """
        if transaction_id in self.delayed:
            del self.delayed[transaction_id]
        else:
            self.cancelled_ids.add(transaction_id)


    def release_delayed(self, transaction_id: str, priority: int = 0):
        """
        Release a delayed transaction back into
        the main queue with a specified priority.

        Args:
            transaction_id (str): The unique ID
                of the delayed transaction to release.
            priority (int, optional): Priority level to assign
                when re-adding to the queue. Defaults to 0.
        """
        txn = self.delayed.pop(transaction_id, None)
        if txn:
            self.add(txn, priority=priority, delayed=False)


    def is_empty(self):
        """
        Check if the transaction queue and delayed dict are both empty.

        Returns:
            bool: True if no transactions
                are pending or delayed, False otherwise.
        """
        if any(queue for queue in self.queue if queue):
            return False
        if self.delayed:
            return False
        return True


    def __str__(self):
        counts = [len(q) for q in self.queue]
        return f"TransactionQueue(priorities={counts}, delayed={len(self.delayed)})"


class TransactionProcessor:
    """
    Processes financial transactions including currency conversion,
    commission calculation, account balance checks,
    and transaction execution with retry logic.

    Attributes:
        MAX_RETRIES (int): Maximum number of retries 
            allowed for processing a transaction.
        currency_rates (Dict[str, float]): Exchange rates relative to USD.
        retry_counts (Dict[str, int]): Tracks retry 
            attempts for each transaction by ID.
    """
    MAX_RETRIES = 3

    def __init__(self, currency_rates: Dict[str, float] = None):
        self.currency_rates = currency_rates or {
            "USD": 1.0, "EUR": 0.9, "RUB": 0.015
        }
        self.retry_counts = {}


    def convert_currency(self,
                         amount: float,
                         from_currency: str,
                         to_currency: str) -> float:
        """
        Convert an amount from one currency to another using stored exchange rates.

        Args:
            amount (float): The amount of money to convert.
            from_currency (str): The currency code of the original amount.
            to_currency (str): The desired currency code to convert to.

        Returns:
            float: The converted amount, rounded to 2 decimal places.
        """
        if from_currency == to_currency:
            return amount
        usd_amount = amount / self.currency_rates.get(from_currency, 1)
        converted = usd_amount * self.currency_rates.get(to_currency, 1)
        return round(converted, 2)


    def calculate_commission(self, transaction: Transaction) -> float:
        """
        Calculate the commission fee for a given transaction.

        Args:
            transaction (Transaction):
              The transaction to calculate commission for.

        Returns:
            float: The commission amount, rounded to 2 decimal places.
        """
        # Commission: 1% for external transfers, 0 for internal
        if transaction.type == TransactionType.EXTERNAL:
            return round(transaction.amount * 0.01, 2)
        return 0.0


    def can_transfer(self, sender_account, amount: float) -> bool:
        """
        Check if the sender account can transfer the given amount.

        Rules:
            - Transfers are not allowed
                if the account status is "frozen".
            - Account balance must remain non-negative
                after transfer for non-premium accounts.

        Args:
            sender_account: The sender's account object
                with balance and status attributes.
            amount (float): The total amount
                (including commission) to be transferred.

        Returns:
            bool: True if transfer is allowed, False otherwise.
        """
        # Balance below 0 (except premium) not allowed
        # Frozen accounts not allowed
        if sender_account.status == "frozen":
            return False
        if sender_account.acc_balance - amount < 0 and \
        not sender_account.acc_type == "premium_account":
            return False
        return True


    def process(self, transaction: Transaction) -> bool:
        """
        Attempt to process a transaction: perform checks,
        convert currencies, update balances,
        handle commissions, and retry on failure up to MAX_RETRIES.

        Args:
            transaction (Transaction): The transaction to process.

        Returns:
            bool: True if transaction is successfully 
                completed, False otherwise.
        """
        txn_id = transaction.id
        self.retry_counts.setdefault(txn_id, 0)

        if transaction.status != TransactionStatus.PENDING:
            print(
                f"Transaction {txn_id} already processed: {transaction.status.name}"
            )
            return False

        # Checks
        if transaction.sender_account.status == "frozen" or \
            transaction.receiver_account.status == "frozen":
            transaction.status = TransactionStatus.FAILED
            transaction.fail_reason = "Frozen account"
            transaction.completed_at = datetime.now()
            print(f"Declined, account is frozen: {transaction}")
            return False

        commission = self.calculate_commission(transaction)
        total_amount = transaction.amount + commission

        if not self.can_transfer(transaction.sender_account, total_amount):
            transaction.status = TransactionStatus.FAILED
            transaction.fail_reason = "Insufficient funds or overdraft restricted"
            transaction.completed_at = datetime.now()
            print(f"Declined, insufficient funds: {transaction}")
            return False

        try:
            # Currency conversion if needed
            amount_in_sender_currency = self.convert_currency(
                transaction.amount, 
                transaction.currency, 
                transaction.sender_account.currency
            )
            commission_in_sender_currency = self.convert_currency(
                commission, 
                transaction.currency, 
                transaction.sender_account.currency
            )
            total_in_sender_currency = amount_in_sender_currency + \
                commission_in_sender_currency

            amount_in_receiver_currency = self.convert_currency(
                transaction.amount, 
                transaction.currency, 
                transaction.receiver_account.currency
            )

            # Withdrawing from sender account
            transaction.sender_account.acc_balance -= total_in_sender_currency
            # Send to the receiver
            transaction.receiver_account.acc_balance += \
                amount_in_receiver_currency

            transaction.commission = commission
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()

            print(f"Transaction successful: {transaction}")
            return True

        except Exception as e:
            self.retry_counts[txn_id] += 1
            if self.retry_counts[txn_id] > self.MAX_RETRIES:
                transaction.status = TransactionStatus.FAILED
                transaction.fail_reason = f"Processing failure: {e}"
                transaction.completed_at = datetime.now()
                print(f"Declined after {self.MAX_RETRIES} retries: {transaction}")
                return False
            else:
                print(f"Error: {e}, retrying {txn_id} (attempt {self.retry_counts[txn_id]})")
                return False