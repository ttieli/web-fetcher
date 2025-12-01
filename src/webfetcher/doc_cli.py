#!/usr/bin/env python3
"""
wdoc - Document to Markdown converter CLI
Convert local documents (.docx) to Markdown.
"""
import sys
import os
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('wdoc')

def main():
    parser = argparse.ArgumentParser(
        description="Convert local documents to Markdown (wdoc)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wdoc document.docx                 # Convert to document.md
  wdoc document.docx -o output/      # Save to output directory
  wdoc document.docx -o readme.md    # Save with specific filename
"""
    )
    
    parser.add_argument("input_file", help="Path to the input file (.docx)")
    parser.add_argument("-o", "--output", help="Output file path or directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Error: Input file '{input_path}' not found.")
        sys.exit(1)
        
    # Determine output path
    if args.output:
        out_arg = Path(args.output)
        if out_arg.is_dir() or args.output.endswith('/') or args.output.endswith(os.sep):
            # It's a directory
            out_dir = out_arg
            out_dir.mkdir(parents=True, exist_ok=True)
            out_filename = input_path.stem + ".md"
            output_path = out_dir / out_filename
        else:
            # It's a file path
            output_path = out_arg
            # Ensure parent dir exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Default: same name, same directory as input (or current dir?)
        # Let's default to current directory to avoid cluttering source folders if different
        output_path = Path.cwd() / (input_path.stem + ".md")

    logger.info(f"Converting '{input_path}'...")
    
    try:
        # Import converter here to avoid startup lag if just showing help
        from webfetcher.converters.docx_converter import convert_docx_to_markdown
        
        temp_docx_path = None

        if input_path.suffix.lower() == '.docx':
            markdown_content = convert_docx_to_markdown(str(input_path))
        elif input_path.suffix.lower() == '.doc':
            logger.info("Detected legacy .doc format. Attempting conversion via LibreOffice...")
            import subprocess
            import shutil
            import tempfile

            # Find soffice executable
            soffice = shutil.which('soffice')
            if not soffice:
                # Check standard macOS location
                mac_soffice = '/Applications/LibreOffice.app/Contents/MacOS/soffice'
                if os.path.exists(mac_soffice):
                    soffice = mac_soffice
            
            if not soffice:
                logger.error("Error: LibreOffice (soffice) not found.")
                logger.info("Please install LibreOffice or add 'soffice' to your PATH to support .doc files.")
                sys.exit(1)

            # Create a temporary directory for the conversion output
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"Converting .doc to .docx using: {soffice}")
                try:
                    # Run conversion
                    # soffice --headless --convert-to docx --outdir <dir> <file>
                    cmd = [
                        soffice,
                        '--headless',
                        '--convert-to', 'docx',
                        '--outdir', temp_dir,
                        str(input_path)
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"LibreOffice conversion failed (code {result.returncode})")
                        if args.verbose:
                            logger.error(f"Stderr: {result.stderr}")
                        raise Exception("LibreOffice conversion failed")

                    # Find the generated .docx file
                    generated_files = list(Path(temp_dir).glob('*.docx'))
                    if not generated_files:
                        raise Exception("LibreOffice did not generate a .docx file")
                    
                    temp_docx_path = generated_files[0]
                    logger.info(f"Intermediate conversion successful: {temp_docx_path.name}")
                    
                    # Now process the temporary .docx
                    markdown_content = convert_docx_to_markdown(str(temp_docx_path))
                    
                except Exception as e:
                    logger.error(f"Legacy conversion error: {e}")
                    sys.exit(1)
        else:
            logger.error(f"Unsupported file format: {input_path.suffix}")
            logger.info("Currently supported formats: .docx, .doc (requires LibreOffice)")
            sys.exit(1)
            
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        logger.info(f"✓ Successfully converted to: {output_path}")
        
    except ImportError as e:
        logger.error(f"Dependency error: {e}")
        logger.info("Please reinstall the package to get new dependencies.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
