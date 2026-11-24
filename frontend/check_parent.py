import psutil
try:
    p = psutil.Process(5420)
    pp = psutil.Process(p.ppid())
    print(f"Parent: {pp.pid} - {pp.cmdline()}")
except Exception as e:
    print(e)
