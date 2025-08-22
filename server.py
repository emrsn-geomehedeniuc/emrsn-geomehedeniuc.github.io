from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import qrcode
from PIL import Image
import os
import re
import io
import zipfile
import pandas as pd
import tempfile
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

app = FastAPI()

# ✅ Allow CORS for your frontend (modify if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔴 Allow requests from any origin (Use frontend URL in production)
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Allowed request methods
    allow_headers=["*"],  # Allowed request headers
)

# Create a directory to store generated QR codes
QR_CODE_DIR = "generated_qr_codes"
os.makedirs(QR_CODE_DIR, exist_ok=True)

# Define the directory where your index.html is located
# Assuming it's in the same directory as the server.py file
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

# Create a separate path for static files (images, CSS, JS)
STATIC_FILES_DIR = os.path.join(STATIC_DIR, "static")
os.makedirs(STATIC_FILES_DIR, exist_ok=True)  # Create the directory if it doesn't exist

# Mount static files directory for serving images, CSS, JS, etc.
app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def home_redirect():
    """Redirect or inform about the QR code generator path"""
    return HTMLResponse(content="""
        <html>
            <head>
                <title>QR Code Generator</title>
                <meta http-equiv="refresh" content="0;url=/QrCodeGenerator" />
            </head>
            <body>
                <p>Redirecting to <a href="/QrCodeGenerator">QR Code Generator</a>...</p>
            </body>
        </html>
    """)

# Add the new endpoint at /QrCodeGenerator
@app.get("/QrCodeGenerator", response_class=HTMLResponse)
def serve_qr_generator():
    """Serve the index.html file at the /QrCodeGenerator path"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Index file not found")
    
    with open(index_path, "r") as file:
        content = file.read()
    return HTMLResponse(content=content)

# Alternative approach using FileResponse
@app.get("/app", response_class=FileResponse)
def serve_index_as_file():
    """Alternative endpoint to serve the index.html file"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Index file not found")
    
    return FileResponse(index_path)

@app.post("/generateQR")
async def generate_qr(request: Request):
    data = await request.json()
    url = data.get("url")
    error_correction_level = data.get("errorCorrectionLevel", "H")  # Default to H if not provided
    
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' in request body.")
    
    # Parse URL to extract brand and qr_code
    # Default values as fallback
    brand = "generic"
    qr_code = "code"
    filename_prefix = "qr_code"  # Default fallback
    
    try:
        # Parse the URL and try to extract brand and QR code
        parsed_url = urlparse(url)
        
        # Pattern 1: https://www.ridgid.com/qr/fxp490
        qr_pattern = re.compile(r"www\.([^.]+)\.com/qr/([^/]+)")
        match = qr_pattern.search(parsed_url.netloc + parsed_url.path)
        
        if match:
            brand = match.group(1).lower()
            qr_code = match.group(2).lower()
            filename_prefix = f"{brand}-qr-{qr_code}"
        else:
            # Alternative pattern matching if needed
            # For example: trying to match other URL formats
            
            # Finally, if no patterns match, use a sanitized version of the hostname as the brand
            hostname = parsed_url.netloc
            if hostname.startswith('www.'):
                hostname = hostname[4:]
            if '.' in hostname:
                brand = hostname.split('.')[0]
            
            # Use part of path as qr_code if available
            path_parts = [p for p in parsed_url.path.split('/') if p]
            if path_parts:
                qr_code = path_parts[-1]
                
            # If we have both brand and qr_code, use the new format
            if brand != "generic" or qr_code != "code":
                filename_prefix = f"{brand}-qr-{qr_code}"
    
    except Exception as e:
        # Log the error but continue with default filename
        print(f"Error parsing URL: {str(e)}")
    
    # Map error correction level to qrcode constants
    error_correction_mapping = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H
    }
    
    # Use the provided error correction level or default to H
    error_correction = error_correction_mapping.get(
        error_correction_level, 
        qrcode.constants.ERROR_CORRECT_H
    )
    
    # Generate the QR Code with the specified error correction level
    qr = qrcode.QRCode(
        error_correction=error_correction,
        box_size=10,
        border=0
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # 1. Generate 2000x2000 px SVG:
    #   - QR code drawn in a 1568x1568 area with 216px padding on all sides
    matrix = qr.get_matrix()  # Get the QR matrix (list of lists of booleans)
    n = len(matrix)
    module_size = 1568 / n  # Each module's size to fill 360px exactly
    svg_elements = []
    # White background for the full 2000x2000 canvas
    svg_elements.append('<rect x="0" y="0" width="2000" height="2000" fill="white" />')
    # Draw each black module as a rectangle
    for i, row in enumerate(matrix):
        for j, cell in enumerate(row):
            if cell:
                # Compute the top-left coordinate of the module, offset by 216px
                x = 216 + j * module_size
                y = 216 + i * module_size
                svg_elements.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{module_size:.2f}" height="{module_size:.2f}" fill="black" />'
                )
    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">'
        + "".join(svg_elements)
        + "</svg>"
    )
    svg_path = os.path.join(QR_CODE_DIR, f"{filename_prefix}.svg")
    with open(svg_path, "w", encoding="utf-8") as svg_file:
        svg_file.write(svg_content)
    
    # 2. Generate 2000x2000 px PNG:
    #   - QR code image generated at 1568x1568 px, centered with 216px padding
    qr_png_img = qr.make_image(fill_color="black", back_color="white")
    qr_png = qr_png_img.resize((1568, 1568), Image.NEAREST)  # Resize to 1568x1568 for quality
    canvas_png = Image.new("RGB", (2000, 2000), "white")
    canvas_png.paste(qr_png, (216, 216))
    png_path = os.path.join(QR_CODE_DIR, f"{filename_prefix}.png")
    canvas_png.save(png_path, "PNG")
    
    # 3. Generate 500x500 px EPS:
    #   - QR code image generated at 360x360 px, centered with 70px padding
    qr_eps_img = qr.make_image(fill_color="black", back_color="white")
    qr_eps = qr_eps_img.resize((360, 360), Image.NEAREST)
    canvas_eps = Image.new("RGB", (500, 500), "white")
    canvas_eps.paste(qr_eps, (70, 70))
    eps_path = os.path.join(QR_CODE_DIR, f"{filename_prefix}.eps")
    canvas_eps.save(eps_path, "EPS")
    
    # Generate full download URLs using the request's base URL
    base_url = str(request.base_url).rstrip("/")
    return {
        "message": "QR Code generated successfully!",
        "files": {
            "svg": f"{base_url}/download/{filename_prefix}.svg",
            "png": f"{base_url}/download/{filename_prefix}.png",
            "eps": f"{base_url}/download/{filename_prefix}.eps"
        }
    }

@app.post("/generateQRFromExcel")
async def generate_qr_from_excel(
    file: UploadFile = File(...),
    errorCorrectionLevel: str = Form("H")
):
    """Generate QR codes from URLs in an Excel file."""
    # Validate file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Check if file has data
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel file is empty")
        
        # Find URL column - case insensitive search for "url"
        url_column = None
        for col in df.columns:
            if 'url' in col.lower():
                url_column = col
                break
        
        if not url_column:
            raise HTTPException(status_code=400, detail="No column containing 'url' found in Excel file")
        
        # Find filename column - case insensitive search for "filename"
        filename_column = None
        for col in df.columns:
            if 'filename' in col.lower() or 'file name' in col.lower() or 'file_name' in col.lower():
                filename_column = col
                break
        
        # Create list of links and filenames
        links_data = []
        for index, row in df.iterrows():
            url = row[url_column]
            # Skip empty URLs
            if pd.isna(url) or not url:
                continue
                
            # Get filename if available
            filename = None
            if filename_column and not pd.isna(row[filename_column]) and row[filename_column]:
                # Clean filename - remove invalid characters
                filename = re.sub(r'[\\/*?:"<>|]', "", str(row[filename_column]))
            
            links_data.append({"url": url, "filename": filename})
        
        if not links_data:
            raise HTTPException(status_code=400, detail="No valid URLs found in Excel file")
        
        # Map error correction level
        error_correction_mapping = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H
        }
        
        # Use provided error correction level or default to H
        error_correction = error_correction_mapping.get(
            errorCorrectionLevel, 
            qrcode.constants.ERROR_CORRECT_H
        )
        
        # Create a temporary directory for SVG files
        temp_dir = tempfile.mkdtemp(prefix="qr_codes_")
        
        # Create a timestamp for unique zip filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"qr_codes_{timestamp}.zip"
        zip_path = os.path.join(QR_CODE_DIR, zip_filename)
        
        # Generate SVG QR codes and add to zip
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for i, link_data in enumerate(links_data):
                url = link_data["url"]
                custom_filename = link_data["filename"]
                
                # Generate QR code
                qr = qrcode.QRCode(
                    error_correction=error_correction,
                    box_size=10,
                    border=0
                )
                qr.add_data(url)
                qr.make(fit=True)
                
                # Determine filename
                if custom_filename:
                    # Use the custom filename from Excel
                    svg_filename = f"{custom_filename}.svg"
                else:
                    # Use the old naming convention
                    try:
                        # Parse URL to extract parts
                        parsed_url = urlparse(url)
                        
                        # Pattern 1: https://www.ridgid.com/qr/fxp490
                        qr_pattern = re.compile(r"www\.([^.]+)\.com/qr/([^/]+)")
                        match = qr_pattern.search(parsed_url.netloc + parsed_url.path)
                        
                        if match:
                            brand = match.group(1).lower()
                            qr_code = match.group(2).lower()
                            svg_filename = f"{brand}-qr-{qr_code}.svg"
                        else:
                            # Alternative extraction
                            hostname = parsed_url.netloc
                            if hostname.startswith('www.'):
                                hostname = hostname[4:]
                            if '.' in hostname:
                                brand = hostname.split('.')[0]
                            else:
                                brand = "generic"
                                
                            # Use part of path as qr_code if available
                            path_parts = [p for p in parsed_url.path.split('/') if p]
                            if path_parts:
                                qr_code = path_parts[-1]
                            else:
                                qr_code = f"code{i+1}"
                                
                            svg_filename = f"{brand}-qr-{qr_code}.svg"
                    except:
                        # Fallback naming
                        svg_filename = f"qr_code_{i+1}.svg"
                
                # Create SVG QR code - Same SVG generation code as in generateQR
                matrix = qr.get_matrix()
                n = len(matrix)
                module_size = 1568 / n
                svg_elements = []
                
                # White background
                svg_elements.append('<rect x="0" y="0" width="2000" height="2000" fill="white" />')
                
                # Draw each black module
                for i, row in enumerate(matrix):
                    for j, cell in enumerate(row):
                        if cell:
                            x = 216 + j * module_size
                            y = 216 + i * module_size
                            svg_elements.append(
                                f'<rect x="{x:.2f}" y="{y:.2f}" width="{module_size:.2f}" height="{module_size:.2f}" fill="black" />'
                            )
                
                svg_content = (
                    f'<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 2000 2000">'
                    + "".join(svg_elements)
                    + "</svg>"
                )
                
                # Write to temp file and add to zip
                temp_svg_path = os.path.join(temp_dir, svg_filename)
                with open(temp_svg_path, "w", encoding="utf-8") as svg_file:
                    svg_file.write(svg_content)
                
                # Add to zip with just the filename (no path)
                zipf.write(temp_svg_path, arcname=svg_filename)
        
        # Clean up temporary directory
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
        
        # Generate download URL
        base_url = "http://localhost:3000"  # Fallback if request base_url not available
        
        return {
            "message": f"Successfully generated {len(links_data)} QR codes",
            "files": {
                "zip": f"{base_url}/download/{zip_filename}"
            }
        }
        
    except Exception as e:
        # Log and return error
        print(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(QR_CODE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
