import qrcode

# --- YOUR CURRENT WI-FI IP ADDRESS ---
my_ip = "10.220.148.137" 
batch_number = "MKCS1267"

# Constructs the URL for your local network
url = f"http://{my_ip}:8501/?batch={batch_number}"

print(f"Generating QR code for: {url}")

# Generate and save the image
img = qrcode.make(url)
img.save("ammonium_qr_local.png")

print("✅ Saved as ammonium_qr_local.png")