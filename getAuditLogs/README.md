# Get Audit logs

### Prerequisites

* To run this script you need python installed on your machine

### Run script

* Script help

  ```
  python getAuditLogs.py -h
  ```

* Run the script using with all options

  ```
    python getAuditLogs.py -t 10.2.171.30 -u admin -p admin -s 08/01/2020 -e 08/03/2020 -c logs.csv
  ```

* Run the script using default options
  
  ```
    # See the default values using `python getAuditLogs.py -h`
    python getAuditLogs.py 
  ```

* The script will prompt you some questions regarding Cohesity Cluster and other information. 

* Enter the correct values and the script will output a csv file (default is output.csv)

### Have any question

Send me an email chandrashekar.dashudu@cohesity.com