import os
import json
import time
import logging
import requests
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, MetaData
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError
from secrets_manager import get_secret

# -------------------
# Logging
# -------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# -------------------
# Database Connection
# -------------------
Base = declarative_base()
db_secret = json.loads(get_secret(
    secret_name=os.environ["RDS_SECRETS_MANAGER_ID"],
    region_name=os.environ["AWS_REGION"]
))

rds_host = os.environ['RDS_HOST']
rds_db_name = os.environ['RDS_DB_NAME']
ods_conn_str = f"mysql+pymysql://{db_secret['username']}:{db_secret['password']}@{rds_host}/{rds_db_name}"

engine = create_engine(ods_conn_str)
session = Session(engine)
meta = MetaData(engine)

# -------------------
# CDM ORM Models
# -------------------
class DFSourceSystem(Base):
    __tablename__ = "df_source_system"
    df_source_system_id = Column(Integer, primary_key=True, autoincrement=True)
    source_system = Column(String)
    name = Column(String)
    created_date = Column(DateTime, default=datetime.utcnow)
    modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DFCustomer(Base):
    __tablename__ = "df_customer"
    df_customer_id = Column(Integer, primary_key=True, autoincrement=True)
    source_customer_id = Column(String)
    customer_name = Column(String)
    created_date = Column(DateTime, default=datetime.utcnow)
    modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DFSubmission(Base):
    __tablename__ = "df_submission"
    df_submission_id = Column(Integer, primary_key=True, autoincrement=True)
    source_submission_id = Column(String)
    df_customer_id = Column(Integer)
    product_id = Column(Integer)
    df_submission_status_id = Column(Integer)
    df_submission_type_id = Column(Integer)
    df_source_system_id = Column(Integer)
    effective_date = Column(DateTime)
    expiration_date = Column(DateTime)
    created_date = Column(DateTime, default=datetime.utcnow)
    modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DFQuote(Base):
    __tablename__ = "df_quote"
    df_quote_id = Column(Integer, primary_key=True, autoincrement=True)
    source_quote_id = Column(String)
    df_submission_id = Column(Integer)
    df_quote_status_id = Column(Integer)
    df_quote_type_id = Column(Integer)
    df_source_system_id = Column(Integer)
    effective_date = Column(DateTime)
    expiration_date = Column(DateTime)
    created_date = Column(DateTime, default=datetime.utcnow)
    modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# -------------------
# Helpers
# -------------------
def fetch_unqork_data(api_url, api_key):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    return response.json()

def consume_unqork(config=None):
    try:
        config_dict = config if isinstance(config, dict) else json.loads(str(config))

        # -------------------
        # Source System
        # -------------------
        source_system = session.query(DFSourceSystem).filter_by(source_system="Unqork").first()
        if not source_system:
            source_system = DFSourceSystem(source_system="Unqork", name="Unqork API")
            session.add(source_system)
            session.commit()

        # -------------------
        # Customer
        # -------------------
        customer = session.query(DFCustomer).filter_by(
            source_customer_id=config_dict["source_customer_id"]
        ).first()
        if not customer:
            customer = DFCustomer(
                source_customer_id=config_dict["source_customer_id"],
                customer_name=config_dict.get("customer_name")
            )
            session.add(customer)
            session.commit()

        # -------------------
        # Submission
        # -------------------
        submission = session.query(DFSubmission).filter_by(
            source_submission_id=config_dict["submission_id"]
        ).first()

        if not submission:
            submission = DFSubmission(
                source_submission_id=config_dict["submission_id"],
                df_customer_id=customer.df_customer_id,
                df_source_system_id=source_system.df_source_system_id,
                effective_date=config_dict.get("effective_date"),
                expiration_date=config_dict.get("expiration_date")
            )
            session.add(submission)
            session.commit()
        else:
            submission.effective_date = config_dict.get("effective_date")
            submission.expiration_date = config_dict.get("expiration_date")
            session.commit()

        # -------------------
        # Quotes (proposal_detail)
        # -------------------
        for proposal in config_dict.get("proposal_detail", []):
            quote = session.query(DFQuote).filter_by(
                source_quote_id=proposal["proposal_id"]
            ).first()

            if not quote:
                quote = DFQuote(
                    source_quote_id=proposal["proposal_id"],
                    df_submission_id=submission.df_submission_id,
                    df_source_system_id=source_system.df_source_system_id,
                    effective_date=proposal.get("proposal_effective_date"),
                    expiration_date=proposal.get("proposal_expiration_date")
                )
                session.add(quote)
            else:
                quote.effective_date = proposal.get("proposal_effective_date")
                quote.expiration_date = proposal.get("proposal_expiration_date")

        session.commit()
        return {"status": "success"}

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"DB Error: {e}")
        raise e


# -------------------
# Lambda Handler
# -------------------
def handle(event, context):
    start_time = time.time()

    api_url = os.environ["UNQORK_API_URL"]
    api_key = os.environ["UNQORK_API_KEY"]

    # unqork_data = fetch_unqork_data(api_url, api_key)

    for record in unqork_data.get("Records", []):
        payload = record["body"]
        consume_unqork(config=payload)

    end_time = time.time()
    return {"execution_time_sec": end_time - start_time}