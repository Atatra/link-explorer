import streamlit as st
import requests
import logging
from streamlit_star_rating import st_star_rating


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Liste des modèles disponibles
models = {
    'v1': 'T5-Small de FalconsAi',
    'v2': 'distilBart fine-tuned',
    'v3': 'T5-Small fine-tuned'
}

sorted_models = dict(sorted(models.items(), key=lambda item: item[1]))

# App Title
st.title("Link Explorer")

# Description
st.write("Le but de cette application est de résumer le contenu d'une page web en quelques phrases. Pour cela, il suffit de renseigner l'URL de la page à explorer et l'application se charge de résumer le contenu de la page.")

# Initialize session state
if 'given_link' not in st.session_state:
    st.session_state['given_link'] = None

if 'last_summary' not in st.session_state:
    st.session_state['last_summary'] = None

if 'last_link' not in st.session_state:
    st.session_state['last_link'] = None

if 'feedback_sent' not in st.session_state:
    st.session_state['feedback_sent'] = False

if 'original_text' not in st.session_state:
    st.session_state['original_text'] = None

if 'show_original' not in st.session_state:
    st.session_state['show_original'] = False

if 'chosen_model' not in st.session_state:
    st.session_state['chosen_model'] = 'v1'

def update_model():
    st.session_state['chosen_model'] = st.session_state['model_selector']
    st.session_state['given_link'] = None  # Reset the input to trigger a refresh


def predict_url_content(url):
    api_url = "http://serving-api:8080/summary"
    params = {'url': url, 'version': st.session_state['chosen_model']}
    try:
        response = requests.post(api_url, params=params)
        response.raise_for_status()
        result = response.json()
        summary = result.get('summary', None)
        original = result.get('original', None)
        
        if summary:
            st.session_state['last_summary'] = summary
            st.session_state['original_text'] = original
        else:
            st.error("L'API n'a pas renvoyé de résumé valide.")
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            error_message = response.json().get("detail", "Unknown error")
            st.error(f"{error_message}")
        else:
            st.error(f"Erreur HTTP : {http_err}")
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la connexion à l'API : {e}")

def send_feedback(url, summary, rating):
    api_url = "http://serving-api:8080/feedback"
    data = {
        'url': url,
        'summary': summary,
        'rating': rating,
        'version': st.session_state['chosen_model']
    }
    try:
        response = requests.post(api_url, json=data)
        response.raise_for_status()
        st.session_state['feedback_sent'] = True
        st.success("Feedback envoyé avec succès !")
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la connexion à l'API : {e}")

def feedback_section(summary, url):
    st.write("## Feedback")
    
    if st.session_state['feedback_sent']:
        st.success("Votre feedback a déjà été envoyé ! Merci.")
        return

    with st.form("feedback_form"):
        rating = st_star_rating(label = "Donnez une note à la qualité du résumé :", maxValue = 5, defaultValue = 3, key = "rating", size = 20)
        submitted = st.form_submit_button("Envoyer le feedback")
        
        if submitted:
            send_feedback(url, summary, rating)
            st.session_state['feedback_sent'] = True

# Select model
st.selectbox(
    "Choisissez le modèle de résumé à utiliser :", 
    list(sorted_models.keys()), 
    format_func=lambda x: models[x], 
    key="model_selector",  # Use a different key to track changes
    on_change=update_model  # Call the function when model changes
)

# Input URL
given_link = st.text_input("URL de la page à explorer")

if given_link:
    if given_link.startswith("http://") or given_link.startswith("https://"):
        if st.session_state['given_link'] != given_link:
            with st.spinner("Résumé en cours de génération..."):
                predict_url_content(given_link)
                st.session_state['given_link'] = given_link
                st.session_state['last_link'] = given_link
                st.session_state['show_original'] = False
                st.session_state['feedback_sent'] = False
    else:
        st.error("Veuillez fournir une URL valide commençant par http:// ou https://")
else:
    st.info("Entrez une URL pour commencer.")

if st.session_state['last_summary']:
    st.write("### Résumé :")
    st.success(st.session_state['last_summary'])
    
    # Button to toggle original text
    if st.button("Afficher le texte original"):
        st.session_state['show_original'] = not st.session_state['show_original']
    
    if st.session_state['show_original'] and st.session_state['original_text']:
        st.write("### Texte Original :")
        st.text_area("Contenu Original", st.session_state['original_text'], height=300)
    
    feedback_section(st.session_state['last_summary'], st.session_state['last_link'])
