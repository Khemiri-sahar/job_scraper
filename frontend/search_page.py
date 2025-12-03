import streamlit as st
import requests  

def search_page():
    st.title("Chercher des offres d'emploi")

    if st.button("Se déconnecter"):
        st.session_state['logged_in'] = False
        st.rerun()


    with st.sidebar:
        st.header("⚙️ Configuration")
        
        backend_url = st.text_input(
            "URL du Backend",
            value="http://127.0.0.1:8000/recommend",
            help="L'adresse de votre API FastAPI"
        )
        
        st.divider()
        
        st.subheader("Statut du Backend")
        try:
            response = requests.get("http://127.0.0.1:8000/", timeout=2)
            if response.status_code == 200:
                data = response.json()
                st.success("Backend en ligne")
                st.caption(f"Jobs disponibles: {data.get('total_jobs', 'N/A')}")
            else:
                st.warning("Backend répond mais avec erreur")
        except requests.exceptions.ConnectionError:
            st.error("Backend hors ligne")
            st.caption("Démarrez avec:")
            st.code("uvicorn main:app --reload")
        except Exception as e:
            st.error(f"Erreur: {str(e)}")
        
    st.write("Dites nous ce que vous cherchez ..." )
    
    query = st.text_input("Votre recherche")
    num_results = st.number_input("Nombre de résultats", min_value=1, max_value=50, value=5)
    
    if st.button("🔎 Chercher des annonces"):
        if query.strip():
            with st.spinner("🔄 Recherche en cours..."):  
                try:
                    # REAL API 
                    response = requests.post(
                        backend_url,
                        json={
                            "text": query,
                            "top_k": num_results
                        },
                        timeout=30  
                    )
                    
                    if response.status_code == 200:
                        job_offers = response.json()
                        
                        if job_offers:
                            st.success(f"{len(job_offers)} offres trouvées!")
                            st.subheader("Résultats de recherche:")
                            
                            for i, job in enumerate(job_offers, 1):
                                with st.container():
                                    col1, col2 = st.columns([3, 1])
                                    
                                    with col1:
                                        st.markdown(f"### {i}. {job.get('title', 'N/A')}")
                                        st.write(f"**Entreprise:** {job.get('company', 'N/A')}")
                                        st.write(f"**Secteur:** {job.get('sector', 'N/A')}")
                                    
                                    with col2:
                                        st.metric("Salaire", job.get('salary', 'N/A'))
                                    
                                    st.divider()
                        else:
                            st.info("Aucune offre trouvée pour cette recherche")
                    
                    elif response.status_code == 500:
                        st.error("Erreur du serveur backend")
                        with st.expander("Voir les détails"):
                            st.code(response.text)
                    
                    else:
                        st.error(f"Erreur API: Code {response.status_code}")
                        st.code(response.text)
                
                except requests.exceptions.ConnectionError:
                    st.error("Impossible de se connecter au backend!")
                    st.warning("Vérifiez que le backend est en cours d'exécution:")
                    
                
                except requests.exceptions.Timeout:
                    st.error("⏱Le backend met trop de temps à répondre")
                    st.info("Le modèle peut prendre du temps à charger la première fois")
                
                except Exception as e:
                    st.error(f"Erreur inattendue: {str(e)}")
                    with st.expander("Détails de l'erreur"):
                        st.exception(e)
        else:
            st.warning("Veuillez entrer une recherche")