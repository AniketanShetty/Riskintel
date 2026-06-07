# -*- coding: utf-8 -*-
"""
Created on Sun Nov 18 16:27:51 2018

@author: Ratnadeep
"""
import pandas as pd

def getpnbdf(varFileName,headerRow):
    pnb = pd.read_csv(varFileName,encoding='latin-1')
    pnb=pnb.iloc[:,:10]
    print(len(pnb))
    pnb.STATE = pnb.STATE.str.strip()
    pnb.STATE = pnb.STATE.str.upper()
    pnb.loc[pnb['STATE'] == 'UTTRAKHAND','STATE']= 'UTTARAKHAND'
    pnb.loc[pnb['STATE'] == 'M.P.','STATE']="MADHYA PRADESH"
    pnb.loc[pnb['STATE'] == 'U P','STATE']="UTTAR PRADESH"
    pnb.loc[pnb['STATE'] == 'LUDHIANA','STATE']="PUNJAB"
    pnb.loc[pnb['STATE'] == 'PATIALA','STATE'] ="PUNJAB"
    pnb.loc[pnb['STATE'] == 'TAMILNADU','STATE'] = 'TAMIL NADU'
    pnb.loc[pnb['STATE'] == 'TN','STATE'] ='TAMIL NADU'
    pnb.loc[pnb['STATE'] == 'ANDHRA','STATE'] ='ANDHRA PRADESH'
    pnb.loc[pnb['STATE'] == 'MP','STATE'] ='MADHYA PRADESH'
    pnb.loc[pnb['STATE'] == 'UP','STATE']="UTTAR PRADESH"
    pnb.loc[pnb['STATE'] == 'GUJRAT','STATE']='GUJARAT'
    pnb.loc[pnb['STATE'] == 'J&K','STATE']='JAMMU AND KASHMIR'
    

    pnb.rename({'OSAMT (Rs. Lac)':'OSAMT'}, axis='columns',inplace=True)
    # Print because of \xa0 character in some amounts
    #print(pnb.iloc[800:807,:]['OSAMT'])
    pnb['OSAMT2']=pnb['OSAMT'].astype(str)
    
    #print(pnb.iloc[800:807,:]['OSAMT2'])
    pnb['OSAMT3'] = pnb.OSAMT2.str.strip()
    pnb['OSAMT4'] = pnb['OSAMT3'].str.replace("'\\xa0'"," ")
    pnb['OSAMT5'] = pnb['OSAMT4'].str.replace(",","")
    
    pnb['OSAMT6'] =pd.to_numeric(pnb['OSAMT5'],errors='coerce')
    pnb.drop(pnb[pnb['STATE'].isna()].index, inplace=True)
    #print(pnb.iloc[800:807,:]['OSAMT6'])
    pnb=pnb.iloc[:,[0,1,2,3,4,5,6,8,9,14]]
    pnb.rename(columns = {'OSAMT6': 'osamt','PRTY':'PARTY'},inplace=True)
    #pnb.rename(columns={'prty':'party'},inplace=True)
    pnb.rename(str.lower,axis='columns',inplace=True)
    pnb.bknm = 'PNB'
    #pnb.to_csv('pnb.csv')
    return pnb

def getidbidf(varFileName,headerRow):
    idbi = pd.read_csv(varFileName, encoding='latin-1',header=headerRow)
    idbi = idbi.iloc[:,:10]#only keep the required 10 columns
    idbi.columns = idbi.columns.str.lower()
    idbi.columns = idbi.columns.str.replace('.','')
    idbi.columns = idbi.columns.str.strip( ' ')
    idbi['state'] = idbi.state.str.upper()
    idbi['state']=idbi.state.str.strip()
    
    #Correct state names:
    idbi.loc[idbi['state'] == 'D','state'] = 'WEST BENGAL'
    #idbi.loc[idbi['state'] == 'WEST BENGAL','state'] = 'WB'
    idbi.loc[idbi['state'] == 'TELENGANA','state'] = 'TELANGANA'
    idbi.loc[idbi['state'] == 'NEW DELHI','state'] = 'DELHI'
    idbi.loc[idbi['state'] == 'ANDHRA','state'] = 'ANDHRA PRADESH'
    idbi.loc[idbi['state'] == 'ANDHRA PRADHESH','state'] = 'ANDHRA PRADESH'
    #idbi.loc[idbi['state'] == 'MADHYA PRADESH','state'] = 'MP'
    idbi.loc[idbi['state'].isna(),'state'] = 'CHHATISGARH'
    idbi.loc[idbi['state'] == 'TN','state'] = 'TAMIL NADU'
    idbi.loc[idbi['state'] == 'TAMILNADU','state'] = 'TAMIL NADU'
    idbi.loc[idbi['state'] == 'MP','state'] = 'MADHYA PRADESH'
    
    idbi.bknm = 'IDBI'

    return idbi

def getbobdf(varFileName,varStatesFile):
    #global varStatesFile
    bob = pd.read_excel(varFileName, sheet_name=None)
    bob = pd.concat(bob,axis=0)
    bob = bob.iloc[:,:9]
    #rename columns
    new_col_names ={'ZONE REGION\nBK BRANCH STATE': 'var1',
                'CUSTOMER': 'party',
                'SRN O': 'srno',
                'REGISTERED ADDRESS': 'regaddr',
                'BALANCE (RS. IN LAKHS)':'osamt',
                'SUIT': 'suit',
                'OTHER_BA NK': 'other_bk'
                }
    #varStatesFile= varPath+'states.csv'
    bob.rename(columns = new_col_names,inplace=True)
    statesdf = pd.read_csv(varStatesFile,header=0)
    
    bob['bknm']=  	'BOB'
    bob['state'] = ''
    bob['bkbr']=''
    bob['sctg'] =0.0
    pos_bkbr = bob.columns.get_loc('bkbr')
    pos_state = bob.columns.get_loc('state')
    for j in range(0,len(bob)):
        myStr = bob.iloc[j,2].split('\n')[-1]
        for i in range(0,len(statesdf)):
            val = myStr.find(statesdf.iloc[i,0])
            if(val != -1):
                varState = statesdf.iloc[i,0]
                bob.iloc[j,pos_state] = varState
                bob.iloc[j,pos_bkbr]=myStr.replace(varState,'')
                
    # JAMMU & KASHMIR HANDLED SEPARATELY
    bob.loc[bob['var1'].str.contains('JAMMU & KASHMIR'),'state']='JAMMU AND KASHMIR'
    #manual correction for states
    bob.loc[bob['var1'].str.contains('UTTAR PARDESH'),'state']='UTTAR PRADESH'
    bob.loc[bob['var1'].str.contains('TELENGANA'),'state']='TELANGANA'
    bob.iloc[320,pos_state]='GUJARAT'
    bob.iloc[331,pos_state]='GUJARAT'
    bob.iloc[367,pos_state] ='TELANGANA'

    
    bob = bob.reset_index()
    cols_drop = ['level_0','level_1','REPORT DATE(MM/D D/YYYY)','var1',
                 'PAN_NO_C OMPANY']
    
    bob.drop(columns=cols_drop,inplace=True)
    return bob

def getsyndicatedf(varFileName,headerLine):
    syndicate = pd.read_csv(varFileName,header=headerLine)
    syndicate = syndicate.iloc[:,1:12]
    
    cols_new_name = { 'BALANCE OUTSTANDING AS ON 30.09.2015':'osamt',
                     'PRTY':'party'}
    syndicate.rename(columns=cols_new_name,inplace=True)
    
    cols_drop = ['STATE.1']
    syndicate.drop(columns=cols_drop,inplace=True)
    syndicate.rename(str.lower,axis=1,inplace=True)
    syndicate.loc[syndicate['state'] =='TAMILNADU','state']='TAMIL NADU'
    syndicate.loc[syndicate['state'] =='ORISSA','state']='ODISHA'
    syndicate.bknm = 'SYNDBK'
    return syndicate

def getCombinedDF(varPath=None):
    if (varPath != None):
        varPath = varPath+'/'
    else:
        varPath = ''
    print(varPath)
    varStatesFile = varPath+'states.csv'
    statesdf = pd.read_csv(varStatesFile,header=0)
    pnb = getpnbdf(varPath+'PNB1.csv',0)
    idbi = getidbidf(varPath+'IDBI.csv',1)
    bob = getbobdf(varPath+'BOB.xlsx',varStatesFile)
    syndicate = getsyndicatedf(varPath+'Syndicate.csv',0)
    combined_df = pd.concat([pnb,bob,idbi,syndicate],axis=0)
    return combined_df

    
    

    
    


    