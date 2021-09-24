import tkinter as tk 
from tkinter import messagebox
# import PyPDF2
import pandas as pd 
import  xmlrpc.client
from datetime import datetime
import json
import sys
from dateutil.relativedelta import relativedelta
from dateutil import tz
import requests
import pytz
import os
from functools import partial  
# from tkinter import *
import paramiko
import io
import base64



root = tk.Tk()
root.title("Download CSV")
# url = 'http://localhost:8069/'
# db = 'quikhr_safr_staging_12_07_2021'
# username = 'admin'
# password = 'qhradmin@123'





def cron_safr_att_csv_gen():
    url = url1.get()
    db = db_name1.get()
    username = username1.get()
    password = password1.get()
    print(url,db,username,password)
    print(url+'common')
    common = xmlrpc.client.ServerProxy(url+'xmlrpc/2/common')
    output = common.version()
    print('details..',output)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(url+'xmlrpc/2/object')
    ids = models.execute_kw(db, uid, password,
    'safr.credentials', 'search',
    [[]],)







    # cron import data
    # models.execute_kw(db, uid, password,
    # 'hr.attendance.import', 'cron_import_data',[[]],)
    # # ['read'], {'raise_exception': False})





    data = models.execute_kw(db, uid, password, 
    'safr.credentials', 'read',
    [ids],{'fields': ['account_id_safr', 'password_safr', 'non_safr_cloud_deploy','safr_dir','event_url','csv_dir']})

    safr_ids = models.execute_kw(db, uid, password,
    'hr.employee', 'search',
    [[]],)

    data2 = models.execute_kw(db, uid, password,
    'hr.employee', 'read',
    [safr_ids],{'fields': ['person_id','emp_code']})
    print(data2)

    safr_dir = listToString([i['safr_dir'] for i in data ])
    safr_account_id = listToString([i['account_id_safr'] for i in data ])
    safr_password =  listToString([i['password_safr'] for i in data ])
    col_names = [
			'date',
			'EmpCode',
			'InTime(HH:MM)',
			'OutTime(HH:MM)',
			'BiometricDate'
		]

    df = pd.DataFrame(columns=col_names)
    since_date = since_date1.get()
    
    print(since_date)
    url = False
    try:
        for each_person in data2:
            if since_date:
                since_timestamp = int(datetime.strptime(
						since_date, '%d/%m/%Y').replace(tzinfo=tz.gettz('Asia/Kolkata')).timestamp() * 1000)
            person_id = each_person['person_id']
            if person_id:
                headers = {
						'accept': 'application/json;charset=UTF-8',
						'X-RPC-DIRECTORY': safr_dir if safr_dir else 'main',
						'X-RPC-AUTHORIZATION': str(safr_account_id)+':'+str(safr_password),
					}
                params = (('combineActiveEvents', 'false'),
						('personId', str(person_id)),
						('rootEventsOnly', 'true'),
						('sinceTime', since_timestamp),
						('spanSources', 'false'),)

                response=requests.get(url if url else 'https://cv-event.real.com/events', headers=headers, params=params)
                print(response)
                print(response.text)
                if response.text:
                    dict_response = json.loads(response.text)
                else:
                    continue
                if not dict_response:
                    continue
                list_events=dict_response.get('events')
                if not type(list_events) == list:
                    continue
                for each_event in list_events:
                    start_date =  datetime.fromtimestamp(int(each_event.get('startTime')/1000),pytz.timezone("Asia/Kolkata")).date()
                    index_list = (df.index[(df['date'] == start_date.strftime("%d-%m-%Y")) & (df['EmpCode'] == each_person['emp_code'])].tolist())
                    if index_list and each_person:
                        index = index_list.pop()
                        df.at[index,'OutTime(HH:MM)']= datetime.fromtimestamp(int(each_event.get('startTime')/1000),pytz.timezone("Asia/Kolkata")).strftime('%H:%M')
                    elif each_person:
                        df = df.append({
                        'date':start_date.strftime("%d-%m-%Y"),
                        'EmpCode':each_person['emp_code'],
                        'InTime(HH:MM)':datetime.fromtimestamp(int(each_event.get('startTime')/1000),pytz.timezone("Asia/Kolkata")).strftime('%H:%M'),
                        'OutTime(HH:MM)':datetime.fromtimestamp(int(each_event.get('startTime')/1000),pytz.timezone("Asia/Kolkata")).strftime('%H:%M'),
                        'BiometricDate':'t'
                        },ignore_index = True)
        csv_dir = csv_dir_local.get()
        df.to_csv(os.path.join(csv_dir,'exportattendance.csv') if csv_dir else '/home/user/workspace/attendance/exportattendance.csv', encoding='utf-8', index=False)

    except Exception as e:
        print(e,'line number of error'.format(sys.exc_info()[-1].tb_lineno))




def file_send_to_server():
    try: 
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh.connect(hostname='192.168.0.16',username='odoouser',password='root@123')
        print(QuikHR_Server_Password.get(),QuikHR_Server_Username.get(),QuikHR_server_hostname.get())
        ssh.connect(hostname=QuikHR_server_hostname.get(),username=QuikHR_Server_Username.get(),password=QuikHR_Server_Password.get())
        sftp_client = ssh.open_sftp()
        print(csv_dir_local.get()+'/exportattendance.csv')
        print(csv_dir_server.get()+'exportattendance.csv')
        sftp_client.put(csv_dir_local.get()+'/exportattendance.csv',csv_dir_server.get()+'/exportattendance.csv')
        sftp_client.close()
        ssh.close()

        url = url1.get()
        db = db_name1.get()
        username = username1.get()
        password = password1.get()
        print(url,db,username,password)
        print(url+'common')
        common = xmlrpc.client.ServerProxy(url+'xmlrpc/2/common')
        output = common.version()
        print('details..',output)
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(url+'xmlrpc/2/object')
       # cron import data
        models.execute_kw(db, uid, password,
        'hr.attendance.import', 'cron_import_data',[[]],)
        # # ['read'], {'raise_exception': False})

    except Exception as e:
        print(e)

def update_personid():
    try:
        url = url1.get()
        db = db_name1.get()
        username = username1.get()
        password = password1.get()
        print(url,db,username,password)
        print(url+'common')
        common = xmlrpc.client.ServerProxy(url+'xmlrpc/2/common')
        output = common.version()
        print('details..',output)
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(url+'xmlrpc/2/object')

        ids = models.execute_kw(db, uid, password,
        'hr.employee', 'search',
        [[['person_id','=','']]],)
        print(ids)
        safr_ids = models.execute_kw(db, uid, password,
        'safr.credentials', 'search',
        [[]],)
        data = models.execute_kw(db, uid, password, 
        'safr.credentials', 'read',
        [safr_ids],{'fields': ['account_id_safr', 'password_safr', 'non_safr_cloud_deploy','safr_dir','event_url','csv_dir']})
        safr_dir = listToString([i['safr_dir'] for i in data ])
        safr_account_id = listToString([i['account_id_safr'] for i in data ])
        safr_password =  listToString([i['password_safr'] for i in data ])


        data2 = models.execute_kw(db, uid, password,
        'hr.employee', 'read',
        [ids],{'fields': ['person_id','emp_code','face_img','name','image']})
        print(data2)
        for i in data2:
            person_id = i['person_id']
            print('person id is blank',i['emp_code'],i['name'])
            # data_img = io.BytesIO(base64.decodestring(i['face_img']))
            # print(data_img)
            headers = {
            'accept': 'application/json;charset=UTF-8',
            'X-RPC-DIRECTORY': safr_dir if safr_dir else 'main',
            'X-RPC-PERSON-NAME': str(i['name']),
            'X-RPC-AUTHORIZATION': safr_account_id+':'+safr_password,
            'Content-Type': 'image/jpeg',
            'X-RPC-EXTERNAL-ID':str(i['emp_code']),
            }
            params = (
            ('insert', 'true'),
            ('update', 'true'),
            ('update-if-lower-quality', 'false'),
            ('merge', 'true'),
            ('regroup', 'false'),
            ('detect-age', 'false'),
            ('detect-gender', 'false'),
            ('detect-sentiment', 'false'),
            ('detect-occlusion', 'false'),
            ('detect-mask', 'false'),
            ('differentiate', 'false'),
            ('similar_limit', '0'),
            ('linear-match', 'false'),
            ('site', 'default'),
            ('source', 'default'),
            ('provide-face-id', 'true'),
            ('min-cpq', '-1'),
            ('min-fsq', '-1'),
            ('min-fcq', '-1'),
            ('insert-profile', 'false'),
            ('max-occlusion', '-1'),
            ('event', 'none'),
            ('context', 'live'),
            ('type', 'person'),
            ('include-expired', 'false'),
            )
            print('image',i['image'])
            emp_code = i['emp_code']
            print('emp_code',emp_code)
            data_img = io.BytesIO(base64.b64decode(i['image']))
            try:
                response = requests.post('https://covi.real.com/people', headers=headers, params=params, data=data_img)
                dict_response = json.loads(response.text)
                print(dict_response)
                externalIdlist = []
                personIdlist = []
                identifiedFaces = dict_response['identifiedFaces']
                for i in identifiedFaces:
                    externalIdlist.append(i['externalId'])
                    personIdlist.append(i['personId'])

                print(externalIdlist,personIdlist)
                
                personId = listToString(personIdlist)

                print(personId,type(personId))

                print('personId', personId)

                id = models.execute_kw(db, uid, password,
                'hr.employee', 'search',
                [[['emp_code','=',emp_code]]],)
                print(id)
                write = models.execute_kw(db, uid, password, 'hr.employee', 'write', [id, {
                'person_id': personId}])
                print(write)

            except Exception as e:
                print(e)

    except Exception as e:
        print(e)


def listToString(s): 
    str1 = "" 
    for ele in s: 
        str1 += ele    
    return str1  

       
url_label = tk.Label(root ,text = "URL").grid(row = 0,column = 0,padx = 10,pady=10,)
db_name_label = tk.Label(root ,text = "DB Name").grid(row = 1,column = 0,padx = 10,pady=10)
username_label = tk.Label(root ,text = "Username").grid(row = 2,column = 0,padx = 10,pady=10)
password_lable = tk.Label(root ,text = "Password").grid(row = 3,column = 0,padx = 10,pady=10)
since_date_label = tk.Label(root ,text = "Since Date (dd/mm/YYYY)").grid(row = 4,column = 0,padx = 10,pady=10)
csv_dir_local_label = tk.Label(root ,text = "CSV Dir for local").grid(row = 5,column = 0,padx = 10,pady=10)
csv_dir_server_label = tk.Label(root,text='CSV Dir For server').grid(row=6,column=0,padx = 10,pady=10)
url1 = tk.Entry(root,textvariable=1,)
url1.grid(row = 0,column = 1,padx = 10,pady=10,)
db_name1 = tk.Entry(root)
db_name1.grid(row = 1,column = 1,padx = 10,pady=10)
username1 = tk.Entry(root)
username1.grid(row = 2,column = 1,padx = 10,pady=10)
password1 = tk.Entry(root)
password1.grid(row = 3,column = 1,padx = 10,pady=10)
since_date1 = tk.Entry(root)
since_date1.grid(row = 4,column = 1,padx = 10,pady=10)
csv_dir_local = tk.Entry(root)
csv_dir_local.grid(row = 5,column = 1,padx = 10,pady=10)
csv_dir_server = tk.Entry(root)
csv_dir_server.grid(row = 6, column = 1,padx = 10,pady=10)

QuikHR_server_hostname_label = tk.Label(root ,text = "QuikHR Server Hostname / IP").grid(row = 7,column = 0,padx = 10,pady=10,)
QuikHR_Server_Username_label = tk.Label(root ,text = "QuikHR Server Username").grid(row = 8,column = 0,padx = 10,pady=10,)
QuikHR_Server_Password_lable = tk.Label(root ,text = "QuikHR Server Password").grid(row = 9,column = 0,padx = 10,pady=10,)
QuikHR_server_hostname = tk.Entry(root)
QuikHR_server_hostname.grid(row = 7,column = 1,padx = 10,pady=10)
QuikHR_Server_Username = tk.Entry(root)
QuikHR_Server_Username.grid(row = 8,column = 1,padx = 10,pady=10)
QuikHR_Server_Password = tk.Entry(root)
QuikHR_Server_Password.grid(row = 9, column = 1,padx = 10,pady=10)



downloas_csv_button = tk.Button(root, text ="Download CSV", command = cron_safr_att_csv_gen,bg='black',fg='white',padx = 10,pady=10)
send_to_server_button = tk.Button(root, text ="Send To server",command = file_send_to_server,bg='black',fg='white',padx = 10,pady=10)
downloas_csv_button.grid(row=10,column=1) 
send_to_server_button.grid(row=12,column=1)

update_personids_button = tk.Button(root, text ="Update PersonIDs",command = update_personid,bg='black',fg='white',padx = 10,pady=10)
update_personids_button.grid(row=14,column=1)
root.geometry("600x600")

root.mainloop()
