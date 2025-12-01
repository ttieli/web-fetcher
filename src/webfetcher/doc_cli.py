#!/usr/bin/env python3
"""
wd - Document Converter CLI
Convert .doc files to .docx, and optionally .docx to Markdown.
"""
import sys
import os
import argparse
from pathlib import Path
import logging
import subprocess
import shutil
import tempfile
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('wd')

def find_soffice() -> Optional[Path]:
    """Finds the soffice executable for LibreOffice conversion."""
    soffice_path = shutil.which('soffice')
    if soffice_path:
        return Path(soffice_path)
    
    # Check standard macOS location if not in PATH
    mac_soffice = Path('/Applications/LibreOffice.app/Contents/MacOS/soffice')
    if mac_soffice.exists():
        return mac_soffice
        
    return None

def main():
    parser = argparse.ArgumentParser(
        description="Convert .doc files to .docx, and optionally .docx to Markdown (wd)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
By default, 'wd' converts .doc files to .docx in the same directory.
Use the '--to-md' flag to convert to Markdown.

Examples:
  wd document.doc                    # Converts document.doc to document.docx
  wd document.doc -o output/         # Converts document.doc to output/document.docx
  wd document.docx --to-md           # Converts document.docx to document.md
  wd document.doc --to-md -o output/ # Converts document.doc to output/document.md
"""
    )
    
    parser.add_argument("input_file", help="Path to the input file (.doc or .docx)")
    parser.add_argument("-o", "--output", help="Output file path or directory")
    parser.add_argument("--to-md", action="store_true", 
                        help="Convert the document to Markdown. By default, .doc files are converted to .docx.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Error: Input file '{input_path}' not found.")
        sys.exit(1)
        
    # --- Determine target suffix and final output path ---
    target_suffix = ".md" if args.to_md else ".docx"
    final_output_path: Optional[Path] = None

    if args.output:
        out_arg = Path(args.output)
        if out_arg.is_dir() or args.output.endswith('/') or args.output.endswith(os.sep):
            # Output is a directory
            out_dir = out_arg
            out_dir.mkdir(parents=True, exist_ok=True)
            output_filename = input_path.stem + target_suffix
            final_output_path = out_dir / output_filename
        else:
            # Output is a specific file path
            final_output_path = out_arg
            final_output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # No output specified. Default to same dir as input, with new extension.
        final_output_path = input_path.parent / (input_path.stem + target_suffix)

    logger.info(f"Processing '{input_path}'...")
    
    docx_to_process: Optional[Path] = None
    delete_intermediate_docx = False
    
    try:
        from webfetcher.converters.docx_converter import convert_docx_to_markdown
        
        # --- Handle .doc to .docx conversion if necessary ---
        if input_path.suffix.lower() == '.doc':
            logger.info("Detected .doc format. Attempting conversion via LibreOffice...")
            soffice = find_soffice()
            if not soffice:
                logger.error("Error: LibreOffice (soffice) not found.")
                logger.info("Please install LibreOffice or add 'soffice' to your PATH to support .doc files.")
                sys.exit(1)

            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                logger.info(f"Converting .doc to .docx using: {soffice}")
                
                cmd = [
                    str(soffice),
                    '--headless',
                    '--convert-to', 'docx',
                    '--outdir', str(temp_dir),
                    str(input_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                
                if result.returncode != 0:
                    logger.error(f"LibreOffice conversion failed (code {result.returncode})")
                    if args.verbose:
                        logger.error(f"Stderr: {result.stderr}")
                    raise Exception("LibreOffice .doc to .docx conversion failed.")

                generated_files = list(temp_dir.glob('*.docx'))
                if not generated_files:
                    raise Exception("LibreOffice did not generate a .docx file.")
                
                docx_to_process = generated_files[0]
                logger.info(f"Intermediate .doc to .docx conversion successful: {docx_to_process.name}")
                delete_intermediate_docx = True # Mark for deletion after use

                # If the target is .docx and not .md, copy the generated docx and exit
                if not args.to_md:
                    shutil.copy(docx_to_process, final_output_path)
                    logger.info(f"✓ Successfully converted .doc to .docx: {final_output_path}")
                    sys.exit(0)

        elif input_path.suffix.lower() == '.docx':
            if not args.to_md:
                logger.info("Input is already a .docx file. No conversion performed by default. Use --to-md to convert to Markdown.")
                sys.exit(0)
            docx_to_process = input_path

        else:
            logger.error(f"Unsupported input file format: {input_path.suffix}")
            logger.info("Currently supported formats: .docx, .doc (requires LibreOffice)")
            sys.exit(1)

        # --- Proceed with Markdown conversion if --to-md is specified ---
        if args.to_md and docx_to_process:
            logger.info(f"Converting {docx_to_process.name} to Markdown...")
            markdown_content = convert_docx_to_markdown(str(docx_to_process))
            
            with open(final_output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
                
            logger.info(f"✓ Successfully converted to Markdown: {final_output_path}")
        elif docx_to_process:
            # This branch should only be reached if input was .docx and --to-md was not used,
            # which should have exited earlier. Or if .doc was processed and not to_md.
            # This is a fallback / safety check
            logger.info("No conversion action specified for .docx input without --to-md.")
            sys.exit(0)
        
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
    finally:
        # Cleanup intermediate .docx file if it was created temporarily
        if delete_intermediate_docx and docx_to_process and docx_to_process.exists():
            logger.debug(f"Cleaning up intermediate .docx file: {docx_to_process}")
            os.remove(docx_to_process)

if __name__ == '__main__':
    main()
