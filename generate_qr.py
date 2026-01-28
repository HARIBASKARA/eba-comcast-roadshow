"""
QR Code Generator for EBI Comcast Roadshow
Generates QR codes for entrance and all 6 team stations
"""

import qrcode
import os
from PIL import Image, ImageDraw, ImageFont

# Create QR codes directory
QR_DIR = 'qr_codes'
os.makedirs(QR_DIR, exist_ok=True)

# Get the local IP address or use localhost
# You'll need to replace this with your actual server IP address
SERVER_URL = "https://eba-comcast-roadshow.onrender.com"  # Your public Render URL

def generate_qr_code(data, filename, label):
    """Generate a QR code with a label"""
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to RGB
    qr_img = qr_img.convert('RGB')
    
    # Create a new image with space for label
    width, height = qr_img.size
    new_height = height + 100
    labeled_img = Image.new('RGB', (width, new_height), 'white')
    
    # Paste QR code
    labeled_img.paste(qr_img, (0, 0))
    
    # Add label text
    draw = ImageDraw.Draw(labeled_img)
    
    try:
        # Try to use a nice font
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_url = ImageFont.truetype("arial.ttf", 14)
    except:
        # Fallback to default font
        font_title = ImageFont.load_default()
        font_url = ImageFont.load_default()
    
    # Draw label
    text_bbox = draw.textbbox((0, 0), label, font=font_title)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    draw.text((text_x, height + 10), label, fill='black', font=font_title)
    
    # Draw URL
    url_text = data
    url_bbox = draw.textbbox((0, 0), url_text, font=font_url)
    url_width = url_bbox[2] - url_bbox[0]
    url_x = (width - url_width) // 2
    draw.text((url_x, height + 50), url_text, fill='gray', font=font_url)
    
    # Save image
    filepath = os.path.join(QR_DIR, filename)
    labeled_img.save(filepath)
    print(f"✅ Generated: {filepath}")
    return filepath

def main():
    global SERVER_URL
    
    print("🚀 EBI Comcast Roadshow QR Code Generator")
    print("=" * 50)
    
    # Ask user for server URL
    print(f"\nCurrent server URL: {SERVER_URL}")
    custom_url = input("Enter your server URL (or press Enter to use current): ").strip()
    
    if custom_url:
        SERVER_URL = custom_url
    
    print(f"\n📍 Using server URL: {SERVER_URL}")
    print("\nGenerating QR codes...\n")
    
    # Generate entrance QR code
    entrance_url = f"{SERVER_URL}/"
    generate_qr_code(
        entrance_url,
        "entrance_qr.png",
        "🚀 Welcome to EBI Roadshow"
    )
    
    # Generate ONE QR per team (physical station QR)
    project_names = {
        '1': 'Framework',
        '2': 'Solution',
        '3': 'Data Analytics Team',
        '4': 'Machine Learning Team',
        '5': 'Artificial Intelligence Team',
        '6': 'Market Team'
    }
    
    for i in range(1, 7):
        # Create ONE QR per team - contains team URL for access AND team ID for verification
        # Format: URL?verify=ID (e.g., /project/1?verify=1)
        team_url = f"{SERVER_URL}/project/{i}?verify={i}"
        team_name = project_names.get(str(i), f'Team {i}')
        generate_qr_code(
            team_url,
            f"team_{i}_qr.png",
            f"📍 {team_name}"
        )
    
    print("\n" + "=" * 50)
    print("✅ All QR codes generated successfully!")
    print(f"📁 QR codes saved in: {os.path.abspath(QR_DIR)}")
    print("\n📋 Instructions:")
    print("1. Print entrance_qr.png - Place at roadshow entrance")
    print("2. Print team_1_qr.png through team_6_qr.png")
    print("3. Place each team QR at its physical station")
    print("\n💡 Flow for registered user:")
    print("   1. Scan entrance → Register")
    print("   2. Click team button → Team page")
    print("   3. Click 'Scan QR' → Camera opens")
    print("   4. Scan physical team QR → Timer starts")
    print("\n💡 Flow if user scans team QR first (not registered):")
    print("   1. Scan team QR directly")
    print("   2. Redirects to entrance → Register")
    print("   3. Auto-goes to that team page")
    print("   4. Click 'Scan QR' → Camera opens")
    print("   5. Scan same physical QR → Timer starts")
    print("\n🎯 ONE QR per team does everything!")

if __name__ == "__main__":
    main()
