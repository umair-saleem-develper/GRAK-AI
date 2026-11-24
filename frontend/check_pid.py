import psutil
try:
    p = psutil.Process(12232)
    print(p.cmdline())
    print(p.cwd())
except Exception as e:
    print(e)
