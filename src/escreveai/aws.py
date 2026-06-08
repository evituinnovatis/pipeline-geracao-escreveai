from typing import Optional

import boto3
from botocore.client import BaseClient
from boto3.session import Session


def criar_sessao_aws(
    region_name: str,
    profile_name: Optional[str] = None,
) -> Session:
    if profile_name:
        return boto3.Session(
            profile_name=profile_name,
            region_name=region_name,
        )

    return boto3.Session(region_name=region_name)


def criar_s3_client(
    region_name: str,
    profile_name: Optional[str] = None,
) -> BaseClient:
    session = criar_sessao_aws(
        region_name=region_name,
        profile_name=profile_name,
    )
    return session.client("s3")

