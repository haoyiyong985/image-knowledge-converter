import zipfile

with zipfile.ZipFile('dist/image-knowledge-converter_20260317_231629.zip') as z:
    print("ZIP 文件内容:\n")
    for name in sorted(z.namelist()):
        size = z.getinfo(name).file_size
        print(f"[OK] {name} ({size} bytes)")
    
    print(f"\n总计: {len(z.namelist())} 个文件")
