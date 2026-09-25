BS = chr(92)
src = '"' + BS + "ud83d" + BS + "udd11" + '"'
print("python source", src, "-> len", len(eval(src)))
