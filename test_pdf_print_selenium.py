#!/usr/bin/env python3
"""
Test PDF print using Selenium + Chrome DevTools Protocol
DO NOT integrate - this is testing only
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import tempfile
import os
import time
import json

def test_selenium_pdf_print():
    url = "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"

    print("="*60)
    print("PDF Print Extraction Test using Selenium")
    print("="*60)
    print(f"Target URL: {url}\n")

    # Configure Chrome options
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    # Test both headless and headed modes
    results = []

    for headless_mode in [False, True]:
        print(f"\n{'='*60}")
        print(f"Testing with headless={headless_mode}")
        print(f"{'='*60}")

        if headless_mode:
            options.add_argument('--headless=new')  # Use new headless mode

        driver = webdriver.Chrome(options=options)

        try:
            # Navigate to page
            print("Navigating to URL...")
            driver.get(url)

            # Wait for page to load
            print("Waiting for page to render...")
            time.sleep(5)

            # Get page info
            title = driver.title
            page_source_length = len(driver.page_source)
            print(f"Page title: {title}")
            print(f"Page source length: {page_source_length:,} bytes")

            # Try to get visible text
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                print(f"Visible text length: {len(body_text)} characters")
                if body_text and len(body_text) < 500:
                    print(f"Visible text preview: {body_text[:200]}")
            except Exception as e:
                print(f"Could not get body text: {e}")
                body_text = ""

            # Take screenshot first
            screenshot_path = tempfile.mktemp(suffix=f'_selenium_{headless_mode}.png', prefix='cebbank_')
            driver.save_screenshot(screenshot_path)
            screenshot_size = os.path.getsize(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
            print(f"Screenshot size: {screenshot_size:,} bytes")

            # Print to PDF using Chrome DevTools Protocol
            print("\nGenerating PDF using Chrome DevTools Protocol...")

            # Execute CDP command to print PDF
            try:
                # Enable Page domain first
                driver.execute_cdp_cmd('Page.enable', {})

                # Print to PDF
                pdf_result = driver.execute_cdp_cmd('Page.printToPDF', {
                    'printBackground': True,
                    'landscape': False,
                    'paperWidth': 8.27,  # A4 width in inches
                    'paperHeight': 11.69, # A4 height in inches
                    'marginTop': 0.4,
                    'marginBottom': 0.4,
                    'marginLeft': 0.4,
                    'marginRight': 0.4,
                    'displayHeaderFooter': False,
                    'preferCSSPageSize': False,
                    'generateDocumentOutline': False
                })

                # Decode PDF data
                pdf_data = base64.b64decode(pdf_result['data'])

                # Save PDF
                fd, pdf_path = tempfile.mkstemp(suffix=f'_selenium_{headless_mode}.pdf', prefix='cebbank_')
                os.close(fd)

                with open(pdf_path, 'wb') as f:
                    f.write(pdf_data)

                pdf_size = os.path.getsize(pdf_path)
                print(f"PDF created: {pdf_path}")
                print(f"PDF size: {pdf_size:,} bytes")

                # Extract text from PDF
                print("\nAttempting text extraction from PDF...")
                extracted_text = extract_text_from_pdf(pdf_path)
                print(f"Text extracted: {len(extracted_text)} characters")

                if len(extracted_text) > 100:
                    print("\n=== First 500 chars of extracted text ===")
                    print(extracted_text[:500])
                    print("...")
                else:
                    print("WARNING: Very little or no text extracted from PDF")
                    if extracted_text:
                        print(f"Full text: {extracted_text}")

                result = {
                    'headless': headless_mode,
                    'pdf_size': pdf_size,
                    'screenshot_size': screenshot_size,
                    'page_source_length': page_source_length,
                    'visible_text_length': len(body_text),
                    'extracted_text_length': len(extracted_text),
                    'pdf_path': pdf_path,
                    'screenshot_path': screenshot_path,
                    'success': len(extracted_text) > 1000
                }

                results.append(result)

            except Exception as e:
                print(f"ERROR generating PDF: {e}")
                import traceback
                traceback.print_exc()
                results.append({'headless': headless_mode, 'error': str(e), 'success': False})

        except Exception as e:
            print(f"ERROR during test: {e}")
            import traceback
            traceback.print_exc()
            results.append({'headless': headless_mode, 'error': str(e), 'success': False})

        finally:
            driver.quit()
            if not headless_mode:
                # Remove headless argument for next iteration
                options._arguments = [arg for arg in options._arguments if not arg.startswith('--headless')]

    return results

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using available libraries"""
    text = ""

    # Try PyPDF2 first (most likely to be installed)
    try:
        import PyPDF2
        print("Using PyPDF2 for text extraction...")
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            print(f"PDF has {num_pages} page(s)")

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {i+1} ---\n{page_text}\n"

        if len(text.strip()) > 50:
            print(f"PyPDF2 extracted {len(text)} characters")
            return text
        else:
            print("PyPDF2 extracted little or no text")
    except ImportError:
        print("PyPDF2 not available")
    except Exception as e:
        print(f"PyPDF2 error: {e}")

    # Try pdfplumber if available
    try:
        import pdfplumber
        print("Using pdfplumber for text extraction...")
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            print(f"PDF has {num_pages} page(s)")

            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {i+1} ---\n{page_text}\n"

        if len(text.strip()) > 50:
            print(f"pdfplumber extracted {len(text)} characters")
            return text
    except ImportError:
        print("pdfplumber not available")
    except Exception as e:
        print(f"pdfplumber error: {e}")

    # If no text extracted
    if not text or len(text.strip()) < 50:
        print("WARNING: PDF appears to be image-based, empty, or libraries unavailable")
        print("Would need OCR (pytesseract + pdf2image) for image-based PDFs")

    return text

def analyze_pdf_metadata(pdf_path):
    """Analyze PDF metadata to understand its structure"""
    print("\n--- PDF Metadata Analysis ---")

    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)

            # Get metadata
            if reader.metadata:
                print("PDF Metadata:")
                for key, value in reader.metadata.items():
                    print(f"  {key}: {value}")

            # Check page dimensions
            if reader.pages:
                page = reader.pages[0]
                try:
                    width = float(page.mediabox.width)
                    height = float(page.mediabox.height)
                    print(f"Page dimensions: {width:.1f} x {height:.1f} points")
                except:
                    pass

            # Check for forms, annotations
            print(f"Number of pages: {len(reader.pages)}")

    except Exception as e:
        print(f"Could not analyze PDF metadata: {e}")

def main():
    print("="*60)
    print("Selenium PDF Print Extraction Test for CEB Bank Page")
    print("="*60)

    results = test_selenium_pdf_print()

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
            print(f"  Page Source Length: {result.get('page_source_length', 0):,} bytes")
            print(f"  Visible Text: {result.get('visible_text_length', 0):,} chars")
            print(f"  Extracted Text: {result.get('extracted_text_length', 0):,} chars")
            print(f"  Success: {'✅' if result.get('success') else '❌'}")

            if result.get('pdf_path'):
                print(f"  PDF Path: {result['pdf_path']}")
                # Analyze PDF structure
                if os.path.exists(result['pdf_path']):
                    analyze_pdf_metadata(result['pdf_path'])

            if result.get('screenshot_path'):
                print(f"  Screenshot: {result['screenshot_path']}")

    # Overall assessment
    print("\n" + "="*60)
    print("OVERALL ASSESSMENT")
    print("="*60)

    any_success = any(r.get('success', False) for r in results)
    all_pdfs_small = all(r.get('pdf_size', 0) < 10000 for r in results if 'pdf_size' in r)

    if any_success:
        print("✅ PDF extraction approach SUCCESSFUL - content can be extracted!")
        print("Recommendation: Implement PDF-based extraction as fallback method")
    elif all_pdfs_small:
        print("❌ PDF extraction approach FAILED")
        print("PDFs are too small (<10KB), likely empty or blocked")
        print("Server-level blocking confirmed - no client-side workaround possible")
    else:
        print("⚠️ PDF extraction approach PARTIALLY SUCCESSFUL")
        print("PDFs generated but text extraction failed")
        print("May need OCR for image-based content")

if __name__ == '__main__':
    main()