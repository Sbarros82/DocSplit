"""
Interface de linha de comando (CLI) do Separador Inteligente de Documentos.

Uso:
    python cli.py <arquivo.pdf> <diretorio_saida>
    
Exemplo:
    python cli.py data/input/comprovantes.pdf data/output/comprovantes_separados/
"""

import sys
import argparse
import logging
from pathlib import Path
from src.pdf_splitter.pipeline import run_pipeline
from src.pdf_splitter.config import settings


def setup_logging(verbose: bool = False) -> None:
    """Configura logging do sistema."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def progress_callback(message: str, current: int, total: int) -> None:
    """Callback para exibir progresso no terminal."""
    percentage = int((current / total) * 100) if total > 0 else 0
    print(f"\r[{percentage:3d}%] {message}", end='', flush=True)
    if current == total:
        print()  # Nova linha ao completar


def main() -> int:
    """Ponto de entrada principal da CLI."""
    parser = argparse.ArgumentParser(
        description='Separador Inteligente de Documentos PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s entrada.pdf saida/
  %(prog)s --no-zip data/input/docs.pdf output/
  %(prog)s -v --no-preprocess arquivo.pdf resultado/
        """,
    )
    
    parser.add_argument(
        'input_pdf',
        type=str,
        help='Caminho do arquivo PDF de entrada',
    )
    
    parser.add_argument(
        'output_dir',
        type=str,
        help='Diretório de saída para documentos separados',
    )
    
    parser.add_argument(
        '--no-zip',
        action='store_true',
        help='Não criar arquivo ZIP com os documentos',
    )
    
    parser.add_argument(
        '--no-preprocess',
        action='store_true',
        help='Desabilitar pré-processamento de imagem antes do OCR',
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verboso (mais detalhes de log)',
    )
    
    args = parser.parse_args()
    
    # Setup
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validações básicas
    input_path = Path(args.input_pdf)
    if not input_path.exists():
        logger.error(f"Arquivo não encontrado: {input_path}")
        return 1
    
    if not input_path.suffix.lower() == '.pdf':
        logger.error(f"Arquivo deve ser PDF: {input_path}")
        return 1
    
    output_path = Path(args.output_dir)
    
    # Executar pipeline
    try:
        logger.info(f"Iniciando processamento de: {input_path}")
        logger.info(f"Saída em: {output_path}")
        
        exported_files = run_pipeline(
            input_pdf=input_path,
            output_dir=output_path,
            progress_callback=progress_callback,
            create_zip=not args.no_zip,
            enable_preprocessing=not args.no_preprocess,
        )
        
        # Resumo final
        print("\n" + "="*60)
        print("✓ Processamento concluído com sucesso!")
        print("="*60)
        print(f"Total de documentos identificados: {len(exported_files)}")
        print(f"Arquivos salvos em: {output_path}")
        
        # Listar alguns documentos
        if exported_files:
            print("\nPrimeiros documentos:")
            for i, file in enumerate(exported_files[:5], 1):
                pages = f"{file.start_page}-{file.end_page}" if file.start_page != file.end_page else str(file.start_page)
                supplier = file.supplier or "N/A"
                print(f"  {i}. {file.filename} - {file.doc_type} - {supplier} (páginas {pages})")
            
            if len(exported_files) > 5:
                print(f"  ... e mais {len(exported_files) - 5} documentos")
        
        print(f"\nVeja o índice completo em: {output_path / 'index.xlsx'}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Erro durante processamento: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
