-- print(table.unpack(arg))
local glue, srlua
if #arg == 2 then
  glue = io.popen("where glue.exe"):read("*a"):match("([^%s]+)")
  srlua = io.popen("where srlua.exe"):read("*a"):match("([^%s]+)")
elseif #arg == 4 then
  glue = arg[3]
  srlua = arg[4]
else
  print("usage: lfreeze prog.lua prog.exe [ glue.exe srlua.exe ]")
end

if not glue or not srlua then
  print("glue", glue)
  print("srlua", srlua)
  os.exit(false)
end

-- print(glue)
-- print(srlua)
local command = ("%s %s %s %s"):format(glue, srlua, arg[1], arg[2])
-- print(command)
os.execute(command)
