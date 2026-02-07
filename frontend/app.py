import streamlit as st
import requests
from pathlib import Path
import os

API_URL = os.getenv('API_URL', 'http://localhost:8000')


def init_session():
    if 'token' not in st.session_state:
        st.session_state['token'] = None
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'confirm_reset' not in st.session_state:
        st.session_state['confirm_reset'] = False


def auth_headers():
    token = st.session_state.get('token')
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def layout():
    init_session()
    st.markdown("#  RAG Model")
    
    with st.sidebar:
        st.markdown("## Account")
        if st.session_state.get('token'):
            st.markdown(f"**Signed in as:** {st.session_state.get('username')}")
            if st.button("Logout", key='logout'):
                st.session_state['token'] = None
                st.session_state['username'] = None
                st.rerun()
        else:
            action = st.radio('Action', ['Login', 'Register'], key='auth_action')
            if action == 'Login':
                uname = st.text_input('Username', key='login_user')
                pwd = st.text_input('Password', type='password', key='login_pass')
                if st.button('Login', key='login_btn'):
                    try:
                        resp = requests.post(f"{API_URL}/auth/login", json={"username": uname, "password": pwd})
                        if resp.status_code == 200:
                            token = resp.json().get('access_token')
                            st.session_state['token'] = token
                            st.session_state['username'] = uname
                            st.success('Logged in')
                            st.rerun()
                        else:
                            st.error('Login failed')
                    except Exception as e:
                        st.error(f'Login error: {e}')
            else:
                rune = st.text_input('Choose username', key='reg_user')
                rpwd = st.text_input('Choose password', type='password', key='reg_pass')
                if st.button('Register', key='register_btn'):
                    try:
                        resp = requests.post(f"{API_URL}/auth/register", json={"username": rune, "password": rpwd})
                        if resp.status_code == 200:
                            st.success('Registered — please login')
                        else:
                            st.error('Registration failed')
                    except Exception as e:
                        st.error(f'Registration error: {e}')

    st.markdown("---")
    st.markdown("## 📚 Manage Documents")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Reset All", type="secondary", key='reset_all'):
            if st.session_state.get('confirm_reset'):
                response = requests.post(f'{API_URL}/rag/reset', headers=auth_headers())
                if response.status_code == 200:
                    st.success("✅ Knowledge base reset!")
                    st.session_state['confirm_reset'] = False
                    st.rerun()
                else:
                    try:
                        st.error(f"Failed to reset: {response.json().get('detail')}")
                    except Exception:
                        st.error(f"Failed to reset: {response.status_code}")
            else:
                st.session_state['confirm_reset'] = True
                st.warning("⚠️ Click again to confirm complete reset")

    if not st.session_state.get('confirm_reset'):
        try:
            response = requests.get(f'{API_URL}/rag/documents', headers=auth_headers())
            if response.status_code == 200:
                docs = response.json().get('documents', [])
                
                if docs:
                    st.markdown(f"**Total documents: {len(docs)}**")
                    for doc in docs:
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.text(f"📄 {doc['filename']}")
                        with c2:
                            if st.button("🗑️", key=f"delete_{doc['doc_id']}"):
                                delete_response = requests.delete(f"{API_URL}/rag/documents/{doc['doc_id']}", headers=auth_headers())
                                if delete_response.status_code == 200:
                                    st.success(f"Deleted {doc['filename']}")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete")
                else:
                    st.info("No documents in the knowledge base yet.")
            else:
                if response.status_code == 401:
                    st.warning("Not authenticated — please login via the sidebar")
                else:
                    st.warning("Could not load documents")
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")

    st.markdown("---")
    st.markdown("## Upload PDF Documents")
    uploaded_file = st.file_uploader("Upload a PDF to add to knowledge base", type=['pdf'])

    if uploaded_file is not None:
        with st.form(key="upload_form", clear_on_submit=True):
            submit = st.form_submit_button("Process PDF")
            if submit:
                with st.spinner("Processing and ingesting document..."):
                    files = {'file': (uploaded_file.name, uploaded_file, 'application/pdf')}
                    try:
                        response = requests.post(f'{API_URL}/rag/upload', files=files, headers=auth_headers())
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ {data['message']}", icon="✅")
                        else:
                            try:
                                error_data = response.json()
                                st.error(f"❌ Upload failed: {error_data.get('detail', 'Unknown error')}")
                            except Exception:
                                st.error(f"❌ Upload failed: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    st.markdown("---")
    st.markdown("## Ask Questions")
    st.markdown("What would you like to know about your documents?")

    with st.form(key="query_form", clear_on_submit=False):
        text_input = st.text_input(label="Ask a question")
        submit = st.form_submit_button("Send")
        
        if submit and text_input.strip() != '':
            with st.spinner("Searching and generating answer..."):
                try:
                    response = requests.post(f'{API_URL}/rag/query',json={"prompt":text_input}, headers=auth_headers())
                    
                    if response.status_code == 200:
                        data = response.json()

                        st.markdown("## Question:")
                        st.markdown(text_input)

                        st.markdown("## Answer:")
                        st.markdown(data.get('answer', ''))

                        st.markdown("## Source:")
                        st.markdown(data.get('filepath', ''))
                    else:
                        st.error(f"❌ Query failed: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def show_about():
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown("# 📖 RAG Assistant")
        st.markdown("**Your AI-powered document analysis tool**")
    
    st.markdown("---")
    
    st.markdown("""
    ### What is this?
    
    A smarter way to work with your documents. Instead of scrolling through PDFs, just ask questions and get instant answers.
    
    **How it works:**
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📤 Upload")
        st.markdown("Add your PDFs to the knowledge base")
    with col2:
        st.markdown("### 🔍 Search")
        st.markdown("Ask questions in plain English")
    with col3:
        st.markdown("### 💡 Answer")
        st.markdown("Get AI-powered responses instantly")
    
    st.markdown("---")
    
    st.markdown("### Contact & Connect")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("📧 **Email**")
        st.markdown("[08amrit@gmail.com](mailto:08amrit@gmail.com)")
    
    with col2:
        st.markdown("💼 **LinkedIn**")
        st.markdown("[Amrit Bhaganagare](https://www.linkedin.com/in/amrit-bhaganagare/)")
    
    with col3:
        st.markdown("💻 **GitHub**")
        st.markdown("[Amrit-B](https://github.com/Amrit-B)")
    
    st.markdown("---")
    st.markdown("*Built with FastAPI, Streamlit, LanceDB, Docker, Sentence Transformers, and Google Gemini API*")

if __name__=="__main__":
    st.set_page_config(page_title="RAG Assistant", layout="wide", initial_sidebar_state="expanded")

    tab1, tab2 = st.tabs(["🤖 RAG Assistant", "📖 About"])

    with tab1:
        layout()

    with tab2:
        show_about()