# Banglish to Bengali Transliteration

import torch
import pandas as pd
import numpy as np
from datasets import load_dataset
from transformers import (
    AutoTokenizer, 
    MBartForConditionalGeneration,  # Corrected model class name
    DataCollatorForSeq2Seq,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer
)
from sklearn.model_selection import train_test_split
import evaluate
import wandb

# 1. Load and Prepare Dataset
def load_bengali_dataset():
    """
    Load the Bengali transliteration dataset from Hugging Face
    """
    dataset = load_dataset("SKNahin/bengali-transliteration-data")
    return dataset

def prepare_dataset(dataset):
    """
    Split dataset into train and validation sets
    """
    train_data = dataset['train']
    
    # Convert to pandas for easier handling
    df = pd.DataFrame({
        'banglish': train_data['banglish'],
        'bangla': train_data['bangla']
    })
    
    # Split into train and validation
    train_df, val_df = train_test_split(
        df, 
        test_size=0.1, 
        random_state=42
    )
    
    return train_df, val_df

# 2. Data Preprocessing
def preprocess_function(examples, tokenizer, max_length=128):
    """
    Tokenize the input and target texts
    """
    inputs = [text for text in examples['banglish']]
    targets = [text for text in examples['bangla']]
    
    model_inputs = tokenizer(
        inputs, 
        max_length=max_length,
        padding='max_length',
        truncation=True
    )
    
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            targets,
            max_length=max_length,
            padding='max_length',
            truncation=True
        )
    
    model_inputs['labels'] = labels['input_ids']
    return model_inputs

class BengaliDataset(torch.utils.data.Dataset):
    """
    Custom dataset class for Bengali transliteration
    """
    def __init__(self, df, tokenizer, max_length=128):
        self.df = df
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        inputs = self.tokenizer(
            row['banglish'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        with self.tokenizer.as_target_tokenizer():
            labels = self.tokenizer(
                row['bangla'],
                max_length=self.max_length,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
        
        return {
            'input_ids': inputs['input_ids'].squeeze(),
            'attention_mask': inputs['attention_mask'].squeeze(),
            'labels': labels['input_ids'].squeeze()
        }

# 3. Model Selection and Training
def initialize_model():
    """
    Initialize the mBART model and tokenizer
    """
    model_name = "facebook/mbart-large-cc25"  # This model supports multiple languages including Bengali
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = MBartForConditionalGeneration.from_pretrained(model_name)  # Using correct model class
    
    # Add special tokens for Banglish if needed
    special_tokens = {"additional_special_tokens": ["<banglish>", "<bangla>"]}
    tokenizer.add_special_tokens(special_tokens)
    model.resize_token_embeddings(len(tokenizer))
    
    return model, tokenizer

def compute_metrics(eval_preds):
    """
    Compute evaluation metrics
    """
    predictions, labels = eval_preds
    # Decode predictions and labels
    predictions = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    
    # Calculate BLEU score
    metric = evaluate.load("sacrebleu")
    results = metric.compute(predictions=predictions, references=[[l] for l in labels])
    
    return {
        "bleu": results["score"]
    }

def train_model(model, tokenizer, train_dataset, val_dataset):
    """
    Train the model using Hugging Face's Trainer
    """
    training_args = Seq2SeqTrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        weight_decay=0.01,
        save_total_limit=3,
        num_train_epochs=3,
        predict_with_generate=True,
        report_to="wandb"
    )
    
    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)
    
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )
    
    trainer.train()
    return trainer

# 4. Main Execution
if __name__ == "__main__":
    # Initialize wandb
    wandb.init(project="banglish-bengali-transliteration")
    
    # Load dataset
    dataset = load_bengali_dataset()
    train_df, val_df = prepare_dataset(dataset)
    
    # Initialize model and tokenizer
    model, tokenizer = initialize_model()
    
    # Create datasets
    train_dataset = BengaliDataset(train_df, tokenizer)
    val_dataset = BengaliDataset(val_df, tokenizer)
    
    # Train model
    trainer = train_model(model, tokenizer, train_dataset, val_dataset)
    
    # Save model
    model_path = "./banglish_bengali_translator"
    trainer.save_model(model_path)
    tokenizer.save_pretrained(model_path)
    
    # Test the model
    def translate_text(text):
        inputs = tokenizer(text, return_tensors="pt", padding=True)
        outputs = model.generate(**inputs)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Example usage
    test_text = "ami tomake bhalobashi"
    translated = translate_text(test_text)
    print(f"Input: {test_text}")
    print(f"Translation: {translated}")

# 5. Utility Functions for Inference
def load_saved_model(model_path):
    """
    Load a saved model and tokenizer
    """
    model = MBartForConditionalGeneration.from_pretrained(model_path)  # Using correct model class
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    return model, tokenizer

def transliterate(text, model, tokenizer):
    """
    Transliterate Banglish text to Bengali
    """
    inputs = tokenizer(text, return_tensors="pt", padding=True)
    outputs = model.generate(**inputs)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)