import os
import logging
import json
import time
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import BIGINT, create_engine, Column, Integer, String, MetaData, DateTime, Float, Text
from sqlalchemy.orm import Session, declarative_base
from secrets_manager import get_secret
from datetime import datetime
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

Base = declarative_base()
db_secret = json.loads(get_secret(
         secret_name=os.environ["RDS_SECRETS_MANAGER_ID"], region_name=os.environ["AWS_REGION"]))

rds_host = os.environ['RDS_HOST']
rds_db_name = os.environ['RDS_DB_NAME']
ods_conn_str = f"mysql+pymysql://{db_secret['username']}:{db_secret['password']}@{rds_host}/{rds_db_name}"

engine = create_engine(ods_conn_str)
session = Session(engine)
meta = MetaData(engine)

class customer_submission(Base):
    __tablename__ = "customer_submission"
    submission_id = Column(String, primary_key=True)
    submission_date = Column(DateTime)
    source_customer_id = Column(String)
    customer_name = Column(String)
    business_unit = Column(String)
    business_segment = Column(String)
    business_subsegment = Column(String)
    program_name = Column(String)
    product_name = Column(String)
    submission_status = Column(String)
    effective_date = Column(DateTime)
    expiration_date = Column(DateTime)

    @classmethod
    def from_dict(cls, d):
        du = {}
        for c in cls.__table__.columns:
            du[c.name] = d[c.name] if c.name in d else getattr(cls, c.name)
        return cls(**du)

class customer_proposal_detail(Base):
    __tablename__ = "customer_proposal_detail"
    proposal_detail_id  = Column(BIGINT, autoincrement=True, primary_key=True)
    submission_id = Column(String)
    proposal_type = Column(String)
    proposal_id = Column(String)
    quote_key = Column(BIGINT)
    source_customer_id = Column(String)
    coverage_code = Column(String)
    customer_name = Column(String)    
    customer_email = Column(String)
    customer_mail_phone_number = Column(String)
    customer_mail_address = Column(String)
    # agency_contact_email = Column(String)
    # agency_contact_full_name = Column(String)
    # source_agency_contact_id = Column(String)
    # source_agency_id = Column(String)
    logged_user_contact_email = Column(String)
    logged_user_contact_full_name = Column(String)
    street = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    country = Column(String)
    total_proposal_premium = Column(Float)
    proposal_status = Column(String)
    pms_status = Column(String)
    is_document_uploaded_manually = Column(String)
    proposal_effective_date = Column(DateTime)
    proposal_expiration_date = Column(DateTime)
    source_system = Column(String)
    override_binding_rules = Column(String)
    county = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    billing_type = Column(String)

    @classmethod
    def from_dict(cls, d):
        du = {}
        for c in cls.__table__.columns:
            du[c.name] = d[c.name] if c.name in d else getattr(cls, c.name)
        return cls(**du)

def query_update_dict(dict, obj):
    d = {}
    for column in obj.__table__.columns:
        if column.name in dict:
            d[column.name] = dict[column.name]
        else:
            d[column.name] = getattr(obj, column.name)
    return d

def get_submission(id=None):
    sql = session.query(customer_submission)
    if id:
        sql = sql.filter(customer_submission.submission_id == id)
    return sql

def get_proposal(id=None):
    sql = session.query(customer_proposal_detail)      
    if id:
        sql = sql.filter(customer_proposal_detail.proposal_id == id)
    
    return sql

def consume(config=None):
    now = datetime.now()
    start_timestamp = datetime.timestamp(now)
    print(f'Processing to DB @ {now} | {datetime.timestamp(now)}')
    try:
        print(config)
        config_dict = config if type(config) is dict else json.loads(str(config))
        submission_id = config_dict['submission_id']
        print(f'submission_id: {submission_id}')
        
        sql_submission = get_submission(id=submission_id)
        
        proposal_detail_dict = config_dict['proposal_detail']
        print(customer_proposal_detail)

        for proposal in proposal_detail_dict:
            proposal['submission_id'] = submission_id
            proposal_dict = proposal if type(proposal) is dict else json.loads(proposal)
            print(proposal_dict)

            proposal_id =  proposal_dict.get("proposal_id")
            quote_key =  proposal_dict.get("quote_key")
            if proposal_id:
                sql_proposal = get_proposal(id=proposal_id)
                proposal_row = sql_proposal.first()
                if proposal_row is None:
                    '''When quote_key is pushed first time, Quoted is updated'''
                    if(quote_key and quote_key.strip()):
                        proposal_dict["pms_status"] = "Quoted"                    
                    session.add(customer_proposal_detail.from_dict(proposal_dict))
                else:
                    '''When quote_key is pushed first time, status is set as Quoted'''
                    db_quote_key = proposal_row.quote_key
                    if((quote_key and quote_key.strip()) and (db_quote_key is None)):
                        proposal_dict["pms_status"] = "Quoted"
                    sql_proposal.update(query_update_dict(obj=customer_proposal_detail, dict=proposal_dict))

        if sql_submission.first() is None:
            session.add(customer_submission.from_dict(config_dict))
        else:
            sql_submission.update(query_update_dict(obj=customer_submission, dict=config_dict))

        session.commit()

        now = datetime.now()
        end_timestamp = datetime.timestamp(now)
        print(f'Processed to DB @ {now} | {datetime.timestamp(now)}')
        return {'execution_time': end_timestamp - start_timestamp}
    except SQLAlchemyError as e:
        print(e)
        session.rollback()
        raise e


def handle(event, context):
    start_time = time.time()
    
    print(engine)
    print(session)
    for record in event['Records']:
        print(record)

        payload = record["body"]
        print(consume(config=payload))

    end_time = time.time()

    return {
        "execution_time_sec": end_time - start_time 
    }

# if __name__ == '__main__':
#     handle({'Records': [{'body': '{"submission_id":"testdec9",\
#  "proposal_detail":[{"submission_id":"testdec9","proposal_id":"test_p_1244","proposal_type":"quote","coverage_code":"GL",\
#  "proposal_status":"","source_customer_id":"17","customer_name":"Zanshin Self Defense Academy",\
# "customer_email":"","agency_contact_email":"","agency_contact_full_name":"katiyar, Ankit ",\
# "source_agency_contact_id":"","state":"TX",\
# "total_proposal_premium":100,"proposal_effective_date":"2022-02-17",\
# "proposal_expiration_date":"2022-02-17","source_system":"Unqork",\
# "override_binding_rules":"","county":"test_county","billing_type":"test_bill","latitude":-70.123,"longitude":179.123456789012456}],\
# "source_customer_id":"18",\
# "customer_name":"Zanshin Self Defense Academy","business_segment":"K&K Sports,\
# Leisure, & Entertainment","business_subsegment":"Mass Merchandising",\
# "business_unit":"K&K Insurance Group Inc.","program_name":"Special Events RPG",\
# "product_name":"Special Events RPG","effective_date":"2022-17-02",\
# "expiration_date":"2022-02-21","submission_date":"2022-02-21","submission_status":"ACTIVE"}'}]}, None)

      