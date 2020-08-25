
import requests
import urllib3
import time
import json
import csv
import math
import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.add_stderr_logger()

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

def convert_to_csv(dict_array, job_name):
    
    keys = ["timeStamp", "userName", "domain", "action", "entityName", "entityType", "entityId", "details", "ip","clusterInfo", "previousRecord", "newRecord" ]
    with open(job_name + '.csv', 'a') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(dict_array)
    print("Wrote a file "+ job_name + ".csv in current directory")


token = None

cluster_endpoint = raw_input("Enter your cluster FQDN or IP : ")
username = raw_input("Enter your cluster username(admin) : ") or "admin"
password = raw_input("Enter your cluster password(admin) : ") or "admin"
org = raw_input("Enter your cluster org name(LOCAL) : ") or "LOCAL"

date_now = datetime.datetime.now().date().strftime('%m/%d/%Y')
date_now_epoch = time.mktime(datetime.datetime.now().timetuple())*1000000.0
start_date_input = raw_input("Enter start date to generate report(mm/dd/yyyy)") 
end_date_input = raw_input("Enter end date to generate report (mm/dd/yyyy)")

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
    
convert_to_csv(master_list, "Auditlogs")
    
    

