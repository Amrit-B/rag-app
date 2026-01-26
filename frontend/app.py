import streamlit as st
import requests
from pathlib import Path

def layout():
    st.markdown("#  RAG Model")
    
    st.markdown("---")
    st.markdown("## 📚 Manage Documents")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Reset All", type="secondary"):
            if st.session_state.get('confirm_reset'):
                response = requests.post('http://localhost:8000/rag/reset')
                if response.status_code == 200:
                    st.success("✅ Knowledge base reset!")
                    st.session_state.confirm_reset = False
                    st.rerun()
                else:
                    st.error("Failed to reset")
            else:
                st.session_state.confirm_reset = True
                st.warning("⚠️ Click again to confirm complete reset")
    
    if not st.session_state.get('confirm_reset'):
        try:
            response = requests.get('http://localhost:8000/rag/documents')
            if response.status_code == 200:
                docs = response.json()['documents']
                
                if docs:
                    st.markdown(f"**Total documents: {len(docs)}**")
                    for doc in docs:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.text(f"📄 {doc['filename']}")
                        with col2:
                            if st.button("🗑️", key=f"delete_{doc['doc_id']}"):
                                delete_response = requests.delete(f"http://localhost:8000/rag/documents/{doc['doc_id']}")
                                if delete_response.status_code == 200:
                                    st.success(f"Deleted {doc['filename']}")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete")
                else:
                    st.info("No documents in the knowledge base yet.")
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
                        response = requests.post('http://localhost:8000/rag/upload', files=files)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ Successfully completed processing: {data['filename']}", icon="✅")
                        else:
                            error_data = response.json()
                            st.error(f"❌ Upload failed: {error_data.get('detail', 'Unknown error')}")
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
                    response = requests.post('http://localhost:8000/rag/query',json={"prompt":text_input})
                    
                    if response.status_code == 200:
                        data = response.json()

                        st.markdown("## Question:")
                        st.markdown(text_input)

                        st.markdown("## Answer:")
                        st.markdown(data['answer'])

                        st.markdown("## Source:")
                        st.markdown(data['filepath'])
                    else:
                        st.error(f"❌ Query failed: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

if __name__=="__main__":
    layout()