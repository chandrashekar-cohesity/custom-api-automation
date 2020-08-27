import argparse
import requests
import urllib3
import time
import json
import csv
import math
import datetime
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.add_stderr_logger()

def valid_date(s):
    """
    Validate the function to be in the correct date-time format
    """
    try:
        return datetime.datetime.strptime(s, '%m/%d/%Y').date().strftime('%m/%d/%Y')
        #return datetime.datetime.date().strftime('%m/%d/%Y')
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def request(method, path=None, data=None, params=None, uri=None, auth=None, content_type="application/json", accept="application/json"):
    headers = {}
    if token:
        headers['Authorization'] = "Bearer " + token
    if auth:
        headers['Authorization'] = auth
    if content_type:
        headers['Content-Type'] = content_type
    if path:
        uri = cluster_ip_or_fqdn+path
    if data:
        payload = json.dumps(data)  
    else:
        payload = None
    if params:
        params=params

    
    r = requests.request(method, uri, headers=headers,params=params,
                         data=payload, verify=False)
    
    if 200 <= r.status_code <= 299:
        return r

    raise Exception(
        "Unsupported HTTP status code (%d) encountered" % r.status_code)

def get_token(username, org, password):
    data = {
        "password": password,
        "username": username,
        "domain": org
    } 
    r = request('POST', 'public/accessTokens', data=data)
    global token
    token = json.loads(r.content)['accessToken']

def get_all_logs_count():
    params = {
        "endTimeUsecs": epoch_end_date,
        "startTimeUsecs": epoch_start_date
    } 
    r = request('GET','public/auditLogs/cluster', params=params)
    logs = json.loads(r.content)
    return logs['totalCount']

def get_logs(start_index):
    params = {
        "endTimeUsecs": epoch_end_date,
        "startTimeUsecs": epoch_start_date,
        "startIndex": start_index,
    } 
    r = request('GET','public/auditLogs/cluster', params=params)
    logs = json.loads(r.content)
    cluster_audit_logs = logs['clusterAuditLogs']
    for logs in cluster_audit_logs:
        temp_log = {}
        #temp_log["tenantName"] = logs.get["tenant"]["name"] # This field is not present in 6.3.1
        temp_log["timeStamp"] = logs.get("humanTimestamp")
        temp_log[ "userName"] = logs.get("userName")
        temp_log[ "domain"] = logs.get("domain")
        temp_log[ "action"] = logs.get("action")
        temp_log[ "entityName"] = logs.get("entityName")
        temp_log[ "entityType"] = logs.get("entityType")
        temp_log[ "entityId"] = logs.get("entityId")
        temp_log[ "details"] = logs.get("details")
        temp_log[ "ip"] = logs.get("ip")
        temp_log["clusterInfo"] = logs.get("clusterInfo")
        temp_log[ "previousRecord"] = logs.get("previousRecord")
        temp_log[ "newRecord"] = logs.get("newRecord")
        master_list.append(temp_log.copy())

def convert_to_csv(dict_array, output_file_name):
    keys = ["timeStamp", "userName", "domain", "action", "entityName", "entityType", "entityId", "details", "ip","clusterInfo", "previousRecord", "newRecord" ]
    with open(output_file_name, 'a') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(dict_array)
    print("Wrote a file "+ output_file_name + " in current directory")


token = None

# cluster_endpoint = raw_input("Enter your cluster FQDN or IP : ")
# username = raw_input("Enter your cluster username(admin) : ") or "admin"
# password = raw_input("Enter your cluster password(admin) : ") or "admin"
# org = raw_input("Enter your cluster org name(LOCAL) : ") or "LOCAL"
# filename = raw_input("Enter the CSV file name(AuditLogs.csv) : ") or "AuditLogs"

date_now = datetime.datetime.now().date().strftime('%m/%d/%Y')
thirty_days_before_now = (datetime.datetime.now() - datetime.timedelta(30)).date().strftime('%m/%d/%Y')


parser = argparse.ArgumentParser()
parser.add_argument('-t', '--target', default='localhost', help='IP address of the target machine in cluster. Defaults to localhost')
parser.add_argument('-u', '--username', default='admin', help='Username. Defaults to admin')
parser.add_argument('-p', '--password', default='admin', help='Password. Defaults to admin')
parser.add_argument('-c', '--csvfile', default='output.csv', help='CSV output filename. Defaults to output.csv)')
parser.add_argument('-s', '--startdate',default=thirty_days_before_now,help='Start date for runs. Format mm/dd/yyyy. Defaults to 30 before days from today', type=valid_date)
parser.add_argument('-e', '--enddate', default=date_now, help='End date for logs(has to be after startdate if provided). Format mm/dd/yyyy. Defaults to today', type=valid_date)

args = parser.parse_args()
cluster_endpoint = str(args.target)
username = str(args.username)
password = str(args.password)
filename = str(args.csvfile)
start_date_input = str(args.startdate)
end_date_input = str(args.enddate)

date_now = datetime.datetime.now().date().strftime('%m/%d/%Y')
date_now_epoch = time.mktime(datetime.datetime.now().timetuple())*1000000.0

print("###NOTE: The results ")
epoch_start_date_input = '{:f}'.format((((datetime.datetime(int(start_date_input.split('/')[2]),int(start_date_input.split('/')[0]),int(start_date_input.split('/')[1])) - datetime.datetime(1970,1,1)).total_seconds())*1000000.0))
epoch_end_date_input = '{:f}'.format((((datetime.datetime(int(end_date_input.split('/')[2]),int(end_date_input.split('/')[0]),int(end_date_input.split('/')[1]), 23,59) - datetime.datetime(1970,1,1)).total_seconds())*1000000.0))

epoch_start_date = epoch_start_date_input.split('.')[0] 
epoch_end_date = epoch_end_date_input.split('.')[0]

cluster_ip_or_fqdn = "https://" + cluster_endpoint +"/irisservices/api/v1/"

get_token(username, 'LOCAL', password)
total_logs = get_all_logs_count()
start_index = 0
master_list = []
for i in range(0,10000, 1000):
    get_logs(i)
    if(len(master_list) >= total_logs):
        break
    
convert_to_csv(master_list, filename)
    
    

