
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

def get_all_jobs():
    job_name_list = []
    r = request('GET','public/protectionJobs')
    jobs = json.loads(r.content)
    for job in jobs:
        if("_DELETED" not in job['name']):
            job_name_list.append(job['name'])
    return job_name_list

def get_protection_id_by_name(job_name):
    params = {'names': job_name}
    r = request('GET','public/protectionJobs', params=params)
    jobs = json.loads(r.content)
    jobId = jobs[0]['id']
    return jobId


def get_protection_runs(name, startTimeUsecs=1554184800000000, endTimeUsecs=1588316399999000, runTypes="kAll", excludeTasks="true", allUnderHierarchy="true", onlyReturnDataMigrationJobs="true"):
    jobId = get_protection_id_by_name(name)
    params = {
        'allUnderHierarchy':allUnderHierarchy,
        'endTimeUsecs':endTimeUsecs,
        'excludeTasks':excludeTasks,
        'numRuns': 1000,
        'id':jobId,
        'onlyReturnDataMigrationJobs': onlyReturnDataMigrationJobs,
        'runTypes': runTypes,
        'startTimeUsecs':startTimeUsecs
        
    }
    r = request('GET','backupjobruns', params=params )
    all_runs_list = json.loads(r.content)
    all_runs = all_runs_list[0]['backupJobRuns']['protectionRuns']
    start_time_list = []
    for i in all_runs:
        if(i['backupRun']['base']['publicStatus'] == 'kFailure'):
            pass
        else:
            start_time_list.append(str(i['backupRun']['base']['startTimeUsecs']))
    
    return jobId, start_time_list



def get_archival_backup_details(start_time_list, jobId, job_name):
    desired_list = []
    datetimeFormat = '%m-%d-%Y %H:%M:%S'

    for i in start_time_list:
        output = {}
        params = {
            'allUnderHierarchy':'true',
            'exactMatchStartTimeUsecs':i,
            'excludeTasks':'true',
            'id':jobId
        }
        r = request('GET','backupjobruns', params=params )
        runDetails = json.loads(r.content)
        output['protection_job_name'] = job_name
        output['job_run_ID'] = runDetails[0]['backupJobRuns']['protectionRuns'][0]['copyRun']['jobInstanceId']
        
        output['backup_status'] = runDetails[0]['backupJobRuns']['protectionRuns'][0]['copyRun']['finishedTasks'][0]['publicStatus']
        if(output['backup_status'] == 'kSuccess'):
            output['backup_starttime'] = time.strftime('%m-%d-%Y %H:%M:%S', time.localtime((runDetails[0]['backupJobRuns']['protectionRuns'][0]['copyRun']['finishedTasks'][0]['startTimeUsecs'])/1000000.))
            output['backup_endtime'] = time.strftime('%m-%d-%Y %H:%M:%S', time.localtime((runDetails[0]['backupJobRuns']['protectionRuns'][0]['copyRun']['finishedTasks'][0]['endTimeUsecs'])/1000000.))
            output['backup_expiry_date'] = time.strftime('%m-%d-%Y %H:%M:%S',  time.localtime((runDetails[0]['backupJobRuns']['protectionRuns'][0]['copyRun']['finishedTasks'][0]['expiryTimeUsecs'])/1000000.))
            days_to_expire = (datetime.datetime.strptime(output['backup_expiry_date'], datetimeFormat) - datetime.datetime.strptime(datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S'), datetimeFormat)).days
            if(days_to_expire < 0):
                output['backup_expiry_in_days'] ="Expired"
            else:
                output['backup_expiry_in_days'] = days_to_expire
        else:
            output['backup_starttime'] = "N/A"
            output['backup_endtime'] = "N/A"
            output['backup_expiry_date'] = "N/A"
            output['backup_expiry_in_days'] = "N/A"
        
        try:
            archival_obj = runDetails[0]['backupJobRuns']['protectionRuns'][0]['copyRun']['finishedTasks'][1]
            if('archivalInfo' in archival_obj):
                output['archival_status'] = archival_obj['publicStatus']
                if(output['archival_status'] == 'kSuccess'):
                    output['archival_starttime'] = time.strftime('%m-%d-%Y %H:%M:%S', time.localtime((archival_obj['archivalInfo']['startTimeUsecs'])/1000000.))
                    output['archival_endtime'] = time.strftime('%m-%d-%Y %H:%M:%S', time.localtime((archival_obj['archivalInfo']['endTimeUsecs'])/1000000.))
                    output['archival_expiry_date'] = time.strftime('%m-%d-%Y %H:%M:%S',  time.localtime((archival_obj['expiryTimeUsecs'])/1000000.))
                    days_to_expire = (datetime.datetime.strptime(output['archival_expiry_date'], datetimeFormat) - datetime.datetime.strptime(datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S'), datetimeFormat)).days
                    if(days_to_expire < 0):
                        output['archival_expiry_in_days'] ="Expired"
                    else:
                        output['archival_expiry_in_days'] = days_to_expire
                else:
                    output['archival_starttime'] = "N/A"
                    output['archival_endtime'] = "N/A"
                    output['archival_expiry_date'] = "N/A"
                    output['archival_expiry_in_days'] = "N/A"
        except IndexError:
            output['archival_status'] = "N/A"
            output['archival_starttime'] = "N/A"
            output['archival_endtime'] = "N/A"
            output['archival_expiry_date'] = "N/A"
            output['archival_expiry_in_days'] = "N/A"
        
        
        
        
        desired_list.append(output)
    return desired_list

def convert_to_csv(dict_array, job_name):
    keys = dict_array[0].keys()
    with open(job_name + '.csv', 'wb') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(dict_array)
    print("Wrote a file "+ job_name + ".csv in current directory")


token = None

cluster_endpoint = raw_input("Enter your cluster FQDN or IP : ")
username = raw_input("Enter your cluster username(admin) : ") or "admin"
password = raw_input("Enter your cluster password(admin) : ") or "admin"
org = raw_input("Enter your cluster org name(LOCAL) : ") or "LOCAL"
protection_job_name = raw_input("Enter Protection Job Name (all by default): ") or "all"
start_date = raw_input("Enter start date to generate report (mm/dd/yyyy)")
end_date = raw_input("Enter end date to generate report (mm/dd/yyyy)")
print("###NOTE: The results ")
epoch_start_date = '{:f}'.format((((datetime.datetime(int(start_date.split('/')[2]),int(start_date.split('/')[0]),int(start_date.split('/')[1])) - datetime.datetime(1970,1,1)).total_seconds())*1000000.0))
epoch_end_date = '{:f}'.format((((datetime.datetime(int(end_date.split('/')[2]),int(end_date.split('/')[0]),int(end_date.split('/')[1]), 23,59) - datetime.datetime(1970,1,1)).total_seconds())*1000000.0))

#cluster_ip_or_fqdn = "https://sv16-pm-haswell2-p1-vip.pm.cohesity.com/irisservices/api/v1/"
cluster_ip_or_fqdn = "https://" + cluster_endpoint +"/irisservices/api/v1/"
start_time_list=[]
desired_list=[]
get_token(username, 'LOCAL', password)

if(protection_job_name == "all"):
    all_job_names = get_all_jobs()
    for job_name in all_job_names:
        jobId, start_time_list = get_protection_runs(job_name, epoch_start_date.split('.')[0], epoch_end_date.split('.')[0] )
        desired_list = get_archival_backup_details(start_time_list, jobId, job_name)
        convert_to_csv(desired_list, job_name)
else:
    jobId, start_time_list = get_protection_runs(protection_job_name, epoch_start_date.split('.')[0], epoch_end_date.split('.')[0])
    desired_list = get_archival_backup_details(start_time_list, jobId, protection_job_name)
    print(json.dumps(desired_list))
    convert_to_csv(desired_list, protection_job_name)

