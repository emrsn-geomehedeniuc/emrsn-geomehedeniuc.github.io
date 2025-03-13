from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
import qrcode
from PIL import Image
import os

app = FastAPI()

# Create a directory to store generated QR codes
QR_CODE_DIR = "generated_qr_codes"
os.makedirs(QR_CODE_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"message": "QR Code Generator API is running."}

@app.post("/generateQR")
async def generate_qr(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' in request body.")
    
    # Generate the QR Code with Error Correction Level H
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=0
    )
    qr.add_data(prompt)
    qr.make(fit=True)
    
    filename_prefix = "qr_code"
    
    # 1. Generate 500x500 px SVG:
    #   - QR code drawn in a 360x360 area with 70px padding on all sides
    matrix = qr.get_matrix()  # Get the QR matrix (list of lists of booleans)
    n = len(matrix)
    module_size = 360 / n  # Each module's size to fill 360px exactly
    svg_elements = []
    # White background for the full 500x500 canvas
    svg_elements.append('<rect x="0" y="0" width="500" height="500" fill="white" />')
    # Draw each black module as a rectangle
    for i, row in enumerate(matrix):
        for j, cell in enumerate(row):
            if cell:
                # Compute the top-left coordinate of the module, offset by 70px
                x = 70 + j * module_size
                y = 70 + i * module_size
                svg_elements.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{module_size:.2f}" height="{module_size:.2f}" fill="black" />'
                )
    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 0 500 500">'
        + "".join(svg_elements)
        + "</svg>"
    )
    svg_path = os.path.join(QR_CODE_DIR, f"{filename_prefix}.svg")
    with open(svg_path, "w", encoding="utf-8") as svg_file:
        svg_file.write(svg_content)
    
    # 2. Generate 2000x2000 px PNG:
    #   - QR code image generated at 1440x1440 px, centered with 280px padding
    qr_png_img = qr.make_image(fill_color="black", back_color="white")
    qr_png = qr_png_img.resize((1440, 1440), Image.NEAREST)  # Resize to 1440x1440 for quality
    canvas_png = Image.new("RGB", (2000, 2000), "white")
    canvas_png.paste(qr_png, (280, 280))
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

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(QR_CODE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
