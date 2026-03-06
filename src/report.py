import json
import csv
import os
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
from src.transaction import TransactionStatus


class ReportBuilder:
    def __init__(self, bank_data, transactions):
        """
        A class to generate reports and
        charts based on bank data and transactions.

        Attributes:
            bank (object): Bank information object extracted from bank_data.
            clients (dict): Dictionary of client objects.
            accounts (dict): Dictionary of account objects.
            transactions (dict): Dictionary of transaction objects.
            reports_dir (str): Path to directory where reports will be saved.
            charts_dir (str): Path to directory where charts will be saved.
        """
        self.bank = bank_data["bank"]
        self.clients = bank_data["clients"]
        self.accounts = bank_data["accounts"]
        self.transactions = transactions

        # Creating reports directory
        self.reports_dir = "reports"
        self.charts_dir = "charts"
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)


    def report_client(self, client_id):
        """
        Generates a textual report for a specific client.

        Args:
            client_id (str): The unique identifier of the client.

        Returns:
            str: Multi-line string report containing client's name,
            birth date, contacts, and details of their accounts.
            If client is not found, returns an error message.
        """
        if client_id not in self.clients:
            return f"Client {client_id} not found."

        client = self.clients[client_id]
        accounts = [
            acc for acc in self.accounts.values() \
            if acc.owner_data["client_id"] == client_id]
        report = [f"Report for client: {client.fio} (ID: {client_id})"]
        report.append(f"Date of birth: {client.birth_date}")
        report.append(f"Contacts: {client.contacts}")
        report.append(f"Accounts ({len(accounts)}):")
        for acc in accounts:
            report.append(
                f" - ID: {acc.account_id}, Balance: {acc.acc_balance} "
                f"{acc.currency}, Status: {acc.status}"
                )

        return "\n".join(report)


    def report_bank(self):
        """
        Generates a summary report for the bank.

        Returns:
            str: String report including bank name, number of clients,
                number of accounts, and the total balance across all accounts.
        """
        report = [
            f"Bank report: {self.bank.name if hasattr(self.bank, 'name') else 'Unnamed Bank'}"]
        report.append(f"Clients: {len(self.clients)}")
        report.append(f"Accounts: {len(self.accounts)}")
        total_balance = sum(acc.acc_balance for acc in self.accounts.values())
        report.append(f"Total bank balalnce: {total_balance}")
        return "\n".join(report)


    def report_risks(self):
        """
        Generates a report on suspicious or error transactions.

        Returns:
            str: String report containing total number of 
                suspicious or failed transactions,
                and the set of client IDs associated with these transactions.
        """
        report = ["Risk report:"]

        # FIX: compare with TransactionStatus,
        # FAILED and CANCELLED are explicitly listed
        errors = [
            txn for txn in self.transactions.values() \
            if txn.status in (TransactionStatus.FAILED, TransactionStatus.CANCELLED)
        ]
        report.append(f"Total suspicious/failed transactions: {len(errors)}")
        risk_clients = set(
            txn.sender_account.owner_data["client_id"] for txn in errors
        )
        report.append(f"Clients with errors: {risk_clients}")
        return "\n".join(report)


    def export_to_json(self, data, filename):
        """
        Exports data to a JSON file in the reports directory.

        Args:
            data (any): Data to be exported to JSON.
            filename (str): Name of the JSON file to create.
        """
        path = os.path.join(self.reports_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"JSON report saved: {path}")


    def export_to_csv(self, data_list, fieldnames, filename):
        """
        Exports a list of dictionaries
        to a CSV file in the reports directory.

        Args:
            data_list (list of dict): 
                List of dictionaries containing the data rows.
            fieldnames (list of str): 
                List of keys corresponding to CSV column headers.
            filename (str): 
                Name of the CSV file to create.
        """
        path = os.path.join(self.reports_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for data in data_list:
                writer.writerow(data)
        print(f"CSV report saved: {path}")


    def save_charts(self):
        """
        Generates and saves multiple chart
        images summarizing clients and accounts data.

        Calls internal methods to create specific charts:
          - Pie chart of top clients by transaction volume.
          - Bar chart of number of accounts per client.
          - Line chart of balance movement for a client.
        """
        self._pie_chart_clients_transaction_volume()
        self._bar_chart_accounts_per_client()
        self._balance_movement_chart_for_client()


    def _pie_chart_clients_transaction_volume(self):
        """
        Creates and saves a pie chart showing
        the top 10 clients by outgoing transaction volume.

        The chart image is saved into the
        charts directory as "top_clients_pie.png".
        """
        # from collections import Counter

        client_sums = Counter()
        for txn in self.transactions.values():
            client_id = txn.sender_account.owner_data["client_id"]
            client_sums[client_id] += txn.amount

        labels = []
        sizes = []
        for client_id, total in client_sums.most_common(10):
            labels.append(self.clients[client_id].fio)
            sizes.append(total)

        plt.figure(figsize=(8, 6))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%')
        plt.title("Top 10 clients by outgoing transaction volume")
        chart_file = os.path.join(self.charts_dir, "top_clients_pie.png")
        plt.savefig(chart_file)
        plt.close()
        print(f"Pie chart saved: {chart_file}")


    def _bar_chart_accounts_per_client(self):
        """
        Creates and saves a bar chart showing
        the number of accounts each client owns.

        The chart image is saved into the
        charts directory as "accounts_per_client_bar.png".
        """
        # from collections import Counter

        counts = Counter(
            acc.owner_data["client_id"] for acc in self.accounts.values()
        )
        labels = [self.clients[cid].fio for cid in counts.keys()]
        values = list(counts.values())

        plt.figure(figsize=(10, 6))
        plt.bar(labels, values)
        plt.xticks(rotation=45, ha='right')
        plt.title("Accounts number per client")
        plt.tight_layout()
        chart_file = os.path.join(
            self.charts_dir, "accounts_per_client_bar.png"
        )
        plt.savefig(chart_file)
        plt.close()
        print(f"Barchart saved: {chart_file}")


    def _balance_movement_chart_for_client(self, client_id=None):
        """
        Creates and saves a line chart of balance
        movement over time for a specified client.
        If client_id is None, the first client in the data is used.

        The chart image is saved into the charts directory named
        "balance_movement_client_{client_id}.png".

        Args:
            client_id (str, optional): 
                The unique identifier of the client to generate the chart for.
        """
        if client_id is None:
            # If client_id is None, the first client in the data is used.
            client_id = next(iter(self.clients))

        client_txns = [txn for txn in self.transactions.values()
                       if txn.sender_account.owner_data["client_id"] == client_id
                       or txn.receiver_account.owner_data["client_id"] == client_id]

        # Sort by date
        client_txns.sort(
            key=lambda x: x.created_at if hasattr(x, "created_at") else datetime.min
        )

        balance = 0
        dates = []
        balances = []

        # Initial balance of the first account of a client
        accounts = [acc for acc in self.accounts.values() if \
                    acc.owner_data["client_id"] == client_id]
        if not accounts:
            print("Client has no funds to visualise.")
            return
        balance = sum(acc.acc_balance for acc in accounts)

        for txn in client_txns:
            dates.append(
                txn.created_at if hasattr(txn, "created_at") else datetime.now()
            )
            if txn.sender_account.owner_data["client_id"] == client_id:
                balance -= txn.amount
            if txn.receiver_account.owner_data["client_id"] == client_id:
                balance += txn.amount
            balances.append(balance)

        plt.figure(figsize=(10, 6))
        plt.plot(dates, balances, marker='o')
        plt.title(
            f"Balance movement of client {self.clients[client_id].fio}"
        )
        plt.xlabel("Date")
        plt.ylabel("Balance")
        plt.grid(True)
        plt.tight_layout()
        file_path = os.path.join(
            self.charts_dir, f"balance_movement_client_{client_id}.png"
        )
        plt.savefig(file_path)
        plt.close()
        print(f"Balance movement chart saved: {file_path}")