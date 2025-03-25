import boto3

def get_session(profile_name):
    return boto3.Session(profile_name=profile_name)

def get_account_id(session):
    return session.client('sts').get_caller_identity()['Account']
