import pandas
import db_lib


def parseSpreadsheet(infilename):
#  file_extension  = infilename[string.rfind(infilename,"."):len(infilename)]
#  file_prefix = infilename[0:string.rfind(infilename,".")]
#  csvfilename = file_prefix + ".csv"

  excel_data = pandas.read_excel(infilename,header=1)

#  for line in excel_data.iterrows():
#    print(line)
  DataFrame = pandas.read_excel(infilename, sheetname=0)
#  print(DataFrame)
  d = DataFrame.to_dict()
  print(d)
  return d

def insertSpreadsheetDict(d,owner):
  currentPucks = []
  for i in range (0,len(d["puckName"])): #number of rows in sheet
#    print(d["container_name"][i])
#    print(d["position"][i])
#    print(d["item_name"][i])
    container_name = str(d["puckName"][i]).replace(" ","")
    position_s = str(d["position"][i]).replace(" ","")
    position = int(position_s)
    propNum = None
    try:
      propNum_s = str(d["proposalNum"][i]).replace(" ","")
      propNum = int(propNum_s)
    except KeyError:
      pass
    except ValueError:
      propNum = None      
    if (propNum == ''):
      propNum = None
    print(propNum)
    item_name1 = str(d["sampleName"][i]).replace(".","_")
    item_name = item_name1.replace(" ","_")    
    modelFilename = str(d["model"][i]).replace(" ","")
    sequenceFilename = str(d["sequence"][i]).replace(" ","")
    containerUID = db_lib.getContainerIDbyName(container_name,owner)
    if (containerUID == ''):
      print("create container " + str(container_name))
      containerUID = db_lib.createContainer(container_name,16,owner,"16_pin_puck")
    sampleUID = db_lib.getSampleIDbyName(item_name,owner) #this line looks like not needed anymore
    if (1):
#    if (sampleUID == ''):      
      print("create sample " + str(item_name))
      sampleUID = db_lib.createSample(item_name,owner,"pin",model=modelFilename,sequence=sequenceFilename,proposalID=propNum)
    else:
      print("WARNING - DUPLICATE SAMPLE NAME " + str(item_name))
    if (containerUID not in currentPucks):
      db_lib.emptyContainer(containerUID)
      currentPucks.append(containerUID)
    print("insertIntoContainer " + str(container_name) + "," + owner + "," + str(position) + "," + sampleUID)
    db_lib.insertIntoContainer(container_name, owner, position, sampleUID)


def importSpreadsheet(infilename,owner):
  d = parseSpreadsheet(infilename)
  insertSpreadsheetDict(d,owner)


  

    