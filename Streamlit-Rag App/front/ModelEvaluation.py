import os


from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_relevancy
)


class ModelEvaluation:
    @staticmethod
    def evaluate_output(questions, answers, contexts):
        # To dict
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts
        }

        dataset = Dataset.from_dict(data)

        result = evaluate(
            dataset = dataset, 
            metrics=[
                context_relevancy,
                faithfulness,
                answer_relevancy,
            ],
        )
        df = result.to_pandas()
        return df
    
    @staticmethod
    def apply_metrics(question, faithfulness, answer_relevancy):
        if "nature of business" in question and faithfulness < 1:          #threshold = 1
            return False
        if 'registered address' in question and faithfulness < 0.5:
            return False
        if 'legal representatives' in question and answer_relevancy < 0.7:
            return False
        return True