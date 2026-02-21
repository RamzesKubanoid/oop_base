from collections import defaultdict, deque
from datetime import date, datetime, timedelta, time
from enum import Enum
from threading import Lock
from transaction import Transaction, TransactionStatus


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40


class AuditLog:
    """
    A logging class that outputs messages with different severity levels.

    Attributes:
        level (LogLevel): The minimum severity level to log.
        lock (Lock): A threading lock to ensure thread-safe output.
    """
    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level
        self.lock = Lock()

    def _log(self, level: LogLevel, message: str):
        if level.value < self.level.value:
            return
        timestamp = datetime.now().isoformat()
        with self.lock:
            print(f"{timestamp} [{level.name}] {message}")

    def debug(self, msg: str):
        self._log(LogLevel.DEBUG, msg)

    def info(self, msg: str):
        self._log(LogLevel.INFO, msg)

    def warn(self, msg: str):
        self._log(LogLevel.WARN, msg)

    def error(self, msg: str):
        self._log(LogLevel.ERROR, msg)


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskAnalyzer:
    """
    Analyzes transactions to identify potentially fraudulent
    or suspicious activity based on multiple risk factors.

    Attributes:
        audit_log (AuditLog): Object for logging analysis activities.
        large_amount_threshold (float): Threshold for 
            flagging large transactions.
        frequent_count_threshold (int): Number of transactions within a 
            time window triggering suspicion.
        frequent_time_window (timedelta): Time window to check 
            for transaction frequency.
        night_start (time): Start time of the night period.
        night_end (time): End time of the night period.
        client_txn_times (defaultdict): Stores recent transaction 
            times per client to analyze frequency.
        client_known_recipients (defaultdict): Tracks known 
            recipients per client.
        suspicious_transactions (list): Stores transactions 
            flagged as suspicious with reasons.
    """
    def __init__(
        self,
        audit_log: AuditLog,
        large_amount_threshold: float = 10000.0,
        frequent_count_threshold: int = 3,
        frequent_time_window_mins: int = 60,
        night_start: time = time(0, 0),
        night_end: time = time(6, 0),
    ):
        self.audit_log = audit_log
        self.large_amount_threshold = large_amount_threshold
        self.frequent_count_threshold = frequent_count_threshold
        self.frequent_time_window = timedelta(minutes=frequent_time_window_mins)
        self.night_start = night_start
        self.night_end = night_end

        # For frequency analysis by client_id (sender)
        self.client_txn_times = defaultdict(deque)
        # For tracking new receivers (account_id)
        self.client_known_recipients = defaultdict(set)

        # Storing suspicious transactions
        # Format: list of tuples (transaction, RiskLevel, [reasons])
        self.suspicious_transactions = []


    def is_night(self, dt: datetime) -> bool:
        """
        Determines if a given datetime falls within
        the configured night hours.

        Args:
            dt (datetime): The datetime to evaluate.

        Returns:
            bool: True if the time is 
                within night hours, False otherwise.
        """
        t = dt.time()
        if self.night_start < self.night_end:
            return self.night_start <= t < self.night_end
        else:
            # For cases like 22:00 - 06:00
            return t >= self.night_start or t < self.night_end


    def analyze_transaction(self, transaction: Transaction) -> RiskLevel:
        """
        Analyzes a transaction to assess its
        risk level based on defined criteria.

        Args:
            transaction (Transaction): The transaction to evaluate.

        Returns:
            RiskLevel: The assessed risk level (LOW, MEDIUM, HIGH).
        """
        reasons = []

        # 1. Large transaction amount
        if transaction.amount >= self.large_amount_threshold:
            reasons.append("Large amount")

        # 2. Frequent transactions from the same client
        client_id = transaction.sender_account.owner_data.get(
            "client_id", None
        )
        if client_id is None:
            self.audit_log.error("Transaction with missing client_id in sender account owner_data.")
            # Default to LOW risk if no client data
            risk_level = RiskLevel.LOW
            return risk_level

        now = transaction.created_at
        times = self.client_txn_times[client_id]
        times.append(now)
        # Remove old transaction timestamps outside the window
        while times and times[0] < now - self.frequent_time_window:
            times.popleft()
        if len(times) >= self.frequent_count_threshold:
            reasons.append("Frequent operations")

        # 3. New recipient (receiver account not previously known)
        recipients = self.client_known_recipients[client_id]
        receiver_acc_id = transaction.receiver_account.account_id
        if receiver_acc_id not in recipients:
            reasons.append("New recipient")
            recipients.add(receiver_acc_id)

        # 4. Transaction during night hours
        if self.is_night(now):
            reasons.append("Night operation")

        # Determine overall risk level based on reasons
        if not reasons:
            risk_level = RiskLevel.LOW
        elif len(reasons) == 1:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH

        # Log suspicious transactions
        if risk_level != RiskLevel.LOW:
            self.audit_log.warn(
                f"Transaction {transaction.id[:8]} flagged as "
                f"{risk_level.value} risk. Reasons: {', '.join(reasons)}"
            )
            self.suspicious_transactions.append((transaction, risk_level, reasons))
        else:
            self.audit_log.info(f"Transaction {transaction.id[:8]} assessed as low risk.")

        return risk_level


    def report_suspicious_operations(self):
        """
        Prints a report of all flagged suspicious transactions with their reasons.
        """
        print("\n--- Suspicious Transactions Report ---")
        for txn, risk, reasons in self.suspicious_transactions:
            client_id = txn.sender_account.owner_data.get("client_id", "Unknown")
            print(
                f"ID: {txn.id[:8]} Sender: {client_id} Amount: {txn.amount} {txn.currency} "
                f"Risk: {risk.value} Reasons: {', '.join(reasons)}"
            )


    def report_risk_profile(self):
        """
        Summarizes the number of suspicious transactions per client and risk level.
        """
        print("\n--- Client Risk Profile ---")
        profile = defaultdict(lambda: {"Low": 0, "Medium": 0, "High": 0})
        for txn, risk, _ in self.suspicious_transactions:
            client_id = txn.sender_account.owner_data.get("client_id", "Unknown")
            profile[client_id][risk.value] += 1
        for client_id, counts in profile.items():
            print(f"Client {client_id}: {counts}")


    def report_error_stats(self, transactions):
        """
        Reports the reasons for transaction failures based on a list of transactions.

        Args:
            transactions (list): List of Transaction objects to analyze.
        """
        print("\n--- Transaction Error Statistics ---")
        error_counts = defaultdict(int)
        for txn in transactions:
            if txn.status == TransactionStatus.FAILED:
                reason = txn.fail_reason or "Unknown"
                error_counts[reason] += 1
        if error_counts:
            for reason, count in error_counts.items():
                print(f"Failed reason '{reason}': {count} times")
        else:
            print("No failed transactions.")