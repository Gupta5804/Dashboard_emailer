import requests
import json
import pandas as pd
from datetime import date,time,datetime,timedelta
from openpyxl import load_workbook
import itertools
import math
import io
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import cufflinks as cf
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from email.mime.image import MIMEImage

from email.mime.text import MIMEText
import smtplib

import matplotlib.pyplot as plt
print("1")
import seaborn as sns

#******* Functions for converting to excel attachment**********
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

# ********** credentials *********************
auth_token_hiya="fc3ed86b62485a2b9a6a680477ea7e60"
auth_token_rawble="e8253e7e6017303a54f57ce28b9d209a"
organization_id_hiya="654806043"
organization_id_rawble = "667580392"
base_url = "https://books.zoho.com/api/v3"
end_points = {'invoices':'/invoices','crm':'/crm','contacts':'/contacts','account':'/account','bills':'/bills'}

#************ Taking entire data INVOICES*********** 
page_number = 1
parameters={'authtoken':auth_token_rawble,'organization_id':organization_id_rawble}
parameters['page'] = page_number
df_list_inv = []
for i in itertools.count():
    parameters['page'] = page_number + i
    response = requests.get(base_url + end_points['invoices'],params = parameters)
    df_temp = pd.DataFrame(response.json()['invoices'])
    df_list_inv.append(df_temp)
    print(parameters)
    if(response.json()['page_context']['has_more_page'] != True):
        break
print(len(df_list_inv))

df_invoice_sheet = pd.concat(df_list_inv,axis=0,sort=False)
print(len(df_invoice_sheet))


#**************calculating weighted average ***********
df_new_inv = pd.DataFrame()
for i in range(len(df_invoice_sheet)):
    if(df_invoice_sheet.iloc[i]['status']=='paid' and df_invoice_sheet.iloc[i]['last_payment_date'] != ''):
        customer_name = df_invoice_sheet.iloc[i]['customer_name']
        difference_date  = (datetime.strptime(df_invoice_sheet.iloc[i]['last_payment_date'],'%Y-%m-%d').date()-datetime.strptime(df_invoice_sheet.iloc[i]['due_date'],'%Y-%m-%d').date()).days
        if(difference_date<0):
            difference_date = 0
            
        amount = df_invoice_sheet.iloc[i]['total']
        df_new_inv = df_new_inv.append({
            'customer_name':customer_name,'difference_days_avg':difference_date,'amount':amount,
        },ignore_index=True)
g = df_new_inv.groupby('customer_name')
df_new_inv["weighted_avg"] = (df_new_inv.difference_days_avg / g.amount.transform("sum")) * df_new_inv.amount
df_new_2_inv = pd.DataFrame(df_new_inv.groupby('customer_name').agg({'weighted_avg':'sum','difference_days_avg':['mean','max','min']}))



#*************dates****************
today = date.today()
week_start = today #+ timedelta(days=7-today.weekday())
first_day =week_start
week = timedelta(days=7)
week_end = week_start + week


#********creating final report***********
df_wk1_inv = df_wk2_inv = df_wk3_inv = df_wk4_inv = pd.DataFrame()
four_wk_report_inv = [df_wk1_inv,df_wk2_inv,df_wk3_inv,df_wk4_inv]

df_invoices_2 = pd.DataFrame(columns=['customer_name','balance','age'])
for i in range(len(df_invoice_sheet)):
    
    customer_name = df_invoice_sheet.iloc[i]['customer_name'] 
    balance = df_invoice_sheet.iloc[i]['balance']
    
    age=" "
    
    if(df_invoice_sheet.iloc[i]['due_days'].split(" ")[0]=='Overdue'):
        
        age = int(df_invoice_sheet.iloc[i]['due_days'].split(" ")[2]) * 1
    elif(df_invoice_sheet.iloc[i]['due_days'].split(" ")[0]=='Due'):
        
        if(df_invoice_sheet.iloc[i]['due_days'].split(" ")[1]=='Today'):
            age=0
        else:
            age = int(df_invoice_sheet.iloc[i]['due_days'].split(" ")[2]) * -1
    
    df_invoices_2 = df_invoices_2.append({
        'customer_name':customer_name,
        'balance':balance,
        'age':age,
    },ignore_index=True)

for i in range(len(four_wk_report_inv)):
    df_temp = pd.DataFrame()
    for k in range(len(df_invoices_2)):
        customer_name = df_invoices_2.iloc[k]['customer_name']
        balance = df_invoices_2.iloc[k]['balance']
        if(df_invoices_2.iloc[k]['age'] != ' '):
            new_age = int(df_invoices_2.iloc[k]['age']) + (i*7)
            weighted_avg=difference_days_avg =probability= "No record"
            if(new_age >= 0):
                minimum_ent = 0
                maximum_ent =0 
                
                if(not df_new_2_inv.weighted_avg[df_new_2_inv.index == customer_name]['sum'].empty):
                    weighted_avg = int(df_new_2_inv.weighted_avg[df_new_2_inv.index == customer_name]['sum'])
                
                if(not df_new_2_inv.difference_days_avg[df_new_2_inv.index == customer_name]['mean'].empty):
                    difference_days_avg = int(df_new_2_inv.difference_days_avg[df_new_2_inv.index == customer_name]['mean'])
                if(not df_new_2_inv.difference_days_avg[df_new_2_inv.index == customer_name]['min'].empty):
                    minimum_ent = int(df_new_2_inv.difference_days_avg[df_new_2_inv.index == customer_name]['min'])
                if(not df_new_2_inv.difference_days_avg[df_new_2_inv.index == customer_name]['max'].empty):
                    maximum_ent = int(df_new_2_inv.difference_days_avg[df_new_2_inv.index == customer_name]['max'])
                
                if(minimum_ent == maximum_ent) :
                    if (new_age<minimum_ent):
                        probability = "25% - 50%"
                    if(new_age>=minimum_ent):
                        probability = "max 100%"
                else:
                    if(new_age < minimum_ent):
                        probability = "0% - 25%"
                    if(new_age>=minimum_ent and new_age< difference_days_avg):
                        probability = "25% - 50%"
                    if(new_age >= difference_days_avg and new_age < (difference_days_avg + ((maximum_ent - difference_days_avg)/2))):
                        probability = "50% - 75%"
                    if(new_age >= (difference_days_avg + ((maximum_ent - difference_days_avg)/2)) and new_age < maximum_ent):
                        probability = "75% - 100%"
                    if(new_age >= maximum_ent):
                        probability = "max 100%"


                        
                        
                df_temp = df_temp.append({
                    'Customer_Name': customer_name,
                    'Balance': balance,
                    'Age' : new_age,
                    'A_Weighted average':weighted_avg,
                    'A_Difference days average':difference_days_avg,
                    'probability': probability,
                },ignore_index=True)
    four_wk_report_inv[i] = df_temp   
sum_recievable_wk = [0,0,0,0]
for j in range(len(four_wk_report_inv)):
    for i in range(len(four_wk_report_inv[j])):
        df_temp = four_wk_report_inv[j]
        sum_recievable_wk[j] = sum_recievable_wk[j] + df_temp.iloc[i]['Balance']
    df_graph_pivoted = four_wk_report_inv[j].pivot_table(index = "Customer_Name",columns = "probability",values="Balance",aggfunc = "sum")
    data = []
    for index,Customer_Name in df_graph_pivoted.iterrows():
        trace = go.Bar( x = df_graph_pivoted.columns, y = Customer_Name , name = index )
        data.append(trace)
    layout = go.Layout(
            title = "As of " +str(today + timedelta(days=(7*j))),
            showlegend=True,
            barmode="stack",
            xaxis = dict(
                    title = "Probability"),
            yaxis = dict(
                    title = "Balance",
    ))
    figure = go.Figure(data=data, layout=layout)

    url = py.plot(figure,filename = "rawble_recievable_wk_" + str(j+1))
    print(url)
    

result1 = pd.concat(four_wk_report_inv, keys=['as of '+str(first_day),'as of '+str(first_day+week), 'as of '+str(first_day+(week+week)),'as of '+str(first_day+(week+week+week))],axis=1)
print(sum_recievable_wk)





#************ Taking entire data BILLS***********
page_number = 1
df_list_bi = []
for i in itertools.count():
    parameters['page'] = page_number + i
    response = requests.get(base_url + end_points['bills'],params = parameters)
    df_temp = pd.DataFrame(response.json()['bills'])
    df_list_bi.append(df_temp)
    print(parameters)
    if(response.json()['page_context']['has_more_page'] != True):
        break
print(len(df_list_bi))

df_bill_sheet = pd.concat(df_list_bi,axis=0,sort=False)
print(len(df_bill_sheet))


#**************calculating weighted average ***********
df_new_bi = pd.DataFrame()
for i in range(len(df_bill_sheet)):
    
    if(df_bill_sheet.iloc[i]['status']=='paid'):
        vendor_name = df_bill_sheet.iloc[i]['vendor_name']
        difference_date  = (datetime.strptime(str(df_bill_sheet.iloc[i]['last_modified_time']).split("T")[0],'%Y-%m-%d').date()-datetime.strptime(df_bill_sheet.iloc[i]['due_date'],'%Y-%m-%d').date()).days
        if difference_date < 0 :
            difference_date = 0
        amount = df_bill_sheet.iloc[i]['total']
        df_new_bi = df_new_bi.append({
            'vendor_name':vendor_name,'difference_days_avg':difference_date,'amount':amount,
        },ignore_index=True)
    
g = df_new_bi.groupby('vendor_name')
df_new_bi["weighted_avg"] = (df_new_bi.difference_days_avg / g.amount.transform("sum")) * df_new_bi.amount
df_new_2_bi = pd.DataFrame(df_new_bi.groupby('vendor_name').agg({'weighted_avg':'sum','difference_days_avg':['mean','max','min']}))

#*************dates****************
today = date.today()
week_start = today #+ timedelta(days=7-today.weekday())
first_day =week_start
week = timedelta(days=7)
week_end = week_start + week


#********creating final report***********
df_wk1_bi = df_wk2_bi = df_wk3_bi = df_wk4_bi = pd.DataFrame()
four_wk_report_bi = [df_wk1_bi,df_wk2_bi,df_wk3_bi,df_wk4_bi]

df_bill_2 = pd.DataFrame(columns=['vendor_name','balance','age'])
for i in range(len(df_bill_sheet)):
    
    vendor_name = df_bill_sheet.iloc[i]['vendor_name'] 
    balance = df_bill_sheet.iloc[i]['balance']
    
    age=" "
    
    if(df_bill_sheet.iloc[i]['due_days'].split(" ")[0]=='Overdue'):
        
        age = int(df_bill_sheet.iloc[i]['due_days'].split(" ")[2]) * 1
    elif(df_bill_sheet.iloc[i]['due_days'].split(" ")[0]=='Due'):
        
        if(df_bill_sheet.iloc[i]['due_days'].split(" ")[1]=='Today'):
            age=0
        else:
            age = int(df_bill_sheet.iloc[i]['due_days'].split(" ")[2]) * -1
    
    df_bill_2 = df_bill_2.append({
        'vendor_name':vendor_name,
        'balance':balance,
        'age':age,
    },ignore_index=True)

for i in range(len(four_wk_report_bi)):
    df_temp = pd.DataFrame()
    for k in range(len(df_bill_2)):
        vendor_name = df_bill_2.iloc[k]['vendor_name']
        balance = df_bill_2.iloc[k]['balance']
        if(df_bill_2.iloc[k]['age'] != ' '):
            new_age = int(df_bill_2.iloc[k]['age']) + (i*7)
            weighted_avg=difference_days_avg = probability= "No record"
            if(new_age >= 0):
                minimum_ent = 0
                maximum_ent =0 
                
                if(not df_new_2_bi.weighted_avg[df_new_2_bi.index == vendor_name]['sum'].empty):
                    weighted_avg = int(df_new_2_bi.weighted_avg[df_new_2_bi.index == vendor_name]['sum'])
                
                if(not df_new_2_bi.difference_days_avg[df_new_2_bi.index == vendor_name]['mean'].empty):
                    difference_days_avg = int(df_new_2_bi.difference_days_avg[df_new_2_bi.index == vendor_name]['mean'])
                if(not df_new_2_bi.difference_days_avg[df_new_2_bi.index == vendor_name]['min'].empty):
                    minimum_ent = int(df_new_2_bi.difference_days_avg[df_new_2_bi.index == vendor_name]['min'])
                if(not df_new_2_bi.difference_days_avg[df_new_2_bi.index == vendor_name]['max'].empty):
                    maximum_ent = int(df_new_2_bi.difference_days_avg[df_new_2_bi.index == vendor_name]['max'])
                
                if(minimum_ent == maximum_ent) :
                    if (new_age<minimum_ent):
                        probability = "25% - 50%"
                    if(new_age>=minimum_ent):
                        probability = "max 100%"
                else:
                    if(new_age < minimum_ent):
                        probability = "0% - 25%"
                    if(new_age>=minimum_ent and new_age< difference_days_avg):
                        probability = "25% - 50%"
                    if(new_age >= difference_days_avg and new_age < (difference_days_avg + ((maximum_ent - difference_days_avg)/2))):
                        probability = "50% - 75%"
                    if(new_age >= (difference_days_avg + ((maximum_ent - difference_days_avg)/2)) and new_age < maximum_ent):
                        probability = "75% - 100%"
                    if(new_age >= maximum_ent):
                        probability = "max 100%"
                        
                        
                df_temp = df_temp.append({
                    'Vendor_Name': vendor_name,
                    'Balance': balance,
                    'Age' : new_age,
                    'A_Weighted average':weighted_avg,
                    'A_Difference days average':difference_days_avg,
                    'probability': probability,
                },ignore_index=True)
    four_wk_report_bi[i] = df_temp   

sum_payable_wk = [0,0,0,0]
for j in range(len(four_wk_report_bi)):
    for i in range(len(four_wk_report_bi[j])):
        df_temp = four_wk_report_bi[j]
        sum_payable_wk[j] = sum_payable_wk[j] + df_temp.iloc[i]['Balance']
    df_graph_pivoted = four_wk_report_bi[j].pivot_table(index = "Vendor_Name",columns = "probability",values="Balance",aggfunc = "sum")
    data = []
    for index,Vendor_Name in df_graph_pivoted.iterrows():
        trace = go.Bar( x = df_graph_pivoted.columns, y = Vendor_Name , name = index )
        data.append(trace)
    layout = go.Layout(
            title = "As of " +str(today + timedelta(days=(7*j))),
            showlegend=True,
            barmode="stack",
            xaxis = dict(
                    title = "Probability"),
            yaxis = dict(
                    title = "Balance"
    ))
    figure = go.Figure(data=data, layout=layout)
    url = py.plot(figure,filename = "rawble_payable_wk_"+str(j+1))
    print(url)

result2 = pd.concat(four_wk_report_bi, keys=['as of '+str(first_day),'as of '+str(first_day+week), 'as of '+str(first_day+(week+week)),'as of '+str(first_day+(week+week+week))],axis=1)
print(sum_payable_wk)
difference = [0,0,0,0]
for j in range(len(sum_payable_wk)):
    difference[j] = sum_recievable_wk[j] - sum_payable_wk[j]
print(difference)

df_graph = pd.DataFrame({'payables':sum_payable_wk,'recievables':sum_recievable_wk,'difference':difference,'week':['as of '+str(first_day),'as of '+str(first_day+week), 'as of '+str(first_day+(week+week)),'as of '+str(first_day+(week+week+week))]})
print(df_graph)
data = df_graph.melt(id_vars =['week'],value_vars=['payables','recievables','difference'] )
print(data)
sns.set(rc={'figure.figsize':(15,12)})
ax = sns.barplot(x='week', y='value',hue='variable', data=data)
for p in ax.patches:
    ax.text(p.get_x() + p.get_width()/2., p.get_height(), '%d' % int(p.get_height()), 
            fontsize=14, color='black', ha='center', va='bottom')


figfilename = "output_"+str(today)+".png"
fig = ax.get_figure()
fig.savefig(figfilename)

df_graph = pd.DataFrame({'payables':sum_payable_wk,'recievables':sum_recievable_wk,'difference':difference,'week':['as of '+str(first_day),'as of '+str(first_day+week), 'as of '+str(first_day+(week+week)),'as of '+str(first_day+(week+week+week))]}).set_index('week',drop=True)



data = [{
    'x': df_graph.index,
    'y': df_graph[col],
    'name': col,
    'type':'bar',
    
}  for col in df_graph.columns]



py.plot(data,filename = "rawble_recievable_payable_summary")

SEND_FROM = 'info@rawble.com'
EXPORTERS = {'dataframe.xlsx': export_excel}

def send_dataframe(send_to, subject, body, df1,df2,ImgFileName):
  multipart = MIMEMultipart()
  multipart['From'] = SEND_FROM
  multipart['To'] = send_to
  multipart['Subject'] = subject
  img_data = open(ImgFileName, 'rb').read()
  for filename in EXPORTERS:    
    attachment1 = MIMEApplication(EXPORTERS[filename](df1))
    attachment1['Content-Disposition'] = 'attachment; filename="recievables.xlsx"'.format(filename)
    multipart.attach(attachment1)
    attachment2 = MIMEApplication(EXPORTERS[filename](df2))
    attachment2['Content-Disposition'] = 'attachment; filename="payables.xlsx"'.format(filename)
    multipart.attach(attachment2)
    image = MIMEImage(img_data, name="graph_"+str(today)+".png")
    multipart.attach(image)
  multipart.attach(MIMEText(body, 'html'))
  s = smtplib.SMTP_SSL('smtp.zoho.com:465')
  s.login('info@rawble.com','rawble@123')
  s.sendmail(SEND_FROM, send_to, multipart.as_string())
  s.quit()

body=  """ <p style="text-align: center;"><strong>As Of <span style="color: #ff0000;">"""+str(today)+"""</span></strong></p>
<p style="text-align: center;">&nbsp;</p>
<p style="text-align: center;"><span style="color: #000000;"><strong>Total Payables = """+str(sum_payable_wk[0])+"""</strong></span></p>
<p style="text-align: center;"><span style="color: #000000;"><strong>Total Recievables = """+str(sum_recievable_wk[0])+"""</strong></span></p>
<p style="text-align: center;"><span style="color: #000000;"><strong><a href = "https://plot.ly/~rishabh.gupta.min15/123/rawble-dashboard/"> Your Dashboard Link </a></strong></span></p>
<p>&nbsp;</p>
<p>&nbsp;</p>
"""
subject = "Rawble Recievables and Payables"
send_dataframe('admin@rawble.com',subject,body,result1,result2,figfilename)
send_dataframe('rishabh.gupta@rawble.com',subject,body,result1,result2,figfilename)
send_dataframe('kunal@rawble.com',subject,body,result1,result2,figfilename)
send_dataframe('gupta.rishabh.abcd@gmail.com',subject,body,result1,result2,figfilename)
send_dataframe('madhur@rawble.com',subject,body,result1,result2,figfilename)