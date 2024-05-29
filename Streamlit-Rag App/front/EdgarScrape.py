from dotenv import load_dotenv
from sec_api import QueryApi
import requests
import os
from OpenCorporates import OpenCorporates
from StateOfIncorporation import StateOfIncorporation
from frontendhelper import check_collection
from RagApplication import RagApplication
import json
from create_collection import add_json_to_collection
import time

class SecPdfDownloader:
    def __init__(self):
        self.queryApi = QueryApi(os.environ['SEC_API_KEY'])
        self.state_app = StateOfIncorporation()
        self.rag_app = RagApplication()

    def check_pdfs(self, file_name): ## Note that this check will not work for a file uploaded from the frontend
        if file_name in os.listdir('company-10ks'):
            return True
        return False
    
    @staticmethod
    def download_pdf_helper(ticker, filing_url, company_name):
        PDF_GENERATOR_API = 'https://api.sec-api.io/filing-reader'
        try:
            new_folder = './company-10ks'
            file_name = company_name + ' 10K.pdf'
            
            if not os.path.isdir(new_folder):
                os.makedirs(new_folder)

            api_url = f"{PDF_GENERATOR_API}?token={os.environ['SEC_API_KEY']}&type=pdf&url={filing_url}"
            response = requests.get(api_url, stream=True)
            response.raise_for_status()

            with open(new_folder + "/" + file_name, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        except:
            print(f"❌ {ticker}: downloaded failed: {filing_url}")

    def download_pdf_and_json(self, ticker):
        query = {
            "query": { "query_string": { 
                "query": f"formType:\"10-K\" AND ticker:{ticker}", # only 10-Ks
            }},
            "from": "0", # start returning matches from position null, i.e. the first matching filing 
            "size": "1"  # return just one filing
            }
        response = self.queryApi.get_filings(query)
        print(response)
        filing = response['filings'][0]['linkToFilingDetails']
        company_name = response['filings'][0]['companyName']
        company_name = self.clean_company_name(company_name)
        #cik = response['filings'][0]['cik']
        try:
            state = response['filings'][0]['entities'][0]['stateOfIncorporation'].lower()
            jurisdiction_code = 'us_' + state
        except Exception as err:
            state_app = StateOfIncorporation()
            question = f"What is the state of incorporation for {company_name}"
            state = state_app.ask_question(question)
            jurisdiction_code  = OpenCorporates.get_jurisdiction_code(state, 'jurisdiction.json')
        file_name = company_name + " 10K.pdf"
        if self.check_pdfs(file_name) == False:
            a_1 = time.time()
            self.download_pdf_helper(ticker, filing, company_name) 
            self.rag_app.add_document(os.path.join('company-10ks', file_name))
            a_2 = time.time()
            print(f"DOWNLOAD AND ADD TO COLLECTION: {a_2 - a_1}")
        if self.check_jsons(company_name) == False:
            b_1 = time.time()
            data, path = self.pull_json(company_name, jurisdiction_code)
            self.rag_app.add_json_to_collection(data, path)
            b_2 = time.time()
            print(f"DOWNLOAD JSON AND ADD TO COLLECTION: {b_2 - b_1}")
            
        
    def check_jsons(self, company_name):
        file_name = f'{company_name}.json'
        if file_name in os.listdir('company_json'):
            return True
        return False

    def clean_company_name(self, name):
        if " COM" in name:
            name = name.replace(" COM", ".COM")
        to_remove = ['CO', 'INC', 'INC.', 'CORP', 'INC.,', 'INC,']
        name_arr = name.split(' ')
        clean_name = []
        for word in name_arr:
            if word.upper() not in to_remove:
                clean_name.append(word.capitalize())
        return " ".join(clean_name)
    
    def pull_json(self, company_name, jurisdiction_code):
        
        company_data = OpenCorporates.loose_search_api(company_name, jurisdiction_code, os.environ['OPENCORPORATE_API_KEY'])
        company_number = OpenCorporates.get_company_number(company_data)
        full_data = OpenCorporates.call_api(jurisdiction_code, company_number, os.environ['OPENCORPORATE_API_KEY'])
        clean_data = OpenCorporates.clean_data(OpenCorporates, full_data)
        file_path = f'company_json/{company_name}.json'
        with open(file_path, 'w') as file:
            json.dump(clean_data, file)
        return clean_data, file_path
    