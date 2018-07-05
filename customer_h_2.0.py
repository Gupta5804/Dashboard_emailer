import requests
import json
import pandas as pd
from datetime import date,time,datetime,timedelta
from openpyxl import load_workbook
import itertools
import math
import io
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def export_csv(df):
    with io.StringIO() as buffer:
        df.to_csv(buffer)
        return buffer.getvalue()

def export_excel(df):
    with io.BytesIO() as buffer:
        writer = pd.ExcelWriter(buffer)
        df.to_excel(writer)
        writer.save()
        return buffer.getvalue()

book = load_workbook('Projections.xlsx')
writer = pd.ExcelWriter("Projections.xlsx", engine='openpyxl')
writer.book = book
writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
auth_token_hiya="fc3ed86b62485a2b9a6a680477ea7e60"
auth_token_rawble="e8253e7e6017303a54f57ce28b9d209a"
organization_id_hiya="654806043"
organization_id_rawble = "667580392"
base_url = "https://books.zoho.com/api/v3"
end_points = {'invoices':'/invoices','crm':'/crm','contacts':'/contacts','account':'/account','bills':'/bills'}



#column names = ['ach_payment_initiated', 'adjustment', 'balance', 'cf_buyer_order_date', 'cf_buyer_order_number', 'cf_delivery_type_1', 'client_viewed_time', 'company_name', 'created_time', 'currency_code', 'currency_id', 'current_sub_status', 'current_sub_status_id', 'custom_field_hash', 'custom_fields', 'customer_id', 'customer_name', 'date', 'documents', 'due_date', 'due_days', 'exchange_rate', 'has_attachment', 'invoice_id', 'invoice_number', 'is_emailed', 'is_viewed_by_client', 'last_modified_time', 'last_payment_date', 'last_reminder_sent_date', 'payment_expected_date', 'reference_number', 'reminders_sent', 'salesperson_id', 'salesperson_name', 'schedule_time', 'shipping_charge', 'status', 'total', 'type', 'write_off_amount', 'zcrm_potential_id', 'zcrm_potential_name'] 
#parameters['page'] = "1"
#print(response.json()['page_context']['has_more_page'])
#if(response.json()['page_context']['has_more_page'] == True):
    #print(1)

page_number = 1
parameters={'authtoken':auth_token_hiya,'organization_id':organization_id_hiya}
parameters['page'] = page_number

#while(response.json()['page_context']['has_more_page'] == True):
df_list = []
for i in itertools.count():
    parameters['page'] = page_number + i
    response = requests.get(base_url + end_points['invoices'],params = parameters)
    df_temp = pd.DataFrame(response.json()['invoices'])
    df_list.append(df_temp)
    print(parameters)
    if(response.json()['page_context']['has_more_page'] != True):
        break
print(len(df_list))

df_invoice_sheet = pd.concat(df_list,axis=0,sort=False)
print(len(df_invoice_sheet))
#df_invoice_sheet=pd.DataFrame(response.json()['invoices'])
#print(df_invoice_sheet[['date','status','customer_name','due_date']])
#print(df_invoice_sheet.groupby(['customer_name']).size())
df_new = pd.DataFrame()
for i in range(len(df_invoice_sheet)):
    #df_temp = pd.DataFrame()
    if(df_invoice_sheet.iloc[i]['status']=='paid' and df_invoice_sheet.iloc[i]['last_payment_date'] != ''):
        customer_name = df_invoice_sheet.iloc[i]['customer_name']
        difference_date  = (datetime.strptime(df_invoice_sheet.iloc[i]['last_payment_date'],'%Y-%m-%d').date()-datetime.strptime(df_invoice_sheet.iloc[i]['due_date'],'%Y-%m-%d').date()).days
        #print(df_invoice_sheet.iloc[i]['customer_name'],df_invoice_sheet.iloc[i]['date'],df_invoice_sheet.iloc[i]['due_date'],df_invoice_sheet.iloc[i]['status'])
        #print((datetime.strptime(df_invoice_sheet.iloc[i]['due_date'],'%Y-%m-%d').date()-datetime.strptime#(df_invoice_sheet.iloc[i]['date'],'%Y-%m-%d').date()).days)
        amount = df_invoice_sheet.iloc[i]['total']
        df_new = df_new.append({
            'customer_name':customer_name,'difference_days_avg':difference_date,'amount':amount,
        },ignore_index=True)
    #df_new = df_temp
g = df_new.groupby('customer_name')
df_new["weighted_avg"] = (df_new.difference_days_avg / g.amount.transform("sum")) * df_new.amount
df_new_2 = pd.DataFrame(df_new.groupby('customer_name').agg({'weighted_avg':'sum','difference_days_avg':'mean'}))
#for key,item in grouped:
    #print(grouped.get_group(key))
#print(df_new_2.iloc[:]['customer_name' == 'ABHISHEIK PHARMACEUTICALS'])
#df_new_2.to_excel(writer, sheet_name='Sheet1')
#writer.save()
#dates
today = date.today()
week_start = today #+ timedelta(days=7-today.weekday())
first_day =week_start
week = timedelta(days=7)
week_end = week_start + week

df_wk1 = df_wk2 = df_wk3 = df_wk4 = pd.DataFrame()
four_wk_report = [df_wk1,df_wk2,df_wk3,df_wk4]

df_invoices_2 = pd.DataFrame(columns=['customer_name','balance','age'])
for i in range(len(df_invoice_sheet)):
    #print(str(df_invoices.iloc[i][['due_days']]).split(" ")[4])
    customer_name = df_invoice_sheet.iloc[i]['customer_name'] 
    balance = df_invoice_sheet.iloc[i]['balance']
    #print(balance,customer_name)
    age=" "
    
    if(df_invoice_sheet.iloc[i]['due_days'].split(" ")[0]=='Overdue'):
        #print(int(str(df_invoices.iloc[i][['due_days']]).split(" ")[6]) * 1)
        age = int(df_invoice_sheet.iloc[i]['due_days'].split(" ")[2]) * 1
    elif(df_invoice_sheet.iloc[i]['due_days'].split(" ")[0]=='Due'):
        #print(int(str(df_invoices.iloc[i][['due_days']]).split(" ")[6]) * -1)
        if(df_invoice_sheet.iloc[i]['due_days'].split(" ")[1]=='Today'):
            age=0
        else:
            age = int(df_invoice_sheet.iloc[i]['due_days'].split(" ")[2]) * -1
    
    df_invoices_2 = df_invoices_2.append({
        'customer_name':customer_name,
        'balance':balance,
        'age':age,
    },ignore_index=True)

for i in range(len(four_wk_report)):
    df_temp = pd.DataFrame()
    for k in range(len(df_invoices_2)):
        customer_name = df_invoices_2.iloc[k]['customer_name']
        balance = df_invoices_2.iloc[k]['balance']
        if(df_invoices_2.iloc[k]['age'] != ' '):
            new_age = int(df_invoices_2.iloc[k]['age']) + (i*7)
            weighted_avg=difference_days_avg = "No record"
            if(new_age >= 0):
                for j in range(len(df_new_2)):
                    weighted_avg_list = list(df_new_2.weighted_avg[df_new_2.index == customer_name])
                    difference_days_avg_list = list(df_new_2.difference_days_avg[df_new_2.index == customer_name])

                    if(weighted_avg_list):
                        weighted_avg = math.ceil(weighted_avg_list[0])
                    if(difference_days_avg_list):
                        difference_days_avg = math.ceil(difference_days_avg_list[0])

                        
                        
                df_temp = df_temp.append({
                    'Customer Name': customer_name,
                    'Balance': balance,
                    'Age' : new_age,
                    'A_Weighted average':weighted_avg,
                    'A_Difference days average':difference_days_avg,
                },ignore_index=True)
    four_wk_report[i] = df_temp   


result = pd.concat(four_wk_report, keys=['as of '+str(first_day),'as of '+str(first_day+week), 'as of '+str(first_day+(week+week)),'as of '+str(first_day+(week+week+week))],axis=1)
#print(result)
result.to_excel(writer, sheet_name='Sheet1')
writer.save()

SEND_FROM = 'info@rawble.com'
EXPORTERS = {'dataframe.xlsx': export_excel}

def send_dataframe(send_to, subject, body, df):
  multipart = MIMEMultipart()
  multipart['From'] = SEND_FROM
  multipart['To'] = send_to
  multipart['Subject'] = subject
  for filename in EXPORTERS:    
    attachment = MIMEApplication(EXPORTERS[filename](df))
    attachment['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    attachment.get_filename
    multipart.attach(attachment)
  multipart.attach(MIMEText(body, 'html'))
  s = smtplib.SMTP_SSL('smtp.zoho.com:465')
  s.login('info@rawble.com','rawble@123')
  s.sendmail(SEND_FROM, send_to, multipart.as_string())
  s.quit()




send_dataframe('gupta.rishabh.abcd@gmail.com','somesome','data',result)