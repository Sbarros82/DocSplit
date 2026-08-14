"""
Interface web com Streamlit (Fase 8 - opcional).

Aplicação simples para upload de PDF, processamento e download dos resultados.

TODO: Implementar apenas após pipeline CLI estiver estável (Fases 1-7).
"""

import streamlit as st
from pathlib import Path
import tempfile
import shutil
from src.pdf_splitter.pipeline import run_pipeline


def main():
    """Interface principal do Streamlit."""
    st.set_page_config(
        page_title="Separador Inteligente de Documentos",
        page_icon="📄",
        layout="wide",
    )
    
    st.title("📄 Separador Inteligente de Documentos PDF")
    st.markdown("""
    Faça upload de um PDF com múltiplos documentos misturados e receba
    arquivos separados, organizados e nomeados automaticamente.
    """)
    
    # Upload de arquivo
    uploaded_file = st.file_uploader(
        "Selecione o PDF para processar",
        type=['pdf'],
        help="PDF escaneado contendo múltiplos documentos (boletos, comprovantes, notas fiscais, etc.)",
    )
    
    if uploaded_file is not None:
        st.success(f"Arquivo carregado: {uploaded_file.name}")
        
        # Opções
        col1, col2 = st.columns(2)
        with col1:
            create_zip = st.checkbox("Gerar arquivo ZIP", value=True)
        with col2:
            enable_preprocessing = st.checkbox("Pré-processar imagens (melhora OCR)", value=True)
        
        # Botão de processar
        if st.button("🚀 Processar PDF", type="primary"):
            with st.spinner("Processando documento... Isso pode levar alguns minutos."):
                try:
                    # Criar diretório temporário
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_dir_path = Path(temp_dir)
                        
                        # Salvar upload
                        input_pdf = temp_dir_path / uploaded_file.name
                        with open(input_pdf, 'wb') as f:
                            f.write(uploaded_file.read())
                        
                        # Executar pipeline
                        output_dir = temp_dir_path / "output"
                        
                        # TODO: implementar progress bar real com callback
                        progress_bar = st.progress(0)
                        
                        exported_files = run_pipeline(
                            input_pdf=input_pdf,
                            output_dir=output_dir,
                            create_zip=create_zip,
                            enable_preprocessing=enable_preprocessing,
                        )
                        
                        progress_bar.progress(100)
                        
                        # Resultados
                        st.success(f"✓ Processamento concluído! {len(exported_files)} documentos identificados.")
                        
                        # TODO: exibir tabela com index_report
                        # TODO: botões de download para ZIP e/ou PDFs individuais
                        
                except Exception as e:
                    st.error(f"Erro durante processamento: {e}")


if __name__ == '__main__':
    main()
