import streamlit as st
import requests

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
                
                function_url = "https://images-service.azurewebsites.net/api/upload" 
                
                response = requests.post(function_url, files=files)
                
                if response.status_code == 200:
                    st.success(response.text)
                else:
                    st.error(f"Błąd serwera: {response.text}")
                    
            except Exception as e:
                st.error(f"Błąd połączenia: {e}")