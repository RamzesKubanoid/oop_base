from src.report import ReportBuilder
from src.main import create_bank_with_clients_and_accounts, simulate_transactions


def report_test():
    # Demo
    bank_data = create_bank_with_clients_and_accounts()
    extended_data = simulate_transactions(bank_data)

    report_builder = ReportBuilder(
        bank_data=bank_data,
        transactions=extended_data["transactions"]
    )

    # Text report for client
    print(report_builder.report_client(
        next(iter(bank_data["clients"].keys())))
    )

    # Text report for bank
    print(report_builder.report_bank())

    # Text report for risks
    print(report_builder.report_risks())

    # JSON export client_data
    clients_data = [
        { "id": cid, 
          "fio": c.fio, 
          "birth_date": 
          str(c.birth_date), 
          "contacts": c.contacts }
        for cid, c in bank_data["clients"].items()
    ]
    report_builder.export_to_json(clients_data, "clients.json")

    # CSV export of an account data
    accounts_data = [{
        "account_id": acc.account_id,
        "client_id": acc.owner_data["client_id"],
        "balance": acc.acc_balance,
        "currency": acc.currency,
        "status": acc.status
    } for acc in bank_data["accounts"].values()]
    fieldnames = ["account_id", "client_id", "balance", "currency", "status"]
    report_builder.export_to_csv(accounts_data, fieldnames, "accounts.csv")

    # Saving charts
    report_builder.save_charts()


if __name__ == '__main__':
    report_test()