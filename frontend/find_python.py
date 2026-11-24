import psutil
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if p.info['name'] in ('python.exe', 'python3.exe') or (p.info['cmdline'] and 'python' in p.info['cmdline'][0].lower()):
            print(p.info['pid'], p.info['cmdline'])
    except:
        pass
