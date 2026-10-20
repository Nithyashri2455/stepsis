import qrcode
import os

url = "http://192.168.1.14:7103"

os.makedirs("qr_code", exist_ok=True)

img = qrcode.make(url)
img.save("qr_code/flask_qrcode.png")

print("QR Code Generated Successfully!")
print("URL:", url)
