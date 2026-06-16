import streamlit as st
import requests
import os

from st_clickable_images import clickable_images

if "last_clicked" not in st.session_state:
    st.session_state.last_clicked = -1

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "gallery_key" not in st.session_state:
    st.session_state.gallery_key = 0

subscription_key = os.getenv("SUBSCRIPTION_KEY")
api_url = os.getenv("API_URL")

session = requests.Session()
session.headers.update({"Ocp-Apim-Subscription-Key": subscription_key})

@st.cache_data(ttl=300)
def fetch_gallery_images():
    resp = session.get(f"{api_url}/images")
    if resp.status_code == 200:
        return resp.json()
    else:
        return None

@st.dialog("Szczegóły obrazu", width="large")
def show_image_details(image_id):
    with st.spinner("Pobieranie danych o zdjęciu..."):
        try:
            resp = session.get(f"{api_url}/images/{image_id}")

            if resp.status_code == 200:
                data = resp.json()
                raw_tags = data.get("tags", [])

                if raw_tags and isinstance(raw_tags, list) and len(raw_tags) > 0:
                    tags = raw_tags[0].split(";")
                else:
                    tags = []

                col1, center_col, col3 = st.columns([1, 2, 1])
                
                with center_col:
                    st.image(data["url"], use_container_width=True)

                st.markdown("<h3 style='text-align: center;'>Tagi:</h3>", unsafe_allow_html=True)
                if tags:
                    tags_joined = " • ".join(tags)
                    st.markdown(f"<p style='text-align: center; font-size: 18px;'>{tags_joined}</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='text-align: center; color: gray;'>Brak przypisanych tagów.</p>", unsafe_allow_html=True)
            else:
                st.error(f"Nie udało się pobrać szczegółów (Kod: {resp.status_code}).")


            _, btn_col, _ = st.columns([1, 1, 1])
            with btn_col:
                if st.button("Usuń to zdjęcie", use_container_width=True, type="primary"):
                    with st.spinner("Usuwanie..."):
                        try:
                            del_resp = session.delete(f"{api_url}/images/{image_id}")
                            
                            if del_resp.status_code in [200, 204, 202]: 
                                fetch_gallery_images.clear() 
                                st.session_state.last_clicked = -1    
                                st.session_state.gallery_key += 1                      
                                st.rerun() 
                            else:
                                st.error(f"Nie udało się usunąć zdjęcia (Kod: {del_resp.status_code})")
                        except Exception as e:
                            st.error(f"Błąd podczas usuwania: {e}")
        except Exception as e:
            st.error(f"Błąd połączenia: {e}")


tab_upload, tab_gallery = st.tabs(["Wgrywanie zdjęcia", "Galeria"])

with tab_upload:
    st.title("Wgrywanie obrazu (Pillow & Multipart)")
    uploaded_file = st.file_uploader(
        "Wybierz zdjęcie",
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Podgląd")

        if st.button("Wyślij na Azure"):
            with st.spinner("Przetwarzanie..."):
                try:
                    files = {
                        "image": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }
                    response = session.post(f"{api_url}/images", files=files)

                    print(response.status_code)

                    if response.status_code == 200:
                        st.success(response.text)
                        st.session_state.uploader_key += 1
                    else:
                        st.error(f"Błąd serwera: {response.text}")

                except Exception as e:
                    st.error(f"Błąd połączenia: {e}")

with tab_gallery:
    st.header("Galeria")

    if st.button("Odśwież galerię"):
        fetch_gallery_images.clear()
        st.rerun()

    with st.spinner("Pobieranie zdjęć..."):
        try:
            images = fetch_gallery_images()

            if images is None:
                st.error("Nie udało się pobrać galerii. Sprawdź logi serwera.")
            elif not images:
                st.info("Brak zdjęć w galerii.")
            else:
                image_urls = [img["url"] for img in images]

                clicked_index = clickable_images(
                    image_urls,
                    titles=[
                        f"Kliknij, aby powiększyć zdjęcie {img.get('id')}"
                        for img in images
                    ],
                    div_style={
                        "display": "grid",
                        "grid-template-columns": "repeat(3, 1fr)",
                        "gap": "15px",
                    },
                    img_style={
                        "cursor": "pointer",
                        "width": "100%",
                        "border-radius": "8px",
                        "object-fit": "cover",
                        "height": "200px",
                    },
                    key=f"image_gallery_{st.session_state.gallery_key}"
                )
                
                if (clicked_index > -1
                    and clicked_index != st.session_state.last_clicked
                ):
                    st.session_state.last_clicked = clicked_index
                    selected_img = images[clicked_index]
                    show_image_details(selected_img["id"])
        except Exception as e:
            st.error(f"Błąd połączenia: {e}")
