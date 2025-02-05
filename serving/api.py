# On first setup, the model FalconAI is downloaded from Huggingface and saved in the cache directory. (~5min)
# Don't delete the docker env or the model will be downloaded again.
# ~20s to generate a Wikipedia summary
# ~1min to generate a youtube video summary (<10min).
# Others depend on the page size.

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import os
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
# For youtube
from youtube_transcript_api import YouTubeTranscriptApi
# For huggingface models
from transformers import pipeline
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import csv
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch


#import fct_model

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

MAX_LENGTH = 500 # Max length of the summary
MIN_LENGTH = 30
prod_path = "/data/prod_data.csv"

@app.on_event("startup")
def load_model():
  """ global summarizer """
  #summarizer = get_summarizer()
  global summarizerFalconT5, modelBart, tokenizerBart, modelT5, tokenizerT5, modelBartNew, tokenizerBartNew, modelT5New, tokenizerT5New
  summarizerFalconT5 = get_summarizer("Falconsai/text_summarization")
  modelBart, tokenizerBart = get_model_tokenizer(model_name="claradlnv/distilbart-fine-tune")
  modelT5, tokenizerT5 = get_model_tokenizer(model_name="maryemj/T5_Small_fineTuned")
  modelBartNew, tokenizerBartNew = get_model_tokenizer(model_name="claradlnv/fine-tuned-distilbart2")
  modelT5New, tokenizerT5New = get_model_tokenizer(model_name="Atatra/T5_Small_fineTuned2")

@app.get("/")
def read_root(input):
  return {"message": f"Hello, {input}"}

@app.post("/summary")
async def summary(url: str, version: str = "v1"):
  """
    Return summary of link's content.
    - v1 for FalconsAI T5-small
    - v2 for our fine-tuned distilBart on a caption summary dataset
    - v3 for our fine-tuned T5-Small on a caption summary dataset
    - V4 for our fine-tuned distilBart on our custom summary dataset
    - V5 for our fine-tuned T5-Small on our custom summary dataset
  """
  response = requests.get(url)
  # Vérifie si la requête a réussi (code 200)
  if response.status_code != 200:
    raise HTTPException(status_code=400, detail="Impossible de récupérer l'URL fournie.")
  soup = BeautifulSoup(response.text, 'html.parser')
  extracted_text = main_content_extractor(soup, url)
  # Vérifie que du texte a bien été extrait
  if not extracted_text or len(extracted_text) < 50:
    raise HTTPException(status_code=400, detail="Aucun contenu pertinent trouvé sur la page.")

  if version == "v1":
    summary = summarizerFalconT5(extracted_text, max_length=MAX_LENGTH, min_length=MIN_LENGTH, do_sample=False)[0]["summary_text"]
  elif version == "v2":
    summary = get_summary(extracted_text, model=modelBart, tokenizer=tokenizerBart)
  elif version == "v3":
    summary = generate_summary(extracted_text, model=modelT5, tokenizer=tokenizerT5)
  elif version == "v4":
    summary = generate_summary(extracted_text, model=modelBartNew, tokenizer=tokenizerBartNew)
  elif version == "v5":
    summary = generate_summary(extracted_text, model=modelT5New, tokenizer=tokenizerT5New)
  return {"summary": summary, "original": extracted_text}


@app.post("/feedback")
async def feedback(background_tasks: BackgroundTasks, request: Request):
  """
  Send feedback of model's prediction.
  Feedback is then saved in /data/prod_data.csv with full text, summary, and rating.
  """
  data = await request.json()
  url = data.get("url")
  # Client should send the full text, but for now...
  response = requests.get(url) 
  soup = BeautifulSoup(response.text, 'html.parser')
  full = main_content_extractor(soup, url)
  summary = data.get("summary")
  rating = data.get("rating")
  version = data.get("version")
  save_feedback(full, summary, rating, version, output_path=prod_path)

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

def get_model_tokenizer(model_name="maryemj/T5_Small_fineTuned"):
  """
  Charge le modèle et le tokenizer depuis Hugging Face.
  """
  logger.info(f"Initializing model and tokenizer with '{model_name}'...")
  try:

    if "T5" in model_name:
      model = T5ForConditionalGeneration.from_pretrained(model_name)
      tokenizer = T5Tokenizer.from_pretrained(model_name)
      logger.info("Model and tokenizer loaded successfully.")
      return model, tokenizer
    
    elif "distilbart" in model_name:
      model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
      tokenizer = AutoTokenizer.from_pretrained(model_name)
      return model, tokenizer
    
    else:
      logger.error("Model not supported")
      raise
    
  except Exception as e:
    logger.error(f"Failed to load the model and tokenizer: {e}")
    raise

def generate_summary(text, tokenizer, model):
  """
  Generate summary for T5-small fine-tuned
  """
  logger.info("Received a summarization request.")
  
  inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

  # Envoyer sur GPU si disponible
  device = "cuda" if torch.cuda.is_available() else "cpu"
  model.to(device)
  inputs = {key: value.to(device) for key, value in inputs.items()}

  outputs = model.generate(**inputs, max_length=MAX_LENGTH, min_length=MIN_LENGTH, do_sample=False)

  summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
  return summary

def get_summary(text, tokenizer, model):
  """
  Generate summary for distilBar fine-tuned
  """
  inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=tokenizer.model_max_length).input_ids
  outputs = model.generate(inputs, max_new_tokens=150, do_sample=False)
  pred_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
  return pred_text

def clean_input_data(data):
  return data.replace("\x00", "")  # Remove null characters

def save_feedback(full, summary, rating, version, output_path):
  full = clean_input_data(full)
  feedback_data = {"article": full, "abstract": summary, "rating": rating, "version": version}
  feedback_df = pd.DataFrame([feedback_data])
  file_exists_and_non_empty = os.path.isfile(output_path) and os.path.getsize(output_path) > 0
  feedback_df.to_csv(output_path, mode='a', header=not file_exists_and_non_empty, index=False,
                     quoting=csv.QUOTE_MINIMAL, encoding="utf-8")