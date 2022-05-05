"""
Based on @cbadenes' BertENClassifier.py
"""
import csv
import json
import kenlm
import torch
import numpy as np
from transformers import BertTokenizer, BertForSequenceClassification

class QuestionClassifier:
    """
    Class Constructor: Initializes local files in resources_dir
    """
    def __init__(self,resources_dir):

        category_model_dir = resources_dir+'/BERT Fine-Tuning category'
        literal_model_dir = resources_dir+'/BERT Fine-Tuning literal'
        resource_model_dir = resources_dir+'/BERT Fine-Tuning resource'
        mapping_csv = resources_dir+'/mapping.csv'
        hierarchy_json = resources_dir+'/dbpedia_hierarchy.json'
        
        self.id_to_label = {}
        self.label_to_id = {}
        with open(mapping_csv) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                self.id_to_label[row[1]] = row[0]
                self.label_to_id[row[0]] = row[1]
        
        self.category_tokenizer = BertTokenizer.from_pretrained(category_model_dir)
        self.category_model = BertForSequenceClassification.from_pretrained(category_model_dir,num_labels=3)
        
        self.literal_tokenizer = BertTokenizer.from_pretrained(literal_model_dir)
        self.literal_model = BertForSequenceClassification.from_pretrained(literal_model_dir,num_labels=3)
        
        self.resource_tokenizer = BertTokenizer.from_pretrained(resource_model_dir)
        self.resource_model = BertForSequenceClassification.from_pretrained(resource_model_dir,num_labels=len(self.id_to_label))
        
        self.hierarchy = {}
        with open(hierarchy_json) as json_file:
            self.hierarchy = json.load(json_file)

        self.fluencyScoreModel = kenlm.Model(resources_dir+"/ZAMIA_Fluency_Score/en_large_model.binary")
            
    def getAnswerCategory(self,question):
        """
        Method that gets the answer category of a question.
        """
        res = self.classifyAnswerCategory(question)
        #If the question is a literal, it returns the literal category.
        if res == 'Literal':
            return self.classifyLiterals(question)
        return res
            
    def classifyAnswerCategory(self,q):
        """
        Auxiliary method that gets the answer category of a question.
        """
        input_ids = torch.tensor(self.category_tokenizer.encode(q, add_special_tokens=True)).unsqueeze(0)  # Batch size 1
        labels = torch.tensor([1]).unsqueeze(0)  # Batch size 1
        
        with torch.no_grad():
            outputs = self.category_model(input_ids, labels=labels)
        logits = outputs[1]
        result = np.argmax(logits.detach().numpy(),axis=1)[0]
        if result == 0:
            categoryLabel = 'Boolean'
        elif result == 1:
            categoryLabel = 'Literal'
        else:
            categoryLabel = 'String'
        return categoryLabel
    
    def classifyLiterals(self,q):
        """
        Method that gets the literal category of a question.
        """
        input_ids = torch.tensor(self.literal_tokenizer.encode(q, add_special_tokens=True)).unsqueeze(0)  # Batch size 1
        labels = torch.tensor([1]).unsqueeze(0)  # Batch size 1
        
        with torch.no_grad():
            outputs = self.literal_model(input_ids, labels=labels)
        logits = outputs[1]
        result = np.argmax(logits.detach().numpy(),axis=1)[0]
        if result == 0:
            categoryLabel = 'Date'
        elif result == 1:
            categoryLabel = 'Number'
        else:
            categoryLabel = 'String'
        return categoryLabel
        
    def getFluencyScore(self,question):
        """
        Method that gets the fluency score of a question.
        """
        return self.fluencyScoreModel.score(question, bos = True, eos = True)
    