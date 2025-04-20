import streamlit as st
import pandas as pd
import random
import requests
import math
import urllib.parse
from bs4 import BeautifulSoup

# ----- Funciones auxiliares -----
def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos
    usando la fórmula de Haversine.
    """
    R = 6371  # Radio de la Tierra en km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calcula el rumbo (bearing) desde (lat1, lon1) a (lat2, lon2) en grados.
    """
    if lat1 == lat2 and lon1 == lon2:
        return None

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlambda)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 180) % 360


def bearing_to_cardinal(bearing):
    """
    Convierte un rumbo en grados a un punto cardinal aproximado.
    """
    if bearing is None:
        return '✅'
    dirs = ['⬆️', '↗️', '➡️', '↘️', '⬇️', '↙️', '⬅️', '↖️']
    ix = int((bearing + 22.5) // 45)% 8
    return dirs[ix]


# ----- Carga de datos -----
@st.cache_data
def load_data(path='platos_nacionales_con_coords.csv'):
    """
    Se asume que el CSV tiene columnas: País, Plato Nacional, latitud, longitud
    """
    return pd.read_csv(path)

df = load_data()

# Inicializar juego
if 'answer_row' not in st.session_state:
    st.session_state.answer_row = df.sample(1).iloc[0]
    st.session_state.attempts = []
    st.session_state.finished = False

answer = st.session_state.answer_row['Country']
ans_lat = st.session_state.answer_row['latitud']
ans_lon = st.session_state.answer_row['longitud']
ans_dish = st.session_state.answer_row['Dish']

st.markdown(
        f"<span style='color:black; font-size:78px; background-color:#FFFFFF; padding:0px; display:block; width:100%; text-align:center;'><strong>GOURMLE<strong></span>",
        unsafe_allow_html=True)

st.markdown(
        f"<span style='color:grey; font-size:28px; background-color:#FFFFFF; padding:0px; display:block; width:100%; text-align:center;'><strong>Guess the country for its national dish<strong></span>",
        unsafe_allow_html=True)

def get_first_image_from_wikipedia(title):
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text",
        "redirects": True,
    }
    response = requests.get("https://en.wikipedia.org/w/api.php", params=params)
    data = response.json()

    try:
        html_content = data["parse"]["text"]["*"]
        soup = BeautifulSoup(html_content, "html.parser")

        # Buscar la primera imagen dentro del contenido del artículo
        first_img = soup.select_one(".infobox img")

        if first_img:
            # Wikipedia usa paths relativos, así que agregamos el host
            return "https:" + first_img["src"]
    except Exception as e:
        print("Error parsing image:", e)

    return ""

img_url = get_first_image_from_wikipedia(ans_dish)

if img_url:
    st.image(img_url, use_container_width=True)
    st.markdown(
        f"<span style='color:black; font-size:38px; background-color:#FFFFFF; padding:5px; display:block; width:100%; text-align:center;'>{str(ans_dish).replace("food","").replace("(","").replace(")","")}</span>",
        unsafe_allow_html=True)
else:
    st.write(f"**Dish:** {ans_dish}")

# Juego activo
if not st.session_state.finished:
    guess = st.selectbox("Elige tu país", sorted(df['Country'].unique()))
    if st.button("Adivinar"):
        dist = haversine(ans_lat, ans_lon,
                         df.loc[df['Country'] == guess, 'latitud'].iloc[0],
                         df.loc[df['Country'] == guess, 'longitud'].iloc[0])
        bearing = calculate_bearing(ans_lat, ans_lon,
                                    df.loc[df['Country'] == guess, 'latitud'].iloc[0],
                                    df.loc[df['Country'] == guess, 'longitud'].iloc[0])
        direction = bearing_to_cardinal(bearing)
        correct = (guess == answer)
        color = 'green' if correct else ('orange' if dist < 5000 else 'red')
        st.session_state.attempts.append({
            'guess': guess,
            'distance': dist,
            'direction': direction,
            'correct': correct,
            'color': color
        })
        # Marcar fin de juego
        if correct or len(st.session_state.attempts) >= 5:
            st.session_state.finished = True


# Crear 5 contenedores vacíos
containers = [st.container() for _ in range(5)]

# Rellenar los contenedores con los intentos
for i, att in enumerate(st.session_state.attempts):
    with containers[i]:
        col1, col2, col3 = st.columns([12, 3, 1])
        with col1:
            st.markdown(f"<span style='color:{att['color']}; font-size:18px; background-color:#f0f0f0; padding:5px; display:block; width:100%; text-align:center;'>{att['guess']}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color:{att['color']}; font-size:18px; background-color:#f0f0f0; padding:5px; display:block; width:100%; text-align:center;'>{att['distance']:.0f} km</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color:{att['color']}; font-size:18px; background-color:#f0f0f0; padding:5px; display:block; width:100%; text-align:center;'>{att['direction']}</span>", unsafe_allow_html=True)
# Rellenar los contenedores restantes con espacios vacíos
for i in range(len(st.session_state.attempts), 5):
    with containers[i]:
        st.markdown("<span style='color:gray; font-size:18px; background-color:#f0f0f0; padding:20px; display:block; width:100%; height:100'></span>", unsafe_allow_html=True)# Mensaje final
if st.session_state.finished:
    if any(att['correct'] for att in st.session_state.attempts):
        st.success(f"¡Correct!")
        st.balloons()
    else:
        st.error(f"You lose! The solution was: {answer}.")

    if st.button("Play again"):
        for key in ['answer_row', 'attempts', 'finished']:
            del st.session_state[key]
        st.rerun()
