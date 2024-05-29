from fillpdf import fillpdfs
from ModelEvaluation import ModelEvaluation
from RagApplication import RagApplication
from OutputParser import OutputParser
import os
import time

class FillPDF:
    def __init__(self):
        self.files = os.listdir('company-10ks')
        self.rag_app = RagApplication()
        self.questions = ["""What is the nature of business for {company}?""",
                            'Who are the legal representatives for {company}?',
                            'What is the registered address for {company}?']

    def clean_outputs(self, arr):
        ret_arr = []
        for index, value in enumerate(arr):
            if index == 1:
                value = value[1:]
            if index == 2:
                value = value[0:-1]
            ret_arr.append("\n".join(value))
        return ret_arr


    def fill_pdf_template(self):
        for file in self.files:
            form_fields = list(fillpdfs.get_form_fields('Template_PDF/template.pdf').keys())
            company_name = " ".join(file.split(' ')[0:-1])
            file_path = os.path.join('company-10ks', file)
            filled_questions = [
            q.format(
                company = company_name
            )
            for q in self.questions
            ]
            outputs = []
            contexts = []
            for q in filled_questions:

                context = ""
                for doc in self.rag_app.compressed_vector_search(q):
                    context = context + " " + doc.page_content
                contexts.append([context])

                answer = self.rag_app.ask_question(q)
                parser = OutputParser(answer)
                outputs.append(parser.get_values())
                time.sleep(15)

            outputs = self.clean_outputs(outputs)
            # answers = [''.join(ele) for ele in outputs]

            df = ModelEvaluation.evaluate_output(filled_questions, outputs, contexts)

            final_outputs = []
            for index, row in df.iterrows():
                if ModelEvaluation.apply_metrics(row['question'], row['faithfulness'], row['answer_relevancy']):
                    final_outputs.append(row['answer'])
                else:
                    final_outputs.append("")

            print(final_outputs)
            final_outputs.append(file)
            data_dict = {
                index:value 
                for index, value in zip(form_fields, final_outputs)
            }
            new_file_name = f'template_{file}'
            fillpdfs.write_fillable_pdf('Template_PDF/template.pdf', output_pdf_path=os.path.join('Template_PDF/filled_pdfs', new_file_name), data_dict=data_dict)
            time.sleep(20) # Delay added because of Cohere API key trial