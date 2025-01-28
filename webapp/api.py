import streamlit as st
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO : Peux être d'abord récuperer le code de la page web grâce au lien (et une API) pour ensuite le passer à l'API de résumé


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

def predict_url_content(url):
    api_url = "http://serving-api:8080/summary"
    params = {'url': url}
    try:
        response = requests.post(api_url, params=params)
        response.raise_for_status()
        result = response.json()
        summary = result.get('summary', None)
        original = result.get('original', None)
        if summary:
            st.session_state['last_summary'] = summary
            #st.success(summary)
        else:
            st.error("L'API n'a pas renvoyé de résumé valide.")
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la connexion à l'API : {e}")

# Version de predict_url_content pour tester l'affichage avec un résumé fixe
def predict_url_content_test(url):
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    st.session_state['last_summary'] = lorem

def send_feedback(url, summary, rating):
    api_url = "http://serving-api:8080/feedback"
    data = {
        'url': url,
        'summary': summary,
        'rating': rating
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
        st.write("### Donnez une note à la qualité du résumé :")
        rating = st.slider("Note (1 : Très mauvais, 5 : Excellent)", min_value=1, max_value=5, value=3)
        submitted = st.form_submit_button("Envoyer le feedback")

        if submitted:
            send_feedback(url, summary, rating)
            st.session_state['feedback_sent'] = True

# Input URL
given_link = st.text_input("URL de la page à explorer")

if given_link:
    if given_link.startswith("http://") or given_link.startswith("https://"):
        with st.spinner("Résumé en cours de génération..."):
            predict_url_content(given_link)
            st.session_state['given_link'] = given_link
            st.session_state['last_link'] = given_link
    else:
        st.error("Veuillez fournir une URL valide commençant par http:// ou https://")
else:
    st.info("Entrez une URL pour commencer.")

if st.session_state['last_summary']:
    st.write("### Résumé :")
    st.success(st.session_state['last_summary'])
    feedback_section(st.session_state['last_summary'], st.session_state['last_link'])
