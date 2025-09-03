FROM docker-dev-local.repo.eap.aon.com/affinity/python-lambda:3.8

#Red Hat Enterprise Server 8 and Oracle Linux 8
RUN curl https://packages.microsoft.com/config/rhel/8/prod.repo > /etc/yum.repos.d/mssql-release.repo

RUN ACCEPT_EULA=Y yum install -y msodbcsql17

COPY requirements.txt ./
RUN python3 -m pip install --upgrade -r requirements.txt

COPY src/*.py ./

CMD ["handler.handle"]