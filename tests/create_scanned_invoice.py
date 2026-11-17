
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pymupdf

output_folder = Path("data/sample_invoices")
output_folder.mkdir(parents=True, exist_ok=True)

image_path = output_folder / "scanned_invoice_2.png"
pdf_path = output_folder / "scanned_invoice_2.pdf"

image = Image.new("RGB", (1600, 1100), "white")
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("arial.ttf", 42)
title_font = ImageFont.truetype("arialbd.ttf", 65)

draw.text(
    (120, 90),
    "SUPPLIER INVOICE",
    font=title_font,
    fill="black"
)

invoice_lines = [
    "Supplier: Nairobi Technology Supplies",
    "Invoice Number: OCR-TEST-002",
    "Invoice Date: 17/11/2026",
    "",
    "Description: Computer Equipment",
    "Quantity: 3",
    "Unit Price: KES 12,000.00",
    "",
    "TOTAL: KES 36,000.00",
    "",
    "Thank you for your business."
]

y_position = 250

for line in invoice_lines:
    draw.text(
        (120, y_position),
        line,
        font=font,
        fill="black"
    )
    y_position += 75

image.save(image_path)

document = pymupdf.open()
page = document.new_page(width=800, height=550)

page.insert_image(
    page.rect,
    filename=str(image_path)
)

document.save(pdf_path)
document.close()

print("Second scanned invoice created successfully.")
print("PDF:", pdf_path)
