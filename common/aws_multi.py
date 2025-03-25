from .aws_accounts import accounts
from .aws_session import get_session, get_account_id

def with_all_accounts(callback):
    results = []
    for account in accounts:
        session = get_session(account['profile'])
        account_id = get_account_id(session)
        results.extend(callback(session, account_id, account['name']))
    return results
