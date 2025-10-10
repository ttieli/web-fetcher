#!/usr/bin/env python3
"""
Test printing page to PDF with Playwright and extracting text
DO NOT integrate - this is testing only
"""
from playwright.sync_api import sync_playwright
import tempfile
import os
import time
import sys

def test_pdf_print_approach():
    url = "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"

    print(f"Testing PDF print approach for: {url}")

    with sync_playwright() as p:
        # Test both headless and headed modes
        results = []
        for headless_mode in [False, True]:
            print(f"\n{'='*60}")
            print(f"Testing with headless={headless_mode}")
            print(f"{'='*60}")

            browser = p.chromium.launch(
                headless=headless_mode,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )

            context = browser.new_context(
                ignore_https_errors=True,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = context.new_page()

            try:
                # Navigate to page
                print(f"Navigating to URL...")
                response = page.goto(url, wait_until='networkidle', timeout=30000)
                print(f"Response status: {response.status if response else 'No response'}")

                # Wait for rendering
                print("Waiting for page to fully render...")
                time.sleep(5)

                # Get page info
                title = page.title()
                html_length = len(page.content())
                print(f"Page title: {title}")
                print(f"HTML content length: {html_length} bytes")

                # Check for visible text on page
                visible_text = page.inner_text('body')
                print(f"Visible text length: {len(visible_text)} characters")
                if len(visible_text) > 0 and len(visible_text) < 500:
                    print(f"Visible text preview: {visible_text[:200]}")

                # Print to PDF
                print("\nGenerating PDF...")

                # Set print media CSS
                page.emulate_media(media='print')

                # Create temp PDF file
                fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f'cebbank_test_{headless_mode}_')
                os.close(fd)

                # Generate PDF
                page.pdf(
                    path=pdf_path,
                    format='A4',
                    print_background=True,
                    margin={'top': '1cm', 'right': '1cm', 'bottom': '1cm', 'left': '1cm'},
                    display_header_footer=False
                )

                # Check PDF size
                pdf_size = os.path.getsize(pdf_path)
                print(f"PDF created: {pdf_path}")
                print(f"PDF size: {pdf_size:,} bytes")

                # Also capture screenshot for comparison
                screenshot_path = pdf_path.replace('.pdf', '.png')
                page.screenshot(path=screenshot_path, full_page=True)
                screenshot_size = os.path.getsize(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
                print(f"Screenshot size: {screenshot_size:,} bytes")

                # Try to extract text from PDF
                print("\nAttempting text extraction from PDF...")
                text_content = extract_text_from_pdf(pdf_path)
                print(f"Text extracted: {len(text_content)} characters")

                if len(text_content) > 100:
                    print("\n=== First 500 chars of extracted text ===")
                    print(text_content[:500])
                    print("...")
                else:
                    print("WARNING: Very little or no text extracted from PDF")
                    if text_content:
                        print(f"Full text: {text_content}")

                result = {
                    'headless': headless_mode,
                    'pdf_size': pdf_size,
                    'screenshot_size': screenshot_size,
                    'html_length': html_length,
                    'visible_text_length': len(visible_text),
                    'extracted_text_length': len(text_content),
                    'pdf_path': pdf_path,
                    'screenshot_path': screenshot_path,
                    'success': len(text_content) > 1000
                }

                results.append(result)

            except Exception as e:
                print(f"ERROR during test: {e}")
                import traceback
                traceback.print_exc()
                results.append({'headless': headless_mode, 'error': str(e), 'success': False})

            finally:
                browser.close()

        return results

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using multiple methods"""
    text = ""

    # Method 1: Try pdfplumber (most reliable)
    try:
        import pdfplumber
        print("Using pdfplumber for text extraction...")
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF has {len(pdf.pages)} page(s)")
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {i+1} ---\n{page_text}\n"
        if len(text.strip()) > 50:
            print(f"pdfplumber extracted {len(text)} characters")
            return text
    except ImportError:
        print("pdfplumber not available, trying PyPDF2...")
    except Exception as e:
        print(f"pdfplumber error: {e}")

    # Method 2: Try PyPDF2
    try:
        import PyPDF2
        print("Using PyPDF2 for text extraction...")
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            print(f"PDF has {len(reader.pages)} page(s)")
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += f"--- Page {i+1} ---\n{page_text}\n"
        if len(text.strip()) > 50:
            print(f"PyPDF2 extracted {len(text)} characters")
            return text
    except ImportError:
        print("PyPDF2 not available")
    except Exception as e:
        print(f"PyPDF2 error: {e}")

    # Method 3: Try pymupdf (fitz)
    try:
        import fitz
        print("Using PyMuPDF for text extraction...")
        doc = fitz.open(pdf_path)
        print(f"PDF has {doc.page_count} page(s)")
        for i, page in enumerate(doc):
            page_text = page.get_text()
            text += f"--- Page {i+1} ---\n{page_text}\n"
        doc.close()
        if len(text.strip()) > 50:
            print(f"PyMuPDF extracted {len(text)} characters")
            return text
    except ImportError:
        print("PyMuPDF not available")
    except Exception as e:
        print(f"PyMuPDF error: {e}")

    # If no text extracted
    if not text or len(text.strip()) < 50:
        print("WARNING: PDF appears to be image-based or empty")
        print("OCR would be needed (pytesseract + pdf2image) for image-based PDFs")

    return text

def main():
    print("="*60)
    print("PDF Print Extraction Test for CEB Bank Page")
    print("="*60)

    results = test_pdf_print_approach()

    print("\n" + "="*60)
    print("FINAL RESULTS SUMMARY")
    print("="*60)

    for result in results:
        mode = "Headed" if not result.get('headless', True) else "Headless"
        print(f"\n{mode} Mode:")

        if 'error' in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            print(f"  PDF Size: {result.get('pdf_size', 0):,} bytes")
            print(f"  Screenshot Size: {result.get('screenshot_size', 0):,} bytes")
            print(f"  HTML Length: {result.get('html_length', 0):,} bytes")
            print(f"  Visible Text: {result.get('visible_text_length', 0):,} chars")
            print(f"  Extracted Text: {result.get('extracted_text_length', 0):,} chars")
            print(f"  Success: {'✅' if result.get('success') else '❌'}")

            if result.get('pdf_path'):
                print(f"  PDF Path: {result['pdf_path']}")
            if result.get('screenshot_path'):
                print(f"  Screenshot: {result['screenshot_path']}")

    # Overall assessment
    print("\n" + "="*60)
    print("OVERALL ASSESSMENT")
    print("="*60)

    any_success = any(r.get('success', False) for r in results)
    if any_success:
        print("✅ PDF extraction approach SUCCESSFUL - content can be extracted!")
    else:
        print("❌ PDF extraction approach FAILED - no meaningful content extracted")

if __name__ == '__main__':
    main()