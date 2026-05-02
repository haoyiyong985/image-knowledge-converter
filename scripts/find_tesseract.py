import shutil
import os

# 查找 tesseract 路径
tess_path = shutil.which('tesseract')
print(f"Tesseract path: {tess_path}")

# 检查 pytesseract
print("\nChecking pytesseract...")
try:
    import pytesseract
    print(f"pytesseract version: {pytesseract.get_tesseract_version()}")
except Exception as e:
    print(f"Error: {e}")
