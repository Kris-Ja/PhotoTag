import streamlit as st
import requests
import os


subscription_key = os.getenv("SUBSCRIPTION_KEY")
session = requests.Session()
session.headers.update({'Ocp-Apim-Subscription-Key': subscription_key})


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
                
                function_url = "https://apim0f54dfec294a4f6e.azure-api.net/" 

                response = session.post(function_url, files=files)
                
                if response.status_code == 200:
                    st.success(response.text)
                else:
                    st.error(f"Błąd serwera: {response.text}")
                    
            except Exception as e:
                st.error(f"Błąd połączenia: {e}")
