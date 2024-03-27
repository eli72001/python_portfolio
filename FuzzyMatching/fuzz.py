import pandas as pd
import warnings
from thefuzz import fuzz


relation = '[Asset] is classified by [Business Dimension] > Name'
# Load Files: All Data Concepts, SQL LDD and PDD, Databricks LDD and PDD
with warnings.catch_warnings(record=True):
    warnings.simplefilter("always")
    concepts = pd.read_excel('dg.xlsx', engine='openpyxl')
    dbPDD = pd.read_excel('columnsCollibra.xlsx', engine='openpyxl')
    dbLDD = pd.read_excel('dbLDD.xlsx', engine='openpyxl')
    sqlPDD = pd.read_excel('SQLPhysicalDataDictionary.xlsx', engine='openpyxl')
    sqlLDD = pd.read_excel('sqlLDD.xlsx', engine='openpyxl')

# Create Set of Data Concepts, LDDs and PDDs
dataConcepts = set(concepts['Name'].tolist())
    # Get rid of duplicates
#databricksColumns = set(dbPDD['Name'].tolist())
#sqlColumns = set(sqlPDD['Name'].tolist())
    # Keep Duplicates
databricksColumns = dbPDD['Name'].tolist()
sqlColumns = sqlPDD['Name'].tolist()
# Put Concepts in Map and Map to Logical Layer
dcMap = {}
dbMap = {}
sqlMap = {}
for c in dataConcepts:
    dbAttribute = dbLDD[~dbLDD[~dbLDD.where(dbLDD[relation]==c).isna()].isnull().any(axis=1)]['Name'].tolist()
    sqlAttribute = sqlLDD[~sqlLDD[~sqlLDD.where(sqlLDD[relation]==c).isna()].isnull().any(axis=1)]['Name'].tolist()
    for attr in dbAttribute:
        if c in dbMap.keys():
            dcMap[c].append(attr)
            dbMap[c].append(attr)
        else:
            dcMap[c] = [attr]
            dbMap[c] = [attr]
        
    for attr in sqlAttribute:
        if c in sqlMap.keys():
            dcMap[c].append(attr)
            sqlMap[c].append(attr)
        else:
            dcMap[c] = [attr]
            sqlMap[c] = [attr]
print(f'Number of DB Columns: {len(databricksColumns)}\nNumber of DB Attributes: {len(dbMap)}')
print(f'Number of SQL Columns: {len(sqlColumns)}\nNumber of SQL Attributes: {len(sqlMap)}')

# Find Matches SQL
sqlFuzzDict = {'Data Concept': [], 'Data Attribute': [],'Column Name': [], 'Ratio Score': [], 'Partial Ratio Score': []}
num = 0
for dc in sqlMap.keys():
    for c in sqlColumns:
        if fuzz.partial_ratio(dc, c) > 74 and fuzz.ratio(dc,c) > 65:
            num+=1
            sqlFuzzDict['Column Name'].append(c)
            sqlFuzzDict['Data Attribute'].append(sqlMap[dc])
            sqlFuzzDict['Data Concept'].append(dc)
            sqlFuzzDict['Ratio Score'].append(fuzz.ratio(dc, c))
            sqlFuzzDict['Partial Ratio Score'].append(fuzz.partial_ratio(dc, c))
#print(pd.DataFrame(sqlFuzzDict).sort_values('Data Concept'))
print('\n')

# Find Matches DB
dbFuzzDict = {'Data Concept': [], 'Data Attribute': [],'Column Name': [], 'Ratio Score': [], 'Partial Ratio Score': []}
num = 0
for dc in dbMap.keys():
    for c in databricksColumns:
        if fuzz.partial_ratio(dc, c) > 74 and fuzz.ratio(dc,c) > 65:
            num+=1
            dbFuzzDict['Column Name'].append(c)
            dbFuzzDict['Data Attribute'].append(dbMap[dc])
            dbFuzzDict['Data Concept'].append(dc)
            dbFuzzDict['Ratio Score'].append(fuzz.ratio(c, dc))
            dbFuzzDict['Partial Ratio Score'].append(fuzz.partial_ratio(c, dc))
print(pd.DataFrame(dbFuzzDict).sort_values('Column Name'))


'''


fuzzDict = {'Data Concept': [], 'Column Name': [], 'Ratio Score': [], 'Partial Ratio Score': []}
num = 0
for dc in dataConcepts:
    for c in databricksColumns:
        #if fuzz.ratio(dc,c) > 60:
        #    print(f"{num}. Similarity Score between {dc.upper()} and {c.upper()}: {fuzz.ratio(dc, c)} {fuzz.partial_ratio(dc,c)}")
        #    num +=1
        if fuzz.ratio(dc,c) > 60:
            fuzzDict['Data Concept'].append(dc)
            fuzzDict['Column Name'].append(c)
            fuzzDict['Ratio Score'].append(fuzz.ratio(dc, c))
            fuzzDict['Partial Ratio Score'].append(fuzz.partial_ratio(dc, c))

print(pd.DataFrame(fuzzDict))

'''