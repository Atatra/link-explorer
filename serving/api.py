# On first setup, the model FalconAI is downloaded from Huggingface and saved in the cache directory. (~5min)
# Don't delete the docker env or the model will be downloaded again.
# ~20s to generate a Wikipedia summary
# ~1min to generate a youtube video summary (<10min).
# Others depend on the page size.

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import joblib
import librosa
import io
import os

import requests
import re
from bs4 import BeautifulSoup
# For youtube
from youtube_transcript_api import YouTubeTranscriptApi
# For huggingface models
from transformers import pipeline
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

#import fct_model

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

MAX_LENGTH = 500 # Max length of the summary
MIN_LENGTH = 30

@app.on_event("startup")
def load_model():
  """ global summarizer """
  #summarizer = get_summarizer()
  global model, tokenizer, summarizer
  summarizer = get_summarizer("Falconsai/text_summarization")
  model, tokenizer = get_model_tokenizer()
    
@app.get("/")
def read_root(input):
  return {"message": f"Hello, {input}"}

@app.post("/summary")
async def summary(url: str, version: str = "v1"):
  """
    Return summary of link's content.
    - v1 for FalconsAI T5-small
    - v2 for our fine-tuned distilBart on a caption summary dataset
  """
  response = requests.get(url)
  soup = BeautifulSoup(response.text, 'html.parser')
  extracted_text = main_content_extractor(soup, url)
  if version == "v1":
    summary = generate_summary(extracted_text)
  else:
    summary = get_summary(extracted_text, model=model, tokenizer=tokenizer)
  return {"summary": summary, "original": extracted_text}

@app.post("/feedback")
async def feedback(background_tasks: BackgroundTasks, prediction, target, file: UploadFile = File(...)):
  global model, last_accuracy
  """
  Send feedback of model's prediction.
  Feedback is then saved in /data/prod_data.csv with embedding, target, and prediction.
  """
  return None

def main_content_extractor(soup, url):
  text = None
  
  if ("wikipedia" in url):
    # Find all p direct children of target_div
    target_div = soup.find('div', class_='mw-content-ltr mw-parser-output')
    paragraphs = " ".join([p.get_text() for p in target_div.find_all('p', recursive=False)]) # A revoir si on veut + de texte
    logger.info("Text: %s", paragraphs)
    
  elif ("youtube" in url): # Retreive transcript if exist
    video_id = url.split("v=")[1]
    try:
      transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
      paragraphs = " ".join([t['text'] for t in transcript])
    except:
      raise HTTPException(status_code=404, detail="No english transcript found for this video.")
    
  else: # Otherwise extract all text from page
    paragraphs = soup.get_text()
    
  text = preprocess(paragraphs)
  return text

def preprocess(text):
  """
    Preprocess text.
  """
  text = text.replace("\n", " ").replace("\t", " ")
  text = " ".join(text.split())  # Remove extra spaces
  text = text.replace('"', "'")
  text = re.sub(r'\[\d+\]', '', text)  # Remove citations
  text = re.sub(r'\[.*?\]', '', text) # Remove hyperlinks
  
  return text

def generate_summary(text):
  logger.info("Received a summarization request.")
  summary = summarizer(text, max_length=MAX_LENGTH, min_length=MIN_LENGTH, do_sample=False)[0]["summary_text"]
  return summary

def get_summarizer(model_name="claradlnv/distilbart-fine-tune"):
  cache_dir = "~/.cache/huggingface/hub/"  # Local directory to store models
  logger.info(f"Model is saved in '{cache_dir}'...")
  try:
    logger.info(f"Initializing summarizer with model '{model_name}'...")
    summarizer = pipeline("summarization", model=model_name)
    logger.info("Model loaded successfully.")
    return summarizer
  except Exception as e:
    logger.error(f"Failed to load the model: {e}")
    raise

def get_model_tokenizer(model_name="claradlnv/distilbart-fine-tune"):
  model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
  tokenizer = AutoTokenizer.from_pretrained(model_name)
  return model, tokenizer

def get_summary(text, tokenizer, model):
  inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=tokenizer.model_max_length).input_ids
  outputs = model.generate(inputs, max_new_tokens=150, do_sample=False)
  pred_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

  return pred_text