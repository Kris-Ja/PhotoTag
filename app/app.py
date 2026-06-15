import streamlit as st
import requests
import os


subscription_key = os.getenv("SUBSCRIPTION_KEY")
session = requests.Session()
session.headers.update({'Ocp-Apim-Subscription-Key': subscription_key})

tab_upload, tab_gallery = st.tabs(["Wgrywanie zdjęcia", "Galeria"])

#API_BASE_URL = "https://apim000dd444778a9bb7.azure-api.net"
API_BASE_URL = "http://localhost:7071/api"

with tab_upload:
    st.title("Wgrywanie obrazu (Pillow & Multipart)")
    uploaded_file = st.file_uploader("Wybierz zdjęcie", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Podgląd")
        
        if st.button("Wyślij na Azure"):
            with st.spinner("Przetwarzanie..."):
                try:
                    files = {
                        "image": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                    }
                    response = session.post(API_BASE_URL, files=files)
                    
                    if response.status_code == 200:
                        st.success(response.text)
                    else:
                        st.error(f"Błąd serwera: {response.text}")
                        
                except Exception as e:
                    st.error(f"Błąd połączenia: {e}")

with tab_gallery:
    st.header("Galeria")

    st.button("Odśwież galerię")

    with st.spinner("Pobieranie zdjęć..."):
        try:
            resp = session.get(f"{API_BASE_URL}/images")

            print(resp.text)

            if resp.status_code == 200:
                images = resp.json()
                
                if not images:
                    st.info("Brak zdjęć w galerii.")
                else:
                    cols = st.columns(3)
                    for idx, img in enumerate(images):
                        with cols[idx % 3]:
                            st.image(img["url"], width='stretch')                     
            else:
                st.error("Nie udało się pobrać galerii.")
        except Exception as e:
            st.error(f"Błąd połączenia: {e}")
