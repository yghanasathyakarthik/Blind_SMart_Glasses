with open(r'D:\Blind_SMart_Glasses\generate_master_doc.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('p_filter = [')
print(text[idx:idx+800])
