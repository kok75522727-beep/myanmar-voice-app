"""Mg Khant အသံပြောင်းစနစ် Pro - Streamlit Voice Changer App."""

import base64
import streamlit as st
from streamlit_option_menu import option_menu

from voice_engine import (
    ALL_VOICES, EFFECTS, MYANMAR_VOICES, SPEED_OPTIONS, apply_effects,
    generate_tts, run_tts_to_file, change_tempo,
)

# ---------------------------------------------------------------------------
# Page config & login
# ---------------------------------------------------------------------------

ADMIN_PASSWORD = "saingmyanmar2026"

st.set_page_config(
    page_title="Mg Khant အသံပြောင်းစနစ် Pro",
    page_icon="🎙️",
    layout="wide",
)


def b64_audio(path):
    """Return base64-encoded audio data for the HTML audio player."""
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    mime = "audio/mpeg"
    return f'data:{mime};base64,{b64}'


def audio_player(path):
    st.audio(b64_audio(path), format="audio/mp3")


def login_screen():
    st.markdown("""
    <style>
    .login-box {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
        padding: 3rem 2.5rem;
        border-radius: 1.2rem;
        text-align: center;
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    }
    .login-box h1 { font-size: 2.4rem; margin-bottom: 0.4rem; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("# 🔐 Admin လျှို့ဝှက်နံပါတ်")
    st.markdown("### Mg Khant အသံပြောင်းစနစ် Pro")
    st.markdown("<br>", unsafe_allow_html=True)
    pwd = st.text_input("Password ကိုထည့်ပါ", type="password",
                        key="login_pwd")
    login_clicked = st.button("ဝင်ရောက်ရန်", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if login_clicked and pwd == ADMIN_PASSWORD:
        st.session_state.logged_in = True
        st.rerun()
    elif login_clicked:
        st.error("❌ မှားနေပါသည်။ Password ပြန်စစ်ပါ။")


# ---------------------------------------------------------------------------
# TTS page
# ---------------------------------------------------------------------------


def tts_page():
    st.header("🗣️ စာသားကနေ အသံထုတ်ခြင်း")
    st.markdown("စာသားထည့်ပြီး voice နဲ့ အသံပြင်ဆင်မှု ရွေးချယ်ပါ။")

    voice_group = st.select_slider(
        "Voice အုပ်စု ရွေးပါ",
        options=["🇲🇲 မြန်မာစကား", "🌏 အာရှဘာသာစကား", "🇺🇸 အင်္ဂလိပ်ဘာသာ", "အားလုံး"],
    )
    if voice_group == "🇲🇲 မြန်မာစကား":
        voices = MYANMAR_VOICES
    elif voice_group == "🌏 အာရှဘာသာစကား":
        voices = ALL_VOICES[2:10]
    elif voice_group == "🇺🇸 အင်္ဂလိပ်ဘာသာ":
        voices = ALL_VOICES[10:]
    else:
        voices = ALL_VOICES

    col1, col2 = st.columns(2)
    with col1:
        voice = st.selectbox("Voice ရွေးပါ",
                             [f"{label} ({sid})" for sid, label in voices])
        voice = voice.split(" (")[1].rstrip(")")
    with col2:
        speed = st.select_slider(
            "အသံအလျင် (Speed)",
            options=list(SPEED_OPTIONS.values()),
            format_func=lambda x: list(SPEED_OPTIONS.keys())[
                list(SPEED_OPTIONS.values()).index(x)],
            value="+0%",
        )

    text = st.text_area(
        "စာသားထည့်ပါ (မြန်မာ / အင်္ဂလိပ်)",
        value="မင်္ဂလာပါ၊ ဒီစနစ်က နေ သင့်စာသားကို အသံအမျိုးမျိုးနဲ့ ဖတ်ပေးပါတယ်။",
        height=180,
    )

    col3, col4 = st.columns(2)
    with col3:
        run_btn = st.button("🎧 အသံထုတ်ရန်", type="primary",
                            use_container_width=True)
    with col4:
        tempo = st.slider("နောက်ဆက် ပြင်ဆင်မှု - Tempo", 0.5, 2.0, 1.0, 0.05)

    if run_btn:
        if not text.strip():
            st.warning("⚠️ စာသားထည့်ပါ။")
        else:
            with st.spinner("⏳ အသံ generate လုပ်နေပါသည်..."):
                try:
                    out_path = run_tts_to_file(text, voice, speed,
                                               suffix="custom")
                    st.session_state.last_audio = out_path
                    st.success("✅ အသံဖန်တီးပြီးပါပြီ။")
                except Exception as e:
                    st.error(f"❌ အောင်မြင်စွာ မဖန်တီးနိုင်ပါ: {e}")

    if "last_audio" in st.session_state:
        st.markdown("---")
        st.subheader("🔊 ရလဒ်အသံ")
        audio_player(st.session_state.last_audio)
        st.download_button(
            "⬇️ အသံဖိုင် Download လုပ်ရန်",
            data=st.session_state.last_audio.read_bytes(),
            file_name="voice_output.mp3",
            mime="audio/mpeg",
        )


# ---------------------------------------------------------------------------
# Voice effects page
# ---------------------------------------------------------------------------


def effects_page():
    st.header("🎚️ အသံဖိုင် Effect ပြောင်းခြင်း")
    st.markdown("Audio ဖိုင် upload လုပ်ပြီး voice effect ရွေးပါ။")

    # Keep the uploaded file in session state: Streamlit reruns the whole
    # script on every widget change, which clears the file_uploader value.
    uploaded = st.file_uploader(
        "Audio ဖိုင်တင်ပါ (mp3 / wav)",
        type=["mp3", "wav", "ogg", "m4a"],
        key="audio_uploader",
    )
    if uploaded is not None:
        st.session_state.uploaded_name = uploaded.name
        st.session_state.uploaded_data = uploaded.read()

    if "uploaded_data" in st.session_state and st.session_state.uploaded_data:
        audio_data = st.session_state.uploaded_data
        input_path = f"/tmp/upload_{st.session_state.uploaded_name}"
        with open(input_path, "wb") as f:
            f.write(audio_data)

        st.subheader("📥 မူရင်းအသံ")
        st.audio(audio_data, format="audio/mp3")

        if "effect_select" not in st.session_state:
            st.session_state.effect_select = list(EFFECTS.keys())[0]
        if "tempo_slider" not in st.session_state:
            st.session_state.tempo_slider = 1.0

        effect = st.selectbox("Effect ရွေးပါ", list(EFFECTS.keys()),
                              index=list(EFFECTS.keys()).index(
                                  st.session_state.effect_select),
                              key="effect_select")
        extra_tempo = st.slider("Extra Speed ပြင်ဆင်မှု", 0.5, 2.0,
                                st.session_state.tempo_slider, 0.05,
                                key="tempo_slider")
        convert_clicked = st.button("🎛️ Effect ပြောင်းရန်", type="primary",
                                    use_container_width=True)

        if convert_clicked:
            with st.spinner("⏳ Effect ပြောင်းနေပါသည်..."):
                try:
                    out_path = apply_effects(input_path,
                                             st.session_state.effect_select,
                                             tempo=st.session_state.tempo_slider)
                    st.session_state.effect_audio = out_path
                    st.session_state.effect_name = st.session_state.effect_select
                    st.success("✅ Effect ပြောင်းပြီးပါပြီ။")
                except Exception as e:
                    st.error(f"❌ ပြောင်းနိုင်ခြင်း မရှိပါ: {e}")

        if "effect_audio" in st.session_state:
            st.markdown("---")
            st.subheader(f"🔊 ရလဒ် - {st.session_state.effect_name}")
            audio_player(st.session_state.effect_audio)
            st.download_button(
                "⬇️ အသံဖိုင် Download လုပ်ရန်",
                data=st.session_state.effect_audio.read_bytes(),
                file_name="voice_effect_output.mp3",
                mime="audio/mpeg",
            )


# ---------------------------------------------------------------------------
# About page
# ---------------------------------------------------------------------------


def about_page():
    st.header("ℹ️ App အကြောင်း")
    st.markdown("""
    ### Mg Khant အသံပြောင်းစနစ် Pro

    ဒီ app က **Python + Streamlit** framework နဲ့ ရေးထားတာဖြစ်ပြီး အောက်ပါ feature တွေ ပါဝင်ပါတယ်။

    | Feature | ဖော်ပြချက် |
    | --- | --- |
    | 🗣️ Text-to-Speech | စာသားကနေ အသံထုတ်ခြင်း (မြန်မာ၊ တရုပ်၊ ဂျပန်၊ ကိုးရီးယား၊ ထိုင်း၊ အင်္ဂလိပ် voice) |
    | 🎚️ Voice Effects | Upload လုပ်တဲ့ audio ကို effect ပြောင်းခြင်း (ချက်က်က်၊ နက်၊ ယောက်ကျား၊ ကလေး၊ ရိုဘက်၊ ရေအောက်၊ ရေဒီယို၊ giant၊ echo) |
    | ⚡ Speed Control | အသံအလျင် 0.5x မှ 2.0x အထိ ချိန်ဆည်းခြင်း |
    | ⬇️ Download | ဖန်တီးတဲ့ အသံဖိုင်တွေကို mp3 နဲ့ download လုပ်ခြင်း |

    **Technology Stack**
    - **Python** — ပင်မ programming language
    - **Streamlit** — web app framework
    - **edge-tts** — Microsoft အသံဖန်တီး engine (အခမဲ့)
    - **ffmpeg** — audio effect processing

    Developed with ❤️
    """)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------


def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_screen()
        return

    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🎙️ Mg Khant အသံပြောင်းစနစ် Pro")
        st.markdown("---")
        selected = option_menu(
            menu_title=None,
            options=["🗣️ အသံထုတ်ရန်", "🎚️ Effect ပြောင်းရန်", "ℹ️ အကြောင်း"],
            default_index=0,
        )
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    if selected == "🗣️ အသံထုတ်ရန်":
        tts_page()
    elif selected == "🎚️ Effect ပြောင်းရန်":
        effects_page()
    else:
        about_page()


if __name__ == "__main__":
    main()
  
