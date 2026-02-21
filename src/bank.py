from utils import BankAccount
from typing import Dict
import uuid
from datetime import date, datetime, time


class Client:
    """
    Represents a bank client with personal information and related accounts.

    Attributes:
        fio (str): Full name of the client.
        client_id (str): Unique identifier of the client.
        birth_date (date): Birth date of the client.
        contacts (dict): Contact information like phone and email.
        account_ids (list): List of associated bank account IDs.
        status (str): Current status of the client. Defaults to active.
    """
    def __init__(self, 
                 fio: str, 
                 client_id: str, 
                 birth_date: date, 
                 contacts: dict):
        self.fio = fio
        self.client_id = client_id
        self.birth_date = birth_date
        self.contacts = contacts  # {"phone": "...", "email": "..."}
        self.account_ids = []
        self.status = "active"
    
    def is_adult(self, today: date = None) -> bool:
        """
        Determines if the client is
        at least 18 years old for the date.

        Args:
            today (date, optional): The date to compare against.
                Defaults to current date.

        Returns:
            bool
        """
        if today is None:
            today = date.today()
        
        # Calc full years: today >= birth date + 18 years?
        years_difference = today.year - self.birth_date.year
        
        # If bday has not raeched yet this year — -1 year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years_difference -= 1

        return years_difference >= 18


    def add_account(self, account_id: str):
        """
        Adds a bank account ID to the
        client's list of associated accounts.

        Args:
            account_id (str): account ID to add.
        """
        self.account_ids.append(account_id)


    def remove_account(self, account_id: str):
        """
        Removes a bank account ID from the
        client's list if present.

        Args:
            account_id (str): account ID to remove.
        """
        if account_id in self.account_ids:
            self.account_ids.remove(account_id)


    def __str__(self):
        return {
            "client": self.fio,
            "id": self.client_id, 
            "status": self.status, 
            "accounts": len(self.account_ids)
        }


class Bank:
    """
    Bank system managing clients, accounts, authentication,
    and account operations.

    Attributes:
        clients (Dict[str, Client]): Mapping of client IDs to Client objects.
        accounts (Dict[str, BankAccount]): Mapping of account IDs.
        failed_logins (Dict[str, int]): Tracking failed 
            login attempts per client.
        blocked_clients (set): Set of client IDs who are blocked.
        suspicious_actions (set): Set of tuples marking 
            suspicious activity (client_id, reason).
    """
    def __init__(self):
        self.clients: Dict[str, Client] = {}  # client_id: Client
        self.accounts: Dict[str, BankAccount] = {}  # account_id: BankAccount
        self.failed_logins: Dict[str, int] = {}  # client_id: int
        self.blocked_clients = set()
        self.suspicious_actions = set()


    def _check_time_restriction(self):
        """
        Internal method to enforce operation time restrictions.

        Raises:
            Exception: If current time is 
                between 00:00 and 05:00 (operations restricted).
        """
        now = datetime.now().time()
        if time(0, 0) <= now < time(5, 0):
            raise Exception("Operations restricted from 00:00 to 05:00")


    def add_client(self, fio: str, birth_date: date, contacts: dict):
        """
        Registers a new client after validating age.

        Args:
            fio (str): Full name of the client.
            birth_date (date): Client's birth date.
            contacts (dict): Contact details.

        Raises:
            ValueError: If the client is under 18 years old.

        Returns:
            str: The generated client ID.
        """
        client_id = str(uuid.uuid4())
        client = Client(fio, client_id, birth_date, contacts)
        if not client.is_adult():
            raise ValueError("Client must be at least 18 years old")
        self.clients[client_id] = client
        print(f"Added client {fio} with ID {client_id}")
        return client_id


    def open_account(self, client_id: str, account_instance: BankAccount):
        """
        Opens a new bank account associated with a client.

        Args:
            client_id (str): The client's unique identifier.
            account_instance (BankAccount): Bank account instance to open.

        Raises:
            Exception: If operations are attempted during restricted hours,
                or client is blocked.
            KeyError: If the client does not exist.

        Returns:
            str: opened account ID.
        """
        self._check_time_restriction()
        if client_id in self.blocked_clients:
            raise Exception("Client is blocked, operations declined")
        if client_id not in self.clients:
            raise KeyError("Client not found")
        # Checking client status
        client = self.clients[client_id]
        if client.status != "active":
            raise Exception("Client status not valid to open an account")

        # Connecting account with a client
        account_id = account_instance.account_id
        self.accounts[account_id] = account_instance
        client.add_account(account_id)
        print(f"Opened an account {account_id} for client {client.fio}")
        return account_id


    def close_account(self, client_id: str, account_id: str):
        """
        Closes an existing bank account if it belongs to the specified client.

        Args:
            client_id (str): The client's unique identifier.
            account_id (str): The account ID to close.

        Raises:
            Exception: If account does not belong
                to client or other validation fails.
            KeyError: If the account does not exist.
        """
        self._check_time_restriction()
        if account_id not in self.accounts:
            raise KeyError("Account not found")
        account = self.accounts[account_id]
        if account.status == "closed":
            print("Account already closed")
            return
        # Checking if account belongs to a client
        client = self.clients.get(client_id)
        if client is None or account_id not in client.account_ids:
            raise Exception("Account does not belong to client")

        account.change_status("closed")
        client.remove_account(account_id)
        print(f"Account {account_id} closed.")


    def freeze_account(self, account_id: str):
        """
        Freezes a bank account, preventing transactions.

        Args:
            account_id (str): The account ID to freeze.

        Raises:
            KeyError: If the account does not exist.
        """
        self._check_time_restriction()
        if account_id not in self.accounts:
            raise KeyError("Account not found")
        account = self.accounts[account_id]
        account.change_status("frozen")
        print(f"Account {account_id} frozen.")


    def unfreeze_account(self, account_id: str):
        """
        Unfreezes a previously frozen bank account.

        Args:
            account_id (str): The account ID to unfreeze.

        Raises:
            KeyError: If the account does not exist.
        """
        self._check_time_restriction()
        if account_id not in self.accounts:
            raise KeyError("Account not found")
        account = self.accounts[account_id]
        if account.status != "frozen":
            print("Account is not frozen")
            return
        account.change_status("active")
        print(f"Account {account_id} unfreezed.")


    def authenticate_client(self, client_id: str):
        """
        Authenticates a client for system access.

        Args:
            client_id (str): The client's unique identifier.

        Raises:
            Exception: If the client is blocked due
                to multiple failed login attempts.
        """
        if client_id in self.blocked_clients:
            raise Exception(
                "The client is blocked after several unsuccessful login attempts."
            )

        self.failed_logins[client_id] = 0
        print(f"The client {client_id} successfully authenticated")


    def failed_login_attempt(self, client_id: str):
        """
        Logs a failed login attempt and blocks the client after 3 failures.

        Args:
            client_id (str): The client's unique identifier.
        """
        count = self.failed_logins.get(client_id, 0) + 1
        self.failed_logins[client_id] = count
        if count >= 3:
            self.blocked_clients.add(client_id)
            print(f"Client {client_id} blocked after 3 failed login attempts")
        else:
            print(f"Failed login attempt for client {client_id}. "
                  f"Attempts: {count}")


    def search_accounts(self, client_id=None, status=None):
        """
        Searches for accounts filtered by client ID and/or account status.

        Args:
            client_id (str, optional): Filter by client ID.
            status (str, optional): Filter by account status.

        Returns:
            list: List of BankAccount objects.
        """
        results = []
        for acc_id, acc in self.accounts.items():
            if client_id is not None:
                client = self.clients.get(client_id)
                if client is None or acc_id not in client.account_ids:
                    continue
            if status is not None and acc.status != status:
                continue
            results.append(acc)
        return results


    def get_total_balance(self):
        """
        Calculates the total balance across all active accounts.

        Returns:
            int: Sum of balances of active accounts.
        """
        total = 0
        for acc in self.accounts.values():
            if acc.status == "active":
                total += acc.acc_balance
        return total


    def get_clients_ranking(self):
        """
        Creates a ranking of clients sorted
        by total active account balance descending.

        Returns:
            list of tuples: Each tuple contains (Client, total_balance)
        """
        ranking = []
        for client_id, client in self.clients.items():
            total_bal = 0
            for acc_id in client.account_ids:
                acc = self.accounts.get(acc_id)
                if acc and acc.status == "active":
                    total_bal += acc.acc_balance
            ranking.append((client, total_bal))
        # Descending sorting
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking


    def mark_suspicious_action(self, client_id: str, reason: str):
        """
        Marks a client's activity as suspicious for further review.

        Args:
            client_id (str): The client's unique identifier.
            reason (str): Description of the suspicious behavior.
        """
        self.suspicious_actions.add((client_id, reason))
        print(f"Suspicious activity by client {client_id}: {reason}")