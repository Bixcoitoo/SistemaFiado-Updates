import json
import re

# Lê a versão do version.json
with open('version.json', 'r', encoding='utf-8') as f:
    version_data = json.load(f)
    version = version_data.get('version', '1.0.0')

print(f'[SYNC] Versão detectada: {version}')

# Atualiza installer.iss
iss_path = 'installer.iss'
with open(iss_path, 'r', encoding='utf-8') as f:
    iss_content = f.read()
iss_content_new = re.sub(r'(AppVersion=).*', f'AppVersion={version}', iss_content)
with open(iss_path, 'w', encoding='utf-8') as f:
    f.write(iss_content_new)
print(f'[SYNC] AppVersion do installer.iss atualizado para {version}')

# Atualiza file_version_info.txt
file_info_path = 'file_version_info.txt'
with open(file_info_path, 'r', encoding='utf-8') as f:
    file_info = f.read()
# Atualiza filevers e prodvers
version_tuple = tuple(map(int, version.split('.'))) + (0,) * (4 - len(version.split('.')))
file_info = re.sub(r'filevers=\([^)]+\)', f'filevers={version_tuple}', file_info)
file_info = re.sub(r'prodvers=\([^)]+\)', f'prodvers={version_tuple}', file_info)
# Atualiza FileVersion e ProductVersion
file_info = re.sub(r"StringStruct\(u'FileVersion', u'[^']*'\)", f"StringStruct(u'FileVersion', u'{version}')", file_info)
file_info = re.sub(r"StringStruct\(u'ProductVersion', u'[^']*'\)", f"StringStruct(u'ProductVersion', u'{version}')", file_info)
with open(file_info_path, 'w', encoding='utf-8') as f:
    f.write(file_info)
print(f'[SYNC] file_version_info.txt atualizado para {version}')

# Atualiza o marcador de versão no main.py
main_path = 'main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main_content = f.read()
main_content_new = re.sub(r"# VERSAO_SISTEMA = '.*'", f"# VERSAO_SISTEMA = '{version}'", main_content)
with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_content_new)
print(f'[SYNC] Versão do main.py atualizada para {version}') 