import logging
import os
import re
import sys


logger = logging.getLogger(__name__)

def connect_to_database(database, treedir, script):
    if database.startswith("sqlite://"):
        from sqlite3 import dbapi2 as sqlite
        db_connection = sqlite.connect(os.path.relpath(database[len("sqlite://"):], treedir))
        datetime_now = "datetime('now')";
        subs="?"
        
    elif database.startswith("mysql://"): #mysql://<mysql_user>:<mysql_password>@localhost/<mysql_database>
        import pymysql
        match = re.match(r'mysql://([^:]+):([^@]*)@([^/]+)/([^?]*)', database.strip())
        if match.group(2) == '':
            #enter password on the command line, if not given (more secure)
            if script:
                pw = input("pw: ")
            else:
                from getpass import getpass
                pw = getpass("Enter the sql database password: ")
        else:
            pw = match.group(2)
        db_connection = pymysql.connect(user=match.group(1), passwd=pw, host=match.group(3), db=match.group(4), port=3306, charset='utf8mb4')
        datetime_now = "NOW()"
        diff_minutes=lambda a,b: 'TIMESTAMPDIFF(MINUTE,{},{})'.format(a,b)
        subs="%s"
    else:
        logger.error("No recognized database specified: {}".format(database))
        sys.exit()
    
    return db_connection, datetime_now, subs

def read_configuration_file(default_appconfig_file, database, EOL_API_key):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), default_appconfig_file)) as conf:
        conf_type = None
        for line in conf:
            # Look for [db] line, followed by uri
            m = re.match(r'\[([^]]+)\]', line)
            if m:
                conf_type = m.group(1)
            if conf_type == 'db' and database is None:
                m = re.match('uri\s*=\s*(\S+)', line)
                if m:
                    database = m.group(1)
            elif conf_type == 'api' and EOL_API_key is None:
                m = re.match('eol_api_key\s*=\s*(\S+)', line)
                if m:
                    EOL_API_key = m.group(1)
    return database, EOL_API_key
