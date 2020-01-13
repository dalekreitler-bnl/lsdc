import Gen_Commands
import Gen_Traj_Square
import beamline_support
import beamline_lib #did this really screw me if I imported b/c of daq_utils import??
from beamline_lib import *
import daq_lib
from daq_lib import *
import daq_utils
import db_lib
import det_lib
import math
import robot_lib
import time
from random import randint
import glob
import xmltodict
from importlib import reload
import start_bs
from start_bs import *
import super_state_machine
import _thread
import parseSheet
import attenCalc
import raddoseLib
from raddoseLib import *
try:
  import ispybLib
except:
  print("ISPYB import error")
  
import sys
from XSDataMXv1 import XSDataResultCharacterisation
global rasterRowResultsList, processedRasterRowCount
global ednaActiveFlag

ednaActiveFlag = 0

global autoRasterFlag
autoRasterFlag = 0

rasterRowResultsList = []

global autoVectorFlag, autoVectorCoarseCoords
autoVectorCoarseCoords = {}
autoVectorFlag=False

#12/19 - general comments. This file takes the brunt of the near daily changes and additions the scientists request. Some duplication and sloppiness reflects that.
# I'm going to leave a lot of the commented lines in, since they might shed light on things or be useful later.

def hi_macro():
  print("hello from macros\n")
  daq_lib.broadcast_output("broadcast hi")


def BS():
  movr(omega,40)

def BS2():
  ascan(omega,0,100,10)

def abortBS():
  if (RE.state != "idle"):
    try:
      RE.abort()
    except super_state_machine.errors.TransitionError:
      print("caught BS")

def changeImageCenterLowMag(x,y,czoom):
  zoom = int(czoom)
  zoomMinXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMinXRBV")
  zoomMinYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMinYRBV")
  minXRBV = beamline_support.getPvValFromDescriptor("lowMagMinXRBV")
  minYRBV = beamline_support.getPvValFromDescriptor("lowMagMinYRBV")
  
  sizeXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomSizeXRBV")
  sizeYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomSizeYRBV")
  sizeXRBV = 640.0
  sizeYRBV = 512.0
  roiSizeXRBV = beamline_support.getPvValFromDescriptor("lowMagROISizeXRBV")
  roiSizeYRBV = beamline_support.getPvValFromDescriptor("lowMagROISizeYRBV")  
  roiSizeZoomXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomROISizeXRBV")
  roiSizeZoomYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomROISizeYRBV")
  inputSizeZoomXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMaxSizeXRBV")
  inputSizeZoomYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMaxSizeYRBV")      
  inputSizeXRBV = beamline_support.getPvValFromDescriptor("lowMagMaxSizeXRBV")
  inputSizeYRBV = beamline_support.getPvValFromDescriptor("lowMagMaxSizeYRBV")      
  x_click = float(x)
  y_click = float(y)
  binningFactor = 2.0  
  if (zoom):
    xclickFullFOV = x_click + zoomMinXRBV
    yclickFullFOV = y_click + zoomMinYRBV
  else:
    binningFactor = 2.0
    xclickFullFOV = (x_click * binningFactor) + minXRBV
    yclickFullFOV = (y_click * binningFactor) + minYRBV    
  new_minXZoom = xclickFullFOV-(sizeXRBV/2.0)
  new_minYZoom = yclickFullFOV-(sizeYRBV/2.0)
  new_minX = new_minXZoom - (sizeXRBV/2.0)
  new_minY = new_minYZoom - (sizeYRBV/2.0)
  noZoomCenterX = sizeXRBV/2.0
  noZoomCenterY = sizeYRBV/2.0  
  if (new_minX < 0):
    new_minX = 0
    noZoomCenterX = (new_minXZoom+(sizeXRBV/2.0))/binningFactor
  if (new_minY < 0):
    new_minY = 0    
    noZoomCenterY = (new_minYZoom+(sizeYRBV/2.0))/binningFactor
  if (new_minX+roiSizeXRBV>inputSizeXRBV):
    new_minX = inputSizeXRBV-roiSizeXRBV    
    noZoomCenterX = ((new_minXZoom+(sizeXRBV/2.0)) - new_minX)/binningFactor
  if (new_minY+roiSizeYRBV>inputSizeYRBV):
    new_minY = inputSizeYRBV-roiSizeYRBV
    noZoomCenterY = ((new_minYZoom+(sizeYRBV/2.0)) - new_minY)/binningFactor    
  if (new_minXZoom+roiSizeZoomXRBV>inputSizeZoomXRBV):
    new_minXZoom = inputSizeZoomXRBV-roiSizeZoomXRBV
  if (new_minXZoom < 0):
    new_minXZoom = 0
  beamline_support.setPvValFromDescriptor("lowMagZoomMinX",new_minXZoom)    
  if (new_minYZoom+roiSizeZoomYRBV>inputSizeZoomYRBV):
    new_minYZoom = inputSizeZoomYRBV-roiSizeZoomYRBV
  if (new_minYZoom < 0):
    new_minYZoom = 0
  beamline_support.setPvValFromDescriptor("lowMagZoomMinY",new_minYZoom)        
  beamline_support.setPvValFromDescriptor("lowMagMinX",new_minX)
  beamline_support.setPvValFromDescriptor("lowMagMinY",new_minY)    
  beamline_support.setPvValFromDescriptor("lowMagCursorX",noZoomCenterX)
  beamline_support.setPvValFromDescriptor("lowMagCursorY",noZoomCenterY)  
      

def changeImageCenterHighMag(x,y,czoom):
  zoom = int(czoom)
  zoomMinXRBV = beamline_support.getPvValFromDescriptor("highMagZoomMinXRBV")
  zoomMinYRBV = beamline_support.getPvValFromDescriptor("highMagZoomMinYRBV")
  minXRBV = beamline_support.getPvValFromDescriptor("highMagMinXRBV")
  minYRBV = beamline_support.getPvValFromDescriptor("highMagMinYRBV")
  
  sizeXRBV = beamline_support.getPvValFromDescriptor("highMagZoomSizeXRBV")
  sizeYRBV = beamline_support.getPvValFromDescriptor("highMagZoomSizeYRBV")
  sizeXRBV = 640.0
  sizeYRBV = 512.0
  roiSizeXRBV = beamline_support.getPvValFromDescriptor("highMagROISizeXRBV")
  roiSizeYRBV = beamline_support.getPvValFromDescriptor("highMagROISizeYRBV")  
  roiSizeZoomXRBV = beamline_support.getPvValFromDescriptor("highMagZoomROISizeXRBV")
  roiSizeZoomYRBV = beamline_support.getPvValFromDescriptor("highMagZoomROISizeYRBV")
  inputSizeZoomXRBV = beamline_support.getPvValFromDescriptor("highMagZoomMaxSizeXRBV")
  inputSizeZoomYRBV = beamline_support.getPvValFromDescriptor("highMagZoomMaxSizeYRBV")      
  inputSizeXRBV = beamline_support.getPvValFromDescriptor("highMagMaxSizeXRBV")
  inputSizeYRBV = beamline_support.getPvValFromDescriptor("highMagMaxSizeYRBV")      
  x_click = float(x)
  y_click = float(y)
  binningFactor = 2.0  
  if (zoom):
    xclickFullFOV = x_click + zoomMinXRBV
    yclickFullFOV = y_click + zoomMinYRBV
  else:
    binningFactor = 2.0
    xclickFullFOV = (x_click * binningFactor) + minXRBV
    yclickFullFOV = (y_click * binningFactor) + minYRBV    
  new_minXZoom = xclickFullFOV-(sizeXRBV/2.0)
  new_minYZoom = yclickFullFOV-(sizeYRBV/2.0)
  new_minX = new_minXZoom - (sizeXRBV/2.0)
  new_minY = new_minYZoom - (sizeYRBV/2.0)
  noZoomCenterX = sizeXRBV/2.0
  noZoomCenterY = sizeYRBV/2.0  
  if (new_minX < 0):
    new_minX = 0
    noZoomCenterX = (new_minXZoom+(sizeXRBV/2.0))/binningFactor
  if (new_minY < 0):
    new_minY = 0    
    noZoomCenterY = (new_minYZoom+(sizeYRBV/2.0))/binningFactor
  if (new_minX+roiSizeXRBV>inputSizeXRBV):
    new_minX = inputSizeXRBV-roiSizeXRBV    
    noZoomCenterX = ((new_minXZoom+(sizeXRBV/2.0)) - new_minX)/binningFactor
  if (new_minY+roiSizeYRBV>inputSizeYRBV):
    new_minY = inputSizeYRBV-roiSizeYRBV
    noZoomCenterY = ((new_minYZoom+(sizeYRBV/2.0)) - new_minY)/binningFactor    

  if (new_minXZoom+roiSizeZoomXRBV>inputSizeZoomXRBV):
    new_minXZoom = inputSizeZoomXRBV-roiSizeZoomXRBV
  if (new_minXZoom < 0):
    new_minXZoom = 0
  if (new_minYZoom+roiSizeZoomYRBV>inputSizeZoomYRBV):
    new_minYZoom = inputSizeZoomYRBV-roiSizeZoomYRBV
  if (new_minYZoom < 0):
    new_minYZoom = 0
  beamline_support.setPvValFromDescriptor("highMagZoomMinX",new_minXZoom)
  beamline_support.setPvValFromDescriptor("highMagZoomMinY",new_minYZoom)
  beamline_support.setPvValFromDescriptor("highMagMinX",new_minX)
  beamline_support.setPvValFromDescriptor("highMagMinY",new_minY)    
  beamline_support.setPvValFromDescriptor("highMagCursorX",noZoomCenterX)
  beamline_support.setPvValFromDescriptor("highMagCursorY",noZoomCenterY)
  

def autoRasterLoop(currentRequest):
  global autoRasterFlag

  
  if not (daq_lib.setGovRobotSA()):
    return 0
  if (daq_utils.beamline == "amx"):  
    if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"queueCollect") == 1):
      delayTime = db_lib.getBeamlineConfigParam(daq_utils.beamline,"autoRasterDelay")
      time.sleep(delayTime)
    
  reqObj = currentRequest["request_obj"]
  if ("centeringOption" in reqObj):
    if (reqObj["centeringOption"] == "AutoLoop"):
      status = loop_center_xrec()
      if (status== 0):
        mvrDescriptor("sampleX",1000)
        status = loop_center_xrec()                
        if (status== 0):
          mvrDescriptor("sampleX",1000)
          status = loop_center_xrec()
      if (1):
#      if (daq_utils.beamline == "fmx"):                        
        time.sleep(2.0)
        status = loop_center_xrec()              
      return status
#  return 1 #short circuit for commissioning
  setTrans(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultTrans"))
  set_field("xrecRasterFlag","100")        
  sampleID = currentRequest["sample"]
  print("auto raster " + str(sampleID))
  status = loop_center_xrec()
  if (status== 0):
    mvrDescriptor("sampleX",1000)
    status = loop_center_xrec()                
    if (status== 0):
      mvrDescriptor("sampleX",1000)
      status = loop_center_xrec()
  if (1):
#  if (daq_utils.beamline == "fmx"):                    
    time.sleep(2.0)
    status = loop_center_xrec()              
#  time.sleep(2.0)
#  status = loop_center_xrec()  
  if (status == -99): #abort, never hit this
    db_lib.updatePriority(currentRequest["uid"],5000)
    return 0    
  if not (status):
    return 0
  time.sleep(2.0) #looks like I really need this sleep, they really improve the appearance 
#  runRasterScan(currentRequest,"LoopShape")
  runRasterScan(currentRequest,"Coarse")  
  time.sleep(1.5)
  loop_center_mask()
  time.sleep(1)
  autoRasterFlag = 1
  runRasterScan(currentRequest,"Fine")
  time.sleep(1)
  runRasterScan(currentRequest,"Line")
#  if (daq_utils.beamline == "fmx"):
  if (1):
    daq_lib.setGovRobotDI()  
  time.sleep(1)
  autoRasterFlag = 0      

  return 1


def autoVector(currentRequest): #12/19 - not tested!
  global autoVectorFlag

  if not (daq_lib.setGovRobotSA()):
    return 0
  reqObj = currentRequest["request_obj"]
  set_field("xrecRasterFlag","100")        
  sampleID = currentRequest["sample"]
  print("auto raster " + str(sampleID))
  status = loop_center_xrec()
  if (status== 0):
    mvrDescriptor("sampleX",1000)
    status = loop_center_xrec()                
    if (status== 0):
      mvrDescriptor("sampleX",1000)
      status = loop_center_xrec()                
  time.sleep(2.0)
  status = loop_center_xrec()
#  time.sleep(2.0)
#  status = loop_center_xrec()  #I think one too many
  if (status == -99): #abort, never hit this
    db_lib.updatePriority(currentRequest["uid"],5000)
    return 0    
  if not (status):
    return 0
  time.sleep(2.0) #looks like I really need this sleep, they really improve the appearance 
  autoVectorFlag = True
  runRasterScan(currentRequest,"autoVector") 
  print("autovec coarse coords 1")
  print(autoVectorCoarseCoords)
  x1Start = autoVectorCoarseCoords["start"]["x"]
  y1Start = autoVectorCoarseCoords["start"]["y"]
  z1Start = autoVectorCoarseCoords["start"]["z"]
  x1End = autoVectorCoarseCoords["end"]["x"]
  y1End = autoVectorCoarseCoords["end"]["y"]
  z1End = autoVectorCoarseCoords["end"]["z"]
#  time.sleep(1.5)
  loop_center_mask()
  time.sleep(1)   
  runRasterScan(currentRequest,"autoVector")
  autoVectorFlag = False  
  print("autovec coarse coords 2")
  print(autoVectorCoarseCoords)
  x2Start = autoVectorCoarseCoords["start"]["x"]
  y2Start = autoVectorCoarseCoords["start"]["y"]
  z2Start = autoVectorCoarseCoords["start"]["z"]
  x2End = autoVectorCoarseCoords["end"]["x"]
  y2End = autoVectorCoarseCoords["end"]["y"]
  z2End = autoVectorCoarseCoords["end"]["z"]

  x_vec_start = min(x1Start,x2Start)
  y_vec_start = (y1Start+y2Start)/2.0
  z_vec_start = (z1Start+z2Start)/2.0  

  x_vec_end = max(x1End,x2End)
  y_vec_end = (y1End+y2End)/2.0
  z_vec_end = (z1End+z2End)/2.0  

  vectorStart = {"x":x_vec_start,"y":y_vec_start,"z":z_vec_start}  
  vectorEnd = {"x":x_vec_end,"y":y_vec_end,"z":z_vec_end}

  x_vec = x_vec_end - x_vec_start
  y_vec = y_vec_end - y_vec_start
  z_vec = z_vec_end - z_vec_start
  trans_total = math.sqrt(x_vec**2 + y_vec**2 + z_vec**2)
#          print trans_total
  framesPerPoint = 1
  vectorParams={"vecStart":vectorStart,"vecEnd":vectorEnd,"x_vec":x_vec,"y_vec":y_vec,"z_vec":z_vec,"trans_total":trans_total,"fpp":framesPerPoint}
  reqObj["vectorParams"] = vectorParams
  reqObj["centeringOption"] = "Interactive" #kind of kludgy so that collectData doesn't go rastering for vector params again
  currentRequest["request_obj"] = reqObj
#  currentRequest["protocol"] = "vector"
  db_lib.updateRequest(currentRequest)
  daq_lib.collectData(currentRequest)
  daq_lib.setGovRobotSA()              
  return 1

def rasterScreen(currentRequest):
  if (daq_utils.beamline == "fmx"):
    gridRaster(currentRequest)
    return
  
  set_field("xrecRasterFlag","100")      
  sampleID = currentRequest["sample"]
  reqObj = currentRequest["request_obj"]
  gridStep = reqObj["gridStep"]
  print("rasterScreen " + str(sampleID))
  time.sleep(20)
  status = loop_center_xrec()
  if (status== 0):
    mvrDescriptor("sampleX",200)
    status = loop_center_xrec()                
  time.sleep(2.0)
  status = loop_center_xrec()              
  if not (status):
    return 0  
  time.sleep(1) #looks like I really need this sleep, they really improve the appearance
  loopSize = getLoopSize()
  if (loopSize != []):
    rasterW = 1.5 * screenXPixels2microns(loopSize[1])
#    rasterH = 1.5 * screenXPixels2microns(loopSize[0])
    rasterH = 2.5 * screenXPixels2microns(loopSize[0])
    if (rasterH > (1.2 * rasterW)): # for c3d error
      rasterW = 630
      rasterH = 510
  else:
    rasterW = 630
    rasterH = 510
#    rasterH = 390    
  rasterReqID = defineRectRaster(currentRequest,rasterW,rasterH,gridStep)     
  snakeRaster(rasterReqID)
  

def multiCol(currentRequest):
  set_field("xrecRasterFlag","100")      
  sampleID = currentRequest["sample"]
  print("multiCol " + str(sampleID))
  status = loop_center_xrec()
  if not (status):
    return 0  
  time.sleep(1) #looks like I really need this sleep, they really improve the appearance
  runRasterScan(currentRequest,"Coarse")
#  runRasterScan(currentRequest,"LoopShape")
#  time.sleep(1) 

def loop_center_xrec_slow():
  global face_on

  daq_lib.abort_flag = 0    

  for i in range(0,360,40):
    if (daq_lib.abort_flag == 1):
      print("caught abort in loop center")
      return 0
    mvaDescriptor("omega",i)
    pic_prefix = "findloop_" + str(i)
    time.sleep(1.5) #for video lag. This sucks
    daq_utils.take_crystal_picture(filename=pic_prefix)
  comm_s = "xrec " + os.environ["CONFIGDIR"] + "/xrec_360_40.txt xrec_result.txt"
  print(comm_s)
  os.system(comm_s)
  xrec_out_file = open("xrec_result.txt","r")
  target_angle = 0.0
  radius = 0
  x_centre = 0
  y_centre = 0
  reliability = 0
  for result_line in xrec_out_file.readlines():
    print(result_line)
    tokens = result_line.split()
    tag = tokens[0]
    val = tokens[1]
    if (tag == "TARGET_ANGLE"):
      target_angle = float(val )
    elif (tag == "RADIUS"):
      radius = float(val )
    elif (tag == "Y_CENTRE"):
      y_centre_xrec = float(val )
    elif (tag == "X_CENTRE"):
      x_centre_xrec = float(val )
    elif (tag == "RELIABILITY"):
      reliability = int(val )
    elif (tag == "FACE"):
      face_on = float(tokens[3])
  xrec_out_file.close()
  xrec_check_file = open("Xrec_check.txt","r")  
  check_result =  int(xrec_check_file.read(1))
  print("result = " + str(check_result))
  xrec_check_file.close()
  if (reliability < 70 or check_result == 0): #bail if xrec couldn't align loop
    return 0
  mvaDescriptor("omega",target_angle)
  x_center = beamline_support.getPvValFromDescriptor("lowMagCursorX")
  y_center = beamline_support.getPvValFromDescriptor("lowMagCursorY")
  print("center on click " + str(x_center) + " " + str(y_center-radius))
  print("center on click " + str((x_center*2) - y_centre_xrec) + " " + str(x_centre_xrec))
  fovx = daq_utils.lowMagFOVx
  fovy = daq_utils.lowMagFOVy
  
  center_on_click(x_center,y_center-radius,fovx,fovy,source="macro")
  center_on_click((x_center*2) - y_centre_xrec,x_centre_xrec,fovx,fovy,source="macro")
  mvaDescriptor("omega",face_on)
  #now try to get the loopshape starting from here
  return 1


def generateRasterCoords4Traj(rasterRequest):

  reqObj = rasterRequest["request_obj"]
  exptimePerCell = reqObj["exposure_time"]  
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  rasterCellMap = {}
  numsteps = float(rasterDef["rowDefs"][0]["numsteps"])
  columns = numsteps
  rows = len(rasterDef["rowDefs"])
  firstRow = rasterDef["rowDefs"][0]
  sx1 = firstRow["start"]["x"] #startX
  sy1 = firstRow["start"]["y"]
  print("start x,y")
  print(sx1)
  print(sy1)

#9/18 - I think these are crap, but will leave them  
  xRelativeMove = sx1
  yzRelativeMove = sy1*sin(omegaRad)
  yyRelativeMove = sy1*cos(omegaRad)
  xMotAbsoluteMove1 = xRelativeMove    
  yMotAbsoluteMove1 = yyRelativeMove
  zMotAbsoluteMove1 = yzRelativeMove


  lastRow= rasterDef["rowDefs"][-1]
  ex1 = lastRow["end"]["x"]   #endX
  ey1 = lastRow["end"]["y"]
  print("end x,y")  
  print(ex1)
  print(ey1)  
  deltax = ex1-sx1
  deltay = ey1-sy1
  xMotAbsoluteMove1 = -(deltax/2.0)
  xMotAbsoluteMove2 = (deltax/2.0)  
  yMotAbsoluteMove1 = -(deltay/2.0)*cos(omegaRad)
  yMotAbsoluteMove2 = (deltay/2.0)*cos(omegaRad)
  zMotAbsoluteMove1 = -(deltay/2.0)*sin(omegaRad)
  zMotAbsoluteMove2 = (deltay/2.0)*sin(omegaRad)

  print(xMotAbsoluteMove1)
  print(yMotAbsoluteMove1)
  print(zMotAbsoluteMove1)
  print(xMotAbsoluteMove2)
  print(yMotAbsoluteMove2)
  print(zMotAbsoluteMove2)
  print(stepsize)  
  genTraj = Gen_Traj_Square.gen_traj_square(xMotAbsoluteMove1, xMotAbsoluteMove2, yMotAbsoluteMove2, yMotAbsoluteMove1, zMotAbsoluteMove2, zMotAbsoluteMove1, columns,rows)
#  gen_traj_square(x_start, x_end, y_start, y_end, z_start, z_end, step)  
  Gen_Commands.gen_commands(genTraj,exptimePerCell)



def generateGridMap(rasterRequest,rasterEncoderMap=None): #12/19 - there's some dials vs dozor stuff in here
  global rasterRowResultsList

  reqObj = rasterRequest["request_obj"]
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  filePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]
  rasterCellMap = {}
  os.system("mkdir -p " + reqObj["directory"])
  for i in range(len(rasterDef["rowDefs"])):
    numsteps = float(rasterDef["rowDefs"][i]["numsteps"])
#next 6 lines to differentiate horizontal vs vertical raster    
    startX = rasterDef["rowDefs"][i]["start"]["x"]
    endX = rasterDef["rowDefs"][i]["end"]["x"]
    startY = rasterDef["rowDefs"][i]["start"]["y"]
    endY = rasterDef["rowDefs"][i]["end"]["y"]
    deltaX = abs(endX-startX)
    deltaY = abs(endY-startY)

    if ((deltaX != 0) and (deltaX>deltaY or not db_lib.getBeamlineConfigParam(daq_utils.beamline,"vertRasterOn"))): #horizontal raster
      if (i%2 == 0): #left to right if even, else right to left - a snake attempt
        startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0) #this is relative to center, so signs are reversed from motor movements.
      else:
        startX = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["x"]-(stepsize/2.0)
      startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
      xRelativeMove = startX
      yzRelativeMove = startY*sin(omegaRad)
      yyRelativeMove = startY*cos(omegaRad)
      xMotAbsoluteMove = rasterStartX+xRelativeMove    
      yMotAbsoluteMove = rasterStartY-yyRelativeMove
      zMotAbsoluteMove = rasterStartZ-yzRelativeMove
      numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
      for j in range(numsteps):
        imIndexStr = str((i*numsteps)+j+1)        
        if (i%2 == 0): #left to right if even, else right to left - a snake attempt
          xMotCellAbsoluteMove = xMotAbsoluteMove+(j*stepsize)
        else:
          xMotCellAbsoluteMove = xMotAbsoluteMove-(j*stepsize)
        if (daq_utils.detector_id == "EIGER-16"):
#          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),j+1)
          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),(i*numsteps)+j+1)
#          dataFileName = imIndexStr #A TERRIBLE KLUDGE TO SWITCH FROM FILENAME DICT KEY TO INDEX FOR DIALS TO DOZOR
        else:
          dataFileName = daq_utils.create_filename(filePrefix+"_Raster_"+str(i),(i*numsteps)+j+1)
#          dataFileName = daq_utils.create_filename(filePrefix+"_Raster_"+str(i),j+1)          
        rasterCellCoords = {"x":xMotCellAbsoluteMove,"y":yMotAbsoluteMove,"z":zMotAbsoluteMove}
        rasterCellMap[dataFileName[:-4]] = rasterCellCoords
#        rasterCellMap[dataFileName] = rasterCellCoords        
    else: #vertical raster
      if (i%2 == 0): #top to bottom if even, else bottom to top - a snake attempt
        startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0) #this is relative to center, so signs are reversed from motor movements.
      else:
        startY = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["y"]-(stepsize/2.0)
      startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0)
      xRelativeMove = startX
      yzRelativeMove = startY*sin(omegaRad)
      yyRelativeMove = startY*cos(omegaRad)
      xMotAbsoluteMove = rasterStartX+xRelativeMove    
      yMotAbsoluteMove = rasterStartY-yyRelativeMove
      zMotAbsoluteMove = rasterStartZ-yzRelativeMove
      numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
      for j in range(numsteps):
        imIndexStr = str((i*numsteps)+j+1)              
        if (i%2 == 0): #top to bottom if even, else bottom to top - a snake attempt
          yMotCellAbsoluteMove = yMotAbsoluteMove-(cos(omegaRad)*(j*stepsize))
          zMotCellAbsoluteMove = zMotAbsoluteMove-(sin(omegaRad)*(j*stepsize))          
        else:
          yMotCellAbsoluteMove = yMotAbsoluteMove+(cos(omegaRad)*(j*stepsize))
          zMotCellAbsoluteMove = zMotAbsoluteMove+(sin(omegaRad)*(j*stepsize))          
        if (daq_utils.detector_id == "EIGER-16"):
          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),(i*numsteps)+j+1)
#          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),j+1)
#          dataFileName = imIndexStr #A TERRIBLE KLUDGE TO SWITCH FROM FILENAME DICT KEY TO INDEX FOR DIALS TO DOZOR
        else:
          dataFileName = daq_utils.create_filename(filePrefix+"_Raster_"+str(i),j+1)
        rasterCellCoords = {"x":xMotAbsoluteMove,"y":yMotCellAbsoluteMove,"z":zMotCellAbsoluteMove}
        rasterCellMap[dataFileName[:-4]] = rasterCellCoords
#        rasterCellMap[dataFileName] = rasterCellCoords        

#commented out all of the processing, as this should have been done by the thread
  if (rasterEncoderMap!= None):
    rasterCellMap = rasterEncoderMap
#  for fname in rasterCellMap.keys():
#    print(fname + " " + str(rasterCellMap[fname]["x"]) + " " + str(rasterCellMap[fname]["y"]) + " " + str(rasterCellMap[fname]["z"]))
  if ("parentReqID" in rasterRequest["request_obj"]):
    parentReqID = rasterRequest["request_obj"]["parentReqID"]
  else:
    parentReqID = -1
  print("RASTER CELL RESULTS")
#  print(rasterCellMap)
  dialsResultLocalList = []
  for i in range (0,len(rasterRowResultsList)):
    for j in range (0,len(rasterRowResultsList[i])):
      try:
        dialsResultLocalList.append(rasterRowResultsList[i][j])
      except KeyError: #this is to deal with single cell row. Instead of getting back a list of one row, I get back just the row from Dials.
        dialsResultLocalList.append(rasterRowResultsList[i])
        break
###############
#  print(dialsResultLocalList)

#  rasterResultObj = {"sample_id": rasterRequest["sample"],"parentReqID":parentReqID,"rasterCellMap":rasterCellMap,"rasterCellResults":{"type":"dozorRasterResult","resultObj":dialsResultLocalList}}
  rasterResultObj = {"sample_id": rasterRequest["sample"],"parentReqID":parentReqID,"rasterCellMap":rasterCellMap,"rasterCellResults":{"type":"dialsRasterResult","resultObj":dialsResultLocalList}}  
  rasterResultID = db_lib.addResultforRequest("rasterResult",rasterRequest["uid"], owner=daq_utils.owner,result_obj=rasterResultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline)
  rasterResult = db_lib.getResult(rasterResultID)
  return rasterResult


def rasterWait():
  time.sleep(0.2)
  while (beamline_support.getPvValFromDescriptor("RasterActive")):
    time.sleep(0.2)

def vectorWait():
  time.sleep(0.15)
  while (beamline_support.getPvValFromDescriptor("VectorActive")):
    time.sleep(0.05)

def vectorActiveWait():
  time.sleep(0.15)
  while (beamline_support.getPvValFromDescriptor("VectorActive")!=1):
    time.sleep(0.05)
  if (0):
#  if (daq_utils.beamline == "fmx"):                    
    if (beamline_support.getPvValFromDescriptor("zebraTriggering") == 0.0):
      time.sleep(5.0)      
      print("check trigger 1")
      if (beamline_support.getPvValFromDescriptor("zebraTriggering") == 0.0):
        print("check trigger 2")        
        if (beamline_support.getPvValFromDescriptor("zebraTriggering") == 0.0):
          print("check trigger 3")          
          beamline_support.setPvValFromDescriptor("photonShutterClose",1)
          daq_lib.gui_message("Timeout in Trigger Wait! Call Staff!!")
          sys.exit()
          

def vectorHoldWait():
  time.sleep(0.15)
  while (beamline_support.getPvValFromDescriptor("VectorState")!=2):
    time.sleep(0.05)

def vectorProceed():
  beamline_support.setPvValFromDescriptor("vectorProceed",1)

def vectorSync():
  beamline_support.setPvValFromDescriptor("vectorSync",1)

def runDozorThread(directory,prefix,rowIndex,rowCellCount,seqNum):  #12/19 - we haven't tried dozor in about one year
  global rasterRowResultsList,processedRasterRowCount
  time.sleep(1.0)
#  dialsComm = db_lib.getBeamlineConfigParam(daq_utils.beamline,"dialsComm")
  dozorComm = os.environ["CONFIGDIR"] + "software/bin/spot_test_row"
  if (rowIndex%2 == 0):
    node = "cpu-003"
  else:
    node = "cpu-003"    
#  if (rowIndex%4 == 0):
#    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode1")
#  elif (rowIndex%4 == 1):
#    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode2")
#  elif (rowIndex%4 == 2):
#    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode3")
#  else:
#    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode4")  
  hdfSampleDataPattern = directory+"/"+prefix+"_" 
  hdfRowFilepattern = hdfSampleDataPattern + str(int(float(seqNum))) + "_master.h5"
  startIndex=(rowIndex*rowCellCount) + 1
  endIndex = startIndex+rowCellCount-1
  comm_s = "ssh -q " + node + " \"source /home/skinner/.bashrc;" + dozorComm + " " + hdfRowFilepattern  + " " + str(startIndex) + " " + str(endIndex) + " "  + str(rowCellCount) + "\""  #works for rectangles only
  print(comm_s)
  localDozorResultDict={}
  localDozorResultDict["data"]={}
  localDozorResultDict["data"]["response"]=[]  
  lines = os.popen(comm_s).readlines()
  found = 0
  for line in lines:
    line.strip()
    tokens = line.split()
    if (found == 0):
      if (tokens[0] == 'sort_key'):
        found = 1
      else:
        continue
    else:
      if (len(tokens) == 5):
        index = float(tokens[0])
        column = int(tokens[1])
        row = int(tokens[2])
        mainScore = float(tokens[3])
        spotScore = float(tokens[4])
#        index = ((row-1)*rowCellCount) + column
        print(tokens)
        localDozorResultDict["data"]["response"].append({'masterIndex': index,'mainScore': mainScore,'spotScore': spotScore,'spot_count_no_ice':spotScore,'image':hdfRowFilepattern,'d_min': index,'total_intensity':mainScore}) ###kludge to give GUI what it wants! see the dials keys in the dict
  processedRasterRowCount+=1
  rasterRowResultsList[rowIndex] = localDozorResultDict["data"]["response"]
#  return localDozorResultDict
  return

  

def runDialsThread(directory,prefix,rowIndex,rowCellCount,seqNum):
  global rasterRowResultsList,processedRasterRowCount
  time.sleep(1.0)
  cbfComm = db_lib.getBeamlineConfigParam(daq_utils.beamline,"cbfComm")
  dialsComm = db_lib.getBeamlineConfigParam(daq_utils.beamline,"dialsComm")
  dialsTuneLowRes = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneLowRes")
  dialsTuneHighRes = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneHighRes")
  dialsTuneIceRingFlag = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneIceRingFlag")
  dialsTuneResoFlag = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneResoFlag")
  dialsTuneThreshFlag = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterThreshFlag")    
  dialsTuneIceRingWidth = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneIceRingWidth")
  dialsTuneMinSpotSize = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultMinSpotSize")
  dialsTuneThreshKern =  db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterThreshKernSize")
  dialsTuneThreshSigBck =  db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterThreshSigBckrnd")
  dialsTuneThreshSigStrong =  db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterThreshSigStrong")    
  if (dialsTuneIceRingFlag):
    iceRingParams = " ice_rings.filter=true ice_rings.width=" + str(dialsTuneIceRingWidth)
  else:
    iceRingParams = ""
  if (dialsTuneThreshFlag):
    threshParams = " spotfinder.threshold.xds.kernel_size=" + str(dialsTuneThreshKern) + "," + str(dialsTuneThreshKern) + " spotfinder.threshold.xds.sigma_background=" + str(dialsTuneThreshSigBck) + " spotfinder.threshold.xds.sigma_strong=" + str(dialsTuneThreshSigStrong)
  else:
    threshParams = ""
  if (dialsTuneResoFlag):
    resoParams = " spotfinder.filter.d_min=" + str(dialsTuneHighRes) + " spotfinder.filter.d_max=" + str(dialsTuneLowRes)
  else:
    resoParams = ""
  if (daq_utils.beamline == "amx"):
    dialsCommWithParams = dialsComm + resoParams + threshParams + iceRingParams + " min_spot_size=" + str(dialsTuneMinSpotSize)
#    dialsCommWithParams = dialsComm + resoParams + iceRingParams + " min_spot_size=3"    
  else:
    dialsCommWithParams = dialsComm + resoParams + threshParams + iceRingParams
  print(dialsCommWithParams)
  if (rowIndex%8 == 0):
    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode1")
  elif (rowIndex%8 == 1):
    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode2")
  elif (rowIndex%8 == 2):
    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode3")
  elif (rowIndex%8 == 3):
    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode4")
  elif (rowIndex%8 == 4):
    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode5")
  elif (rowIndex%8 == 5):
    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode6")
  elif (rowIndex%8 == 6):
    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode7")
  else:
    node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode8")  
  if (seqNum>-1): #eiger
    cbfDir = directory+"/cbf"
    comm_s = "mkdir -p " + cbfDir
    os.system(comm_s)
    hdfSampleDataPattern = directory+"/"+prefix+"_" 
    hdfRowFilepattern = hdfSampleDataPattern + str(int(float(seqNum))) + "_master.h5"
#    hdfRowFilepattern = hdfSampleDataPattern + str(rowIndex) + "_" + str(int(float(seqNum))) + "_master.h5"    
    CBF_conversion_pattern = cbfDir + "/" + prefix+"_" + str(rowIndex)+"_"  
    comm_s = "eiger2cbf-linux " + hdfRowFilepattern
    startIndex=(rowIndex*rowCellCount) + 1
    endIndex = startIndex+rowCellCount-1
    if (0):
#    if (rowCellCount==1): #account for bug in converter      
#      comm_s = "ssh -q " + node + " \"/usr/local/MX-Soft/bin/eiger2cbfJohn " + hdfRowFilepattern  + " 1 " + CBF_conversion_pattern + "000001.cbf\""
      comm_s = "ssh -q " + node + " \"" + cbfComm + " "  + hdfRowFilepattern  + " 1 " + CBF_conversion_pattern + "000001.cbf\""          
    else:
#      comm_s = "ssh -q " + node + " \"" + cbfComm + " " + hdfRowFilepattern  + " 1:" + str(rowCellCount) + " " + CBF_conversion_pattern + "\""
      comm_s = "ssh -q " + node + " \"" + cbfComm + " " + hdfRowFilepattern  + " " + str(startIndex) + ":" + str(endIndex) + " " + CBF_conversion_pattern + "\""  #works for rectangles only
    print(comm_s)
    os.system(comm_s)
    CBFpattern = CBF_conversion_pattern + "*.cbf"
  else:
    CBFpattern = directory + "/cbf/" + prefix+"_" + str(rowIndex) + "_" + "*.cbf"
  time.sleep(1.0)
  comm_s = "ssh -q " + node + " \"ls -rt " + CBFpattern + ">>/dev/null\""
  lsOut = os.system(comm_s)
#  comm_s = "ssh -q " + node + " \"ls -rt " + CBFpattern + "|" + dialsComm + "\""
  comm_s = "ssh -q " + node + " \"ls " + CBFpattern + "|" + dialsCommWithParams + "\""  
#  comm_s = "ssh -q " + node + " \"ls -rt " + CBFpattern + "|/usr/local/MX-Soft/Phenix/phenix-installer-dev-2666-intel-linux-2.6-x86_64-centos6/build/bin/dials.find_spots_client\""  
##4/11  comm_s = "ssh -q " + node + " \"ls -rt " + CBFpattern + "|/usr/local/crys-local/dials-v1-2-0/build/bin/dials.find_spots_client\""  
  print(comm_s)
  retry = 3
  while(1):
    resultString = "<data>\n"+os.popen(comm_s).read()+"</data>\n"
#    print(resultString)
    localDialsResultDict = xmltodict.parse(resultString)
    if (localDialsResultDict["data"] == None and retry>0):
      print("ERROR \n" + resultString + " retry = " + str(retry))
      retry = retry - 1
      if (retry==0):
        localDialsResultDict["data"]={}
        localDialsResultDict["data"]["response"]=[]
        for jj in range (0,rowCellCount):
          localDialsResultDict["data"]["response"].append({'d_min': '-1.00','d_min_method_1': '-1.00','d_min_method_2': '-1.00','image': '','spot_count': '0','spot_count_no_ice': '0','total_intensity': '0'})
        break
                                      
    else:
      break
  rasterRowResultsList[rowIndex] = localDialsResultDict["data"]["response"]
#  print("\n")
#  print(rasterRowResultsList[rowIndex])
#  print("\n")
  processedRasterRowCount+=1
  print("leaving thread")

def generateGridMapFine(rasterRequest,rasterEncoderMap=None,rowsOfSubrasters=0,columnsOfSubrasters=0,rowsPerSubraster=0,cellsPerSubrasterRow=0):
  global rasterRowResultsList

  reqObj = rasterRequest["request_obj"]
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  filePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]
  rasterCellMap = {}
  os.system("mkdir -p " + reqObj["directory"])
  for i in range(len(rasterDef["rowDefs"])):
    numsteps = float(rasterDef["rowDefs"][i]["numsteps"])
#next 6 lines to differentiate horizontal vs vertical raster    
    startX = rasterDef["rowDefs"][i]["start"]["x"]
    endX = rasterDef["rowDefs"][i]["end"]["x"]
    startY = rasterDef["rowDefs"][i]["start"]["y"]
    endY = rasterDef["rowDefs"][i]["end"]["y"]
    deltaX = abs(endX-startX)
    deltaY = abs(endY-startY)

    if (deltaX>deltaY): #horizontal raster
      if (i%2 == 0): #left to right if even, else right to left - a snake attempt
        startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0) #this is relative to center, so signs are reversed from motor movements.
      else:
        startX = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["x"]-(stepsize/2.0)
      startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
      xRelativeMove = startX
      yzRelativeMove = startY*sin(omegaRad)
      yyRelativeMove = startY*cos(omegaRad)
      xMotAbsoluteMove = rasterStartX+xRelativeMove    
      yMotAbsoluteMove = rasterStartY-yyRelativeMove
      zMotAbsoluteMove = rasterStartZ-yzRelativeMove
      numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
      for j in range(numsteps):
        imIndexStr = str((i*numsteps)+j+1)        
        if (i%2 == 0): #left to right if even, else right to left - a snake attempt
          xMotCellAbsoluteMove = xMotAbsoluteMove+(j*stepsize)
        else:
          xMotCellAbsoluteMove = xMotAbsoluteMove-(j*stepsize)
        if (daq_utils.detector_id == "EIGER-16"):
#          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),j+1)
          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),(i*numsteps)+j+1)
#          dataFileName = imIndexStr #A TERRIBLE KLUDGE TO SWITCH FROM FILENAME DICT KEY TO INDEX FOR DIALS TO DOZOR
        else:
          dataFileName = daq_utils.create_filename(filePrefix+"_Raster_"+str(i),(i*numsteps)+j+1)
#          dataFileName = daq_utils.create_filename(filePrefix+"_Raster_"+str(i),j+1)          
        rasterCellCoords = {"x":xMotCellAbsoluteMove,"y":yMotAbsoluteMove,"z":zMotAbsoluteMove}
        rasterCellMap[dataFileName[:-4]] = rasterCellCoords
#        rasterCellMap[dataFileName] = rasterCellCoords        
    else: #vertical raster
      if (i%2 == 0): #top to bottom if even, else bottom to top - a snake attempt
        startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0) #this is relative to center, so signs are reversed from motor movements.
      else:
        startY = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["y"]-(stepsize/2.0)
      startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0)
      xRelativeMove = startX
      yzRelativeMove = startY*sin(omegaRad)
      yyRelativeMove = startY*cos(omegaRad)
      xMotAbsoluteMove = rasterStartX+xRelativeMove    
      yMotAbsoluteMove = rasterStartY-yyRelativeMove
      zMotAbsoluteMove = rasterStartZ-yzRelativeMove
      numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
      for j in range(numsteps):
        imIndexStr = str((i*numsteps)+j+1)              
        if (i%2 == 0): #top to bottom if even, else bottom to top - a snake attempt
          yMotCellAbsoluteMove = yMotAbsoluteMove-(cos(omegaRad)*(j*stepsize))
          zMotCellAbsoluteMove = zMotAbsoluteMove-(sin(omegaRad)*(j*stepsize))          
        else:
          yMotCellAbsoluteMove = yMotAbsoluteMove+(cos(omegaRad)*(j*stepsize))
          zMotCellAbsoluteMove = zMotAbsoluteMove+(sin(omegaRad)*(j*stepsize))          
        if (daq_utils.detector_id == "EIGER-16"):
          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),(i*numsteps)+j+1)
#          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),j+1)
#          dataFileName = imIndexStr #A TERRIBLE KLUDGE TO SWITCH FROM FILENAME DICT KEY TO INDEX FOR DIALS TO DOZOR
        else:
          dataFileName = daq_utils.create_filename(filePrefix+"_Raster_"+str(i),j+1)
        rasterCellCoords = {"x":xMotAbsoluteMove,"y":yMotCellAbsoluteMove,"z":zMotCellAbsoluteMove}
        rasterCellMap[dataFileName[:-4]] = rasterCellCoords
#        rasterCellMap[dataFileName] = rasterCellCoords        

#commented out all of the processing, as this should have been done by the thread
  if (rasterEncoderMap!= None):
    rasterCellMap = rasterEncoderMap
#  for fname in rasterCellMap.keys():
#    print(fname + " " + str(rasterCellMap[fname]["x"]) + " " + str(rasterCellMap[fname]["y"]) + " " + str(rasterCellMap[fname]["z"]))
  if ("parentReqID" in rasterRequest["request_obj"]):
    parentReqID = rasterRequest["request_obj"]["parentReqID"]
  else:
    parentReqID = -1
  print("RASTER CELL RESULTS")
#  print(rasterCellMap)
  if (rowsOfSubrasters != 0):
    cellsPerSubraster = rowsPerSubraster*cellsPerSubrasterRow
    subrastersPerCompositeRaster = rowsOfSubrasters*columnsOfSubrasters
    rowsPerCompositeRaster = rowsPerSubraster*rowsOfSubrasters
    cellsPerCompositeRasterRow = columnsOfSubrasters*cellsPerSubrasterRow
    cellsPerCompositeRaster = cellsPerSubraster*subrastersPerCompositeRaster
    subRasterListFlipped = []
    for ii in range (0,len(rasterRowResultsList)):
      subrasterFlipped = []  
      for i in range (0,rowsPerSubraster):
        for j in range (0,cellsPerSubrasterRow):
          origSubrasterIndex = (i*cellsPerSubrasterRow)+j                
          if (i%2 == 1): #odd,flip
            subrasterIndex = (i*cellsPerSubrasterRow)+(cellsPerSubrasterRow-j-1)
          else:
            subrasterIndex = origSubrasterIndex
          subrasterFlipped.append(rasterRowResultsList[ii][subrasterIndex])
#  print(subrasterFlipped)
      subRasterListFlipped.append(subrasterFlipped)
#print(subRasterListFlipped)
#flattenedList = []
    dialsResultLocalList = []
    for ii in range (0,rowsOfSubrasters):
      for jj in range (0,rowsPerSubraster):          
        for i in range (0,columnsOfSubrasters):
          for j in range (0,cellsPerSubrasterRow):
            dialsResultLocalList.append(subRasterListFlipped[(ii*columnsOfSubrasters)+i][(jj*cellsPerSubrasterRow)+j]) #first dimension is easy, 
#    print(flattenedList)
  else:
    dialsResultLocalList = []    
    for i in range (0,len(rasterRowResultsList)):
      for j in range (0,len(rasterRowResultsList[i])):
        try:
          dialsResultLocalList.append(rasterRowResultsList[i][j])
        except KeyError: #this is to deal with single cell row. Instead of getting back a list of one row, I get back just the row from Dials.
          dialsResultLocalList.append(rasterRowResultsList[i])
          break
###############
#  print(dialsResultLocalList)

  rasterResultObj = {"sample_id": rasterRequest["sample"],"parentReqID":parentReqID,"rasterCellMap":rasterCellMap,"rasterCellResults":{"type":"dozorRasterResult","resultObj":dialsResultLocalList}}
#  rasterResultObj = {"sample_id": rasterRequest["sample"],"parentReqID":parentReqID,"rasterCellMap":rasterCellMap,"rasterCellResults":{"type":"dialsRasterResult","resultObj":dialsResultLocalList}}  
  rasterResultID = db_lib.addResultforRequest("rasterResult",rasterRequest["uid"], owner=daq_utils.owner,result_obj=rasterResultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline)
  rasterResult = db_lib.getResult(rasterResultID)
  return rasterResult


def snakeRaster(rasterReqID,grain=""):
  scannerType = db_lib.getBeamlineConfigParam(daq_utils.beamline,"scannerType")
  if (scannerType == "PI"):
    snakeRasterFine(rasterReqID,grain)
  else:
    snakeRasterNormal(rasterReqID,grain)

def snakeRasterNoTile(rasterReqID,grain=""):
  global dialsResultDict,rasterRowResultsList,processedRasterRowCount

  if not (daq_lib.setGovRobotDA()):
    return
  
  rasterRequest = db_lib.getRequestByID(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  parentReqID = reqObj["parentReqID"]
  parentReqProtocol = ""
  
  if (parentReqID != -1):
    parentRequest = db_lib.getRequestByID(parentReqID)
    parentReqObj = parentRequest["request_obj"]
    parentReqProtocol = parentReqObj["protocol"]
    detDist = parentReqObj["detDist"]    
  data_directory_name = str(reqObj["directory"])
  os.system("mkdir -p " + data_directory_name)
  os.system("chmod -R 777 " + data_directory_name)  
  filePrefix = str(reqObj["file_prefix"])
  file_number_start = reqObj["file_number_start"]  
  dataFilePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]  
  exptimePerCell = reqObj["exposure_time"]
  img_width_per_cell = reqObj["img_width"]
  wave = reqObj["wavelength"]
  xbeam = beamline_support.getPvValFromDescriptor("beamCenterX")
  ybeam = beamline_support.getPvValFromDescriptor("beamCenterY")
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"]) #these are real sample motor positions
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  rowCount = len(rasterDef["rowDefs"])
  rasterRowResultsList = [{} for i in range(0,rowCount)]    
  processedRasterRowCount = 0
  rasterEncoderMap = {}
  totalImages = 0
#get the center of the raster, in screen view, mm, relative to center
  rows = rasterDef["rowDefs"]
  numrows = len(rows)
  rasterCenterScreenX = (rows[0]["start"]["x"]+rows[0]["end"]["x"])/2.0
  rasterCenterScreenY = ((rows[-1]["start"]["y"]+rows[0]["start"]["y"])/2.0)+(stepsize/2.0)
  xRelativeMove = rasterCenterScreenX
  yzRelativeMove = -(rasterCenterScreenY*sin(omegaRad))
  yyRelativeMove = -(rasterCenterScreenY*cos(omegaRad))

  xMotAbsoluteMove = rasterStartX+xRelativeMove #note we convert relative to absolute moves, using the raster center that was saved in x,y,z
  yMotAbsoluteMove = rasterStartY+yyRelativeMove
  zMotAbsoluteMove = rasterStartZ+yzRelativeMove
  
#  mvrDescriptor("sampleX",xRelativeMove,"sampleY",yyRelativeMove,"sampleZ",yzRelativeMove)

  mvaDescriptor("sampleX",xMotAbsoluteMove,"sampleY",yMotAbsoluteMove,"sampleZ",zMotAbsoluteMove)
  
  #raster centered, now zero motors
  mvaDescriptor("fineX",0,"fineY",0,"fineZ",0)  
#  return
  for i in range(len(rasterDef["rowDefs"])):
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    totalImages = totalImages+numsteps
  rasterFilePrefix = dataFilePrefix + "_Raster"

#  total_exposure_time = exptimePerCell*totalImages  
  det_lib.detector_set_num_triggers(totalImages)
  det_lib.detector_set_trigger_mode(3)
  det_lib.detector_setImagesPerFile(numsteps)  
  detectorArm(omega,img_width_per_cell,totalImages,exptimePerCell,rasterFilePrefix,data_directory_name,file_number_start) #this waits

  zebraVecDaqSetup(omega,img_width_per_cell,exptimePerCell,totalImages,rasterFilePrefix,data_directory_name,file_number_start)
  procFlag = int(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterProcessFlag"))  
  generateRasterCoords4Traj(rasterRequest)
  total_exposure_time = exptimePerCell*totalImages    
    
  beamline_support.setPvValFromDescriptor("zebraPulseMax",totalImages) 
  vectorSync()    
  beamline_support.setPvValFromDescriptor("vectorStartOmega",omega)
  beamline_support.setPvValFromDescriptor("vectorEndOmega",(img_width_per_cell*totalImages)+omega)
#    mvaDescriptor("sampleX",xMotAbsoluteMove,"sampleY",yMotAbsoluteMove,"sampleZ",zMotAbsoluteMove)
  beamline_support.setPvValFromDescriptor("vectorframeExptime",exptimePerCell*1000.0)
  beamline_support.setPvValFromDescriptor("vectorNumFrames",totalImages)
  rasterFilePrefix = dataFilePrefix + "_Raster_" + str(i)
#  scanWidth = float(totalImages)*img_width_per_cell
  Gen_Commands.go_all()
  beamline_support.setPvValFromDescriptor("vectorGo",1)
  vectorActiveWait()    
  vectorWait()
  zebraWait()
##  zebraWaitDownload(totalImages)
  #delete these
  time.sleep(2.0)
  det_lib.detector_stop_acquire()
  det_lib.detector_wait()
  mvaDescriptor("fineX",0,"fineY",0,"fineZ",0)
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)      
  
#  return #SHORT-CIRCUIT
#    if (0):
  if (procFlag):
    if (daq_utils.beamline == "amx"):
      rasterRowEncoderVals = {"x":beamline_support.getPvValFromDescriptor("zebraEncX"),"y":beamline_support.getPvValFromDescriptor("zebraEncY"),"z":beamline_support.getPvValFromDescriptor("zebraEncZ"),"omega":beamline_support.getPvValFromDescriptor("zebraEncOmega")}
      for j in range (0,numsteps):
        dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),(i*numsteps)+j+1)
        imIndexStr = str((i*numsteps)+j+1)
        rasterEncoderMap[dataFileName[:-4]] = {"x":rasterRowEncoderVals["x"][j],"y":rasterRowEncoderVals["y"][j],"z":rasterRowEncoderVals["z"][j],"omega":rasterRowEncoderVals["omega"][j]}
    seqNum = int(det_lib.detector_get_seqnum())
    for i in range(len(rasterDef["rowDefs"])):  
      _thread.start_new_thread(runDialsThread,(data_directory_name,filePrefix+"_Raster",i,numsteps,seqNum))
  else:
    rasterRequestID = rasterRequest["uid"]
    db_lib.updateRequest(rasterRequest)    
    db_lib.updatePriority(rasterRequestID,-1)  
#  set_field("xrecRasterFlag",rasterRequest["uid"])
    if (lastOnSample()):  
      daq_lib.setGovRobotSA()      
    return 1
      
  rasterTimeout = 600
  timerCount = 0
  while (1):
    timerCount +=1
    if (timerCount>rasterTimeout):
      break
    time.sleep(1)
    print(processedRasterRowCount)
    if (processedRasterRowCount == rowCount):
      break
#  if (0):
  if (daq_utils.beamline == "amx"):                
    rasterResult = generateGridMap(rasterRequest,rasterEncoderMap) #I think rasterRequest is entire request, of raster type    
  else:
    rasterResult = generateGridMap(rasterRequest)     
  rasterRequest["request_obj"]["rasterDef"]["status"] = 2
  protocol = reqObj["protocol"]
  print("protocol = " + protocol)
  if (protocol == "multiCol" or parentReqProtocol == "multiColQ"):
    if (parentReqProtocol == "multiColQ"):    
      multiColThreshold  = parentReqObj["diffCutoff"]
    else:
      multiColThreshold  = reqObj["diffCutoff"]         
    gotoMaxRaster(rasterResult,multiColThreshold=multiColThreshold) 
  else:
#    if (deltaX>deltaY): #horizontal raster, dont bother vert for now, did not do pos calcs, wait for zebra
    if (0):
      gotoMaxRaster(rasterResult)
#  print(rasterRequest)
  rasterRequestID = rasterRequest["uid"]
  db_lib.updateRequest(rasterRequest)
#  print("after update")
#  print(rasterRequest)
  
  db_lib.updatePriority(rasterRequestID,-1)  
  set_field("xrecRasterFlag",rasterRequest["uid"])
  if (lastOnSample()):    
    daq_lib.setGovRobotSA()      
  return 1

    

def snakeRasterFine(rasterReqID,grain=""): #12/19 - This is for the PI scanner. It was challenging to write. It was working the last time the scanner was on. 
  global dialsResultDict,rasterRowResultsList,processedRasterRowCount

  if not (daq_lib.setGovRobotDA()):
    return
  
  rasterRequest = db_lib.getRequestByID(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])  
  data_directory_name = str(reqObj["directory"])
  filePrefix = str(reqObj["file_prefix"])
  file_number_start = reqObj["file_number_start"]  
  dataFilePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]  
  wave = reqObj["wavelength"]
  xbeam = beamline_support.getPvValFromDescriptor("beamCenterX")
  ybeam = beamline_support.getPvValFromDescriptor("beamCenterY")
  processedRasterRowCount = 0
  totalImages = 0
#get the center of the raster, in screen view, mm, relative to center
  rows = rasterDef["rowDefs"]
  numrows = len(rows)
  origRasterCenterScreenX = (rows[0]["start"]["x"]+rows[0]["end"]["x"])/2.0
  origRasterCenterScreenY = ((rows[-1]["start"]["y"]+rows[0]["start"]["y"])/2.0)+(stepsize/2.0)
  mvaDescriptor("fineX",0,"fineY",0,"fineZ",0)  
  exptimePerCell = reqObj["exposure_time"]
  img_width_per_cell = reqObj["img_width"]  
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  firstRow = rasterDef["rowDefs"][0]
  lastRow= rasterDef["rowDefs"][-1]
  sx1 = firstRow["start"]["x"] #startX
  sy1 = firstRow["start"]["y"]
  ex1 = lastRow["end"]["x"]   #endX
  ey1 = lastRow["end"]["y"]
  rasterLenX = ex1-sx1
  rasterLenY = ey1-sy1
  omegaLimit = 40.0
  xLimit = 180.0
  yLimit = 120.0
  if (rasterLenX<xLimit and rasterLenY<yLimit): #no need for tiling. Just do what was done before so we can have a heatmap
    snakeRasterNoTile(rasterReqID)
    return
  maxFramesOmega = int(omegaLimit/img_width_per_cell)
  maxFramesX = int(xLimit/stepsize)
  maxFramesY = int(yLimit/stepsize)  
  columnsOfSubrasters = int(math.ceil(rasterLenX/xLimit))
  subrasterLenX = rasterLenX/columnsOfSubrasters
  subrasterColumns = int(subrasterLenX/stepsize)
  
  maxRowsPerSubraster1 = int(maxFramesOmega/subrasterColumns) # we want this one to come up short, no ceil, worry about omega
  maxRowsPerSubraster2 = maxFramesY #worry about Y,Z travel
  maxRowsPerSubraster = min(maxRowsPerSubraster1,maxRowsPerSubraster2)
  
#  rowsPerSubraster = int(maxFramesOmega/maxFramesX) # we want this one to come up short, no ceil

  totalRowsY = int(rasterLenY/stepsize)
  rowsOfSubrasters = int(math.ceil(float(totalRowsY)/float(maxRowsPerSubraster)))
  rowsPerSubraster = int(totalRowsY/rowsOfSubrasters)  
  subrasterLenY = rowsPerSubraster*stepsize
  newRasterLenX = columnsOfSubrasters*subrasterLenX
  newRasterLenY = subrasterLenY*rowsOfSubrasters
  numsteps_h = columnsOfSubrasters*subrasterColumns
  numsteps_v = rowsPerSubraster*rowsOfSubrasters
  newRasterDef = defineTiledRaster(rasterDef,numsteps_h,numsteps_v,origRasterCenterScreenX,origRasterCenterScreenY)
  reqObj["rasterDef"] = newRasterDef
  rasterDef = reqObj["rasterDef"]
  rasterRequest["request_obj"]  = reqObj


  set_field("xrecRasterFlag","100")
  db_lib.updateRequest(rasterRequest) #define new dimensions  
  time.sleep(1.0)
  set_field("xrecRasterFlag",rasterRequest["uid"]) #draw the raster

  
  deltax = subrasterLenX
  deltay = subrasterLenY
  print("omega start " + str(omega))
  print("orig raster Len X = " + str(rasterLenX))
  print("orig raster Len Y = " + str(rasterLenY))  

  xMotAbsoluteMove1 = -(deltax/2.0)
  xMotAbsoluteMove2 = deltax/2.0
  yMotAbsoluteMove1 = -(deltay*cos(omegaRad))/2.0
  yMotAbsoluteMove2 = (deltay*cos(omegaRad))/2.0
  zMotAbsoluteMove1 = -(deltay*sin(omegaRad))/2.0
  zMotAbsoluteMove2 = (deltay*sin(omegaRad))/2.0
  

  print("columns of subrasters " + str(columnsOfSubrasters))
  print("rows of subrasters " + str(rowsOfSubrasters))  
  print("subraster columns " + str(subrasterColumns))
  print("sub rows " + str(rowsPerSubraster))  
  print("individual subraster vectors, all same for all subs (start xyz, end xyz")
  
  print(xMotAbsoluteMove1)
  print(yMotAbsoluteMove1)
  print(zMotAbsoluteMove1)
  print(xMotAbsoluteMove2)
  print(yMotAbsoluteMove2)
  print(zMotAbsoluteMove2)
  print(stepsize)
  
#  genTraj = Gen_Traj_Square.gen_traj_square(xMotAbsoluteMove1, xMotAbsoluteMove2, yMotAbsoluteMove2, yMotAbsoluteMove1, zMotAbsoluteMove2, zMotAbsoluteMove1, subrasterColumns,rowsPerSubraster)
#  Gen_Commands.gen_commands(genTraj,exptimePerCell)

  numberOfSubrasters = rowsOfSubrasters*columnsOfSubrasters
  rasterRowResultsList = [{} for i in range(0,numberOfSubrasters)]      
  cellsPerSubraster = rowsPerSubraster*subrasterColumns
  totalImages = numberOfSubrasters*cellsPerSubraster
  rasterFilePrefix = dataFilePrefix + "_Raster"
  print("number of subrasters " + str(numberOfSubrasters))
  print("cells per subrasters " + str(cellsPerSubraster))

  os.system("mkdir -p " + data_directory_name)
  os.system("chmod -R 777 " + data_directory_name)  
  

#  total_exposure_time = exptimePerCell*totalImages  
  det_lib.detector_set_num_triggers(totalImages)
  det_lib.detector_set_trigger_mode(3)
  det_lib.detector_setImagesPerFile(cellsPerSubraster)  

#this could be tricky, b/c omega is angle start that ends up in header, so if you want to arm once, this won't be right
  detectorArm(omega,img_width_per_cell,totalImages,exptimePerCell,rasterFilePrefix,data_directory_name,file_number_start) #this waits
  procFlag = int(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterProcessFlag"))  
  
  subrasters = []

  for i in range (0,rowsOfSubrasters): #this is very misleading, "end" not used? these are really the start coords of each sub?
    for j in range (0,columnsOfSubrasters): #for now, just make a list of subraster start, end coords.      
      subrasterStartX = sx1+(j*subrasterLenX)+(subrasterLenX/2.0)
      subrasterStartY = sy1+(i*subrasterLenY)+(subrasterLenY/2.0)
      subraster = {"startX":subrasterStartX,"startY":subrasterStartY,"endX":subrasterStartX+(subrasterLenX/2.0),"endy":subrasterStartY+(subrasterLenY/2.0)}
      subrasters.append(subraster)
      print(subraster)
  
#assume we now have list of first row start, last row end of subs

#from the upper left hand corner of every subraster
  print("main raster center " + str(rasterStartX) + " " + str(rasterStartY) + " " + str(rasterStartZ))  
  for i in range (0,len(subrasters)): # coarse move and go? but the zebra needs to be reset b/c it controls omega
#hey - these are all the same - just need to move the coarse stages, then every subraster is the same damn thing as far as the PI is concerned!
    genTraj = Gen_Traj_Square.gen_traj_square(xMotAbsoluteMove1, xMotAbsoluteMove2, yMotAbsoluteMove2, yMotAbsoluteMove1, zMotAbsoluteMove2, zMotAbsoluteMove1, subrasterColumns,rowsPerSubraster)
    Gen_Commands.gen_commands(genTraj,exptimePerCell)

    xRelativeMove = subrasters[i]["startX"]
    yzRelativeMove = subrasters[i]["startY"]*sin(omegaRad)
    yyRelativeMove = subrasters[i]["startY"]*cos(omegaRad)
    xMotAbsoluteMove = rasterStartX+xRelativeMove
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    zMotAbsoluteMove = rasterStartZ-yzRelativeMove
    print("absolute corner moves " + str(xMotAbsoluteMove) + " " + str(yMotAbsoluteMove) + " " + str(zMotAbsoluteMove))    
    mvaDescriptor("sampleX",xMotAbsoluteMove,"sampleY",yMotAbsoluteMove,"sampleZ",zMotAbsoluteMove)
    mvaDescriptor("fineX",0,"fineY",0,"fineZ",0)
#file_number_start not used
    rasterFilePrefix = dataFilePrefix + "_Raster_" + str(i)
    zebraVecDaqSetup(omega,img_width_per_cell,exptimePerCell,cellsPerSubraster,rasterFilePrefix,data_directory_name,file_number_start)
    total_exposure_time = exptimePerCell*cellsPerSubraster
    beamline_support.setPvValFromDescriptor("zebraPulseMax",cellsPerSubraster) 
    vectorSync()    
    beamline_support.setPvValFromDescriptor("vectorStartOmega",omega)
    beamline_support.setPvValFromDescriptor("vectorEndOmega",(img_width_per_cell*cellsPerSubraster)+omega)
    beamline_support.setPvValFromDescriptor("vectorframeExptime",exptimePerCell*1000.0)
    beamline_support.setPvValFromDescriptor("vectorNumFrames",cellsPerSubraster)
    Gen_Commands.go_all()
    beamline_support.setPvValFromDescriptor("vectorGo",1)
    vectorActiveWait()    
    vectorWait()
    zebraWait()
    seqNum = int(det_lib.detector_get_seqnum())
###??    subrasterIndex =
    if (procFlag):    
      _thread.start_new_thread(runDialsThread,(data_directory_name,filePrefix+"_Raster",i,cellsPerSubraster,seqNum))    
##  zebraWaitDownload(totalImages)
  #delete these
  time.sleep(2.0)
  det_lib.detector_stop_acquire()
  det_lib.detector_wait()
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)        
  mvaDescriptor("fineX",0,"fineY",0,"fineZ",0)
  
#  if (lastOnSample()):   #done below
#    daq_lib.setGovRobotSA()
  if not (procFlag):
    return 1
  rasterTimeout = 60
  timerCount = 0
  while (1):
    timerCount +=1
    if (timerCount>rasterTimeout):
      break
    time.sleep(1)
    print(processedRasterRowCount)
    if (processedRasterRowCount == numberOfSubrasters):
      break
  if (0):
    rasterResult = generateGridMapFine(rasterRequest,rasterEncoderMap) #I think rasterRequest is entire request, of raster type    
  else:
    rasterResult = generateGridMapFine(rasterRequest,rowsOfSubrasters=rowsOfSubrasters,columnsOfSubrasters=columnsOfSubrasters,rowsPerSubraster=rowsPerSubraster,cellsPerSubrasterRow=subrasterColumns)
    
  rasterRequest["request_obj"]["rasterDef"]["status"] = 2
##############  gotoMaxRaster(rasterResult)
#  print(rasterRequest)
  rasterRequestID = rasterRequest["uid"]
  db_lib.updateRequest(rasterRequest) #so that it will fill heatmap?
  db_lib.updatePriority(rasterRequestID,-1)
  set_field("xrecRasterFlag",rasterRequest["uid"])
  if (lastOnSample()):    
    daq_lib.setGovRobotSA()      
  return 1

  

def snakeRasterNormal(rasterReqID,grain=""):
  global rasterRowResultsList,processedRasterRowCount

#  if not (daq_lib.setGovRobotDA()):
#    return
  if (daq_utils.beamline == "fmx"):
    beamline_support.setPvValFromDescriptor("sampleProtect",0)
  daq_lib.setRobotGovState("DA")    
  rasterRequest = db_lib.getRequestByID(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  parentReqID = reqObj["parentReqID"]
  parentReqProtocol = ""
  
  if (parentReqID != -1):
    parentRequest = db_lib.getRequestByID(parentReqID)
    parentReqObj = parentRequest["request_obj"]
    parentReqProtocol = parentReqObj["protocol"]
    detDist = parentReqObj["detDist"]    
# 2/17/16 - a few things for integrating dials/spotfinding into this routine
#  filePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]
  data_directory_name = str(reqObj["directory"])
  os.system("mkdir -p " + data_directory_name)
  os.system("chmod -R 777 " + data_directory_name)  
  filePrefix = str(reqObj["file_prefix"])
  file_number_start = reqObj["file_number_start"]  
  dataFilePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]  
  exptimePerCell = reqObj["exposure_time"]
  img_width_per_cell = reqObj["img_width"]
#  sweep_end_angle = reqObj["sweep_end"]  
#really should read these two from hardware  
  wave = reqObj["wavelength"]
  xbeam = beamline_support.getPvValFromDescriptor("beamCenterX")
  ybeam = beamline_support.getPvValFromDescriptor("beamCenterY")
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"]) #these are real sample motor positions
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
#  current_omega_mod = beamline_lib.get_epics_motor_pos(beamline_support.pvNameSuffix_from_descriptor("omega"))%360.0
  rowCount = len(rasterDef["rowDefs"])
  rasterRowResultsList = [{} for i in range(0,rowCount)]    
  processedRasterRowCount = 0
  rasterEncoderMap = {}

  totalImages = 0
  for i in range(len(rasterDef["rowDefs"])):
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    totalImages = totalImages+numsteps
  rasterFilePrefix = dataFilePrefix + "_Raster"
  total_exposure_time = exptimePerCell*totalImages
  det_lib.detector_set_num_triggers(totalImages)
  det_lib.detector_set_trigger_mode(3)
#  det_lib.detector_set_trigger_exposure(exptimePerCell)  
  det_lib.detector_setImagesPerFile(numsteps)  
  detectorArm(omega,img_width_per_cell,totalImages,exptimePerCell,rasterFilePrefix,data_directory_name,file_number_start) #this waits
  if not (daq_lib.setGovRobotDA()):
    if (daq_utils.beamline == "fmx"):
      beamline_support.setPvValFromDescriptor("sampleProtect",1)    
    return      
  zebraVecDaqSetup(omega,img_width_per_cell,exptimePerCell,numsteps,rasterFilePrefix,data_directory_name,file_number_start)
  procFlag = int(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterProcessFlag"))    
  
  for i in range(len(rasterDef["rowDefs"])):
    if (daq_lib.abort_flag == 1):
      daq_lib.setGovRobotSA()
      if (daq_utils.beamline == "fmx"):
        beamline_support.setPvValFromDescriptor("sampleProtect",1)    
      return 0
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    startX = rasterDef["rowDefs"][i]["start"]["x"]
    endX = rasterDef["rowDefs"][i]["end"]["x"]
    startY = rasterDef["rowDefs"][i]["start"]["y"]
    endY = rasterDef["rowDefs"][i]["end"]["y"]
    deltaX = abs(endX-startX)
    deltaY = abs(endY-startY)
    if ((deltaX != 0) and (deltaX>deltaY or not db_lib.getBeamlineConfigParam(daq_utils.beamline,"vertRasterOn"))): #horizontal raster
####      startX = startX + (stepsize/2.0)      
####      endX = endX - (stepsize/2.0)      
      startY = startY + (stepsize/2.0)
      endY = startY
    else: #vertical raster
####      startY = startY + (stepsize/2.0)
####      endY = endY - (stepsize/2.0)
      startX = startX + (stepsize/2.0)
      endX = startX
      
    xRelativeMove = startX

    yzRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)
    print("x rel move = " + str(xRelativeMove))
    xMotAbsoluteMove = rasterStartX+xRelativeMove #note we convert relative to absolute moves, using the raster center that was saved in x,y,z
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    zMotAbsoluteMove = rasterStartZ-yzRelativeMove
##      time.sleep(1)#cosmetic
#      yRelativeMove = -((numsteps-1)*stepsize)
    xRelativeMove = endX-startX
    yRelativeMove = endY-startY
##    yRelativeMove = -(endY-startY)    
    
    yyRelativeMove = yRelativeMove*cos(omegaRad)
    yzRelativeMove = yRelativeMove*sin(omegaRad)

    xEnd = xMotAbsoluteMove + xRelativeMove
    yEnd = yMotAbsoluteMove - yyRelativeMove
    zEnd = zMotAbsoluteMove - yzRelativeMove

    if (i%2 != 0): #this is to scan opposite direction for snaking
      xEndSave = xEnd
      yEndSave = yEnd
      zEndSave = zEnd
      xEnd = xMotAbsoluteMove
      yEnd = yMotAbsoluteMove
      zEnd = zMotAbsoluteMove
      xMotAbsoluteMove = xEndSave
      yMotAbsoluteMove = yEndSave
      zMotAbsoluteMove = zEndSave
    beamline_support.setPvValFromDescriptor("zebraPulseMax",numsteps) #moved this      
    beamline_support.setPvValFromDescriptor("vectorStartOmega",omega)
    if (img_width_per_cell != 0):
      beamline_support.setPvValFromDescriptor("vectorEndOmega",(img_width_per_cell*numsteps)+omega)
    else:
      beamline_support.setPvValFromDescriptor("vectorEndOmega",omega)      
    beamline_support.setPvValFromDescriptor("vectorStartX",xMotAbsoluteMove)
    beamline_support.setPvValFromDescriptor("vectorStartY",yMotAbsoluteMove)  
    beamline_support.setPvValFromDescriptor("vectorStartZ",zMotAbsoluteMove)
######    mvaDescriptor("sampleX",xMotAbsoluteMove,"sampleY",yMotAbsoluteMove,"sampleZ",zMotAbsoluteMove)
    beamline_support.setPvValFromDescriptor("vectorEndX",xEnd)
    beamline_support.setPvValFromDescriptor("vectorEndY",yEnd)  
    beamline_support.setPvValFromDescriptor("vectorEndZ",zEnd)  
    beamline_support.setPvValFromDescriptor("vectorframeExptime",exptimePerCell*1000.0)
    beamline_support.setPvValFromDescriptor("vectorNumFrames",numsteps)
    rasterFilePrefix = dataFilePrefix + "_Raster_" + str(i)
    scanWidth = float(numsteps)*img_width_per_cell
###    beamline_support.setPvValFromDescriptor("zebraGateNumGates",numsteps)    #moved to setup
#    time.sleep(.2)
    beamline_support.setPvValFromDescriptor("vectorGo",1)
    vectorActiveWait()    
    vectorWait()
    zebraWait()
#    time.sleep(1)
    zebraWaitDownload(numsteps)
    if (procFlag):    
      if (0):
################      if (daq_utils.beamline == "amx"):
        rasterRowEncoderVals = {"x":beamline_support.getPvValFromDescriptor("zebraEncX"),"y":beamline_support.getPvValFromDescriptor("zebraEncY"),"z":beamline_support.getPvValFromDescriptor("zebraEncZ"),"omega":beamline_support.getPvValFromDescriptor("zebraEncOmega")}
#      print(rasterRowEncoderVals)
        for j in range (0,numsteps):
          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),(i*numsteps)+j+1)
#          dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),j+1)
          imIndexStr = str((i*numsteps)+j+1)
#          dataFileName = imIndexStr
#          rasterEncoderMap[dataFileName] = {"x":rasterRowEncoderVals["x"][j],"y":rasterRowEncoderVals["y"][j],"z":rasterRowEncoderVals["z"][j],"omega":rasterRowEncoderVals["omega"][j]}
          rasterEncoderMap[dataFileName[:-4]] = {"x":rasterRowEncoderVals["x"][j],"y":rasterRowEncoderVals["y"][j],"z":rasterRowEncoderVals["z"][j],"omega":rasterRowEncoderVals["omega"][j]}        
      if (daq_utils.detector_id == "EIGER-16"):
#      seqNum = beamline_support.get_any_epics_pv("XF:17IDC-ES:FMX{Det:Eig16M}cam1:SequenceId","VAL")
        seqNum = int(det_lib.detector_get_seqnum())
      else:
        seqNum = -1
#      print("running dials thread")
      _thread.start_new_thread(runDialsThread,(data_directory_name,filePrefix+"_Raster",i,numsteps,seqNum))
#      _thread.start_new_thread(runDozorThread,(data_directory_name,filePrefix+"_Raster",i,numsteps,seqNum))    
#      print("thread running")
#################  time.sleep(2.0)
  det_lib.detector_stop_acquire()
  det_lib.detector_wait()
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)      
  
      
#    set_field("xrecRasterFlag",rasterRequest["uid"])
#I guess this starts the gather loop
  print("moving to raster start")
  mvaDescriptor("sampleX",rasterStartX,"sampleY",rasterStartY,"sampleZ",rasterStartZ)
  print("done moving to raster start")  
  if (procFlag):
    rasterTimeout = 300
#  rasterTimeout = 900  
    timerCount = 0
    while (1):
      timerCount +=1
      if (daq_lib.abort_flag == 1):
        print("caught abort waiting for raster!")
        break
      if (timerCount>rasterTimeout):
        print("Raster timeout!")
        break
      time.sleep(1)
      print(str(processedRasterRowCount) + "/" + str(rowCount))      
#      print(processedRasterRowCount)
      if (processedRasterRowCount == rowCount):
        break
    if (0):
#  if (daq_utils.beamline == "amx"):                
      rasterResult = generateGridMap(rasterRequest,rasterEncoderMap) #I think rasterRequest is entire request, of raster type    
    else:
      rasterResult = generateGridMap(rasterRequest)     
    rasterRequest["request_obj"]["rasterDef"]["status"] = 2
    protocol = reqObj["protocol"]
    print("protocol = " + protocol)
    if (protocol == "multiCol" or parentReqProtocol == "multiColQ"):
      if (parentReqProtocol == "multiColQ"):    
        multiColThreshold  = parentReqObj["diffCutoff"]
      else:
        multiColThreshold  = reqObj["diffCutoff"]         
      gotoMaxRaster(rasterResult,multiColThreshold=multiColThreshold) 
    else:
      if (1):
        gotoMaxRaster(rasterResult)
  rasterRequestID = rasterRequest["uid"]
  db_lib.updateRequest(rasterRequest)
  db_lib.updatePriority(rasterRequestID,-1)
####  time.sleep(2.0)
####  if (procFlag):
####    set_field("xrecRasterFlag",rasterRequest["uid"])
#  time.sleep(2.0)
#  mvaDescriptor("omega",omega)  #this was commented, don't know why
  if (lastOnSample() and not autoRasterFlag):  
    daq_lib.setGovRobotSA()
  elif (autoRasterFlag):
#    if (daq_utils.beamline == "fmx"):
    if (1):        
      daq_lib.setGovRobotDI()    
  if (procFlag):
    time.sleep(2.0)    
    set_field("xrecRasterFlag",rasterRequest["uid"])
  if (daq_utils.beamline == "fmx"):
    beamline_support.setPvValFromDescriptor("sampleProtect",1)        
  return 1


def reprocessRaster(rasterReqID):
  global rasterRowResultsList,processedRasterRowCount

  rasterRequest = db_lib.getRequestByID(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  data_directory_name = str(reqObj["directory"])
  filePrefix = str(reqObj["file_prefix"])
  file_number_start = reqObj["file_number_start"]  
  dataFilePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]  
  exptimePerCell = reqObj["exposure_time"]
  img_width_per_cell = reqObj["img_width"]
  wave = reqObj["wavelength"]
  xbeam = beamline_support.getPvValFromDescriptor("beamCenterX")
  ybeam = beamline_support.getPvValFromDescriptor("beamCenterY")
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"]) #these are real sample motor positions
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  rowCount = len(rasterDef["rowDefs"])
  rasterRowResultsList = [{} for i in range(0,rowCount)]    
  processedRasterRowCount = 0
  rasterEncoderMap = {}
  totalImages = 0
  for i in range(len(rasterDef["rowDefs"])):
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    totalImages = totalImages+numsteps
  rasterFilePrefix = dataFilePrefix + "_Raster"
  total_exposure_time = exptimePerCell*totalImages
#  zebraVecDaqSetup(omega,img_width_per_cell,exptimePerCell,numsteps,rasterFilePrefix,data_directory_name,file_number_start)
  procFlag = 1
  
  for i in range(len(rasterDef["rowDefs"])):
    time.sleep(0.5) 
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    startX = rasterDef["rowDefs"][i]["start"]["x"]
    endX = rasterDef["rowDefs"][i]["end"]["x"]
    startY = rasterDef["rowDefs"][i]["start"]["y"]
    endY = rasterDef["rowDefs"][i]["end"]["y"]
    deltaX = abs(endX-startX)
    deltaY = abs(endY-startY)
    if ((deltaX != 0) and (deltaX>deltaY or not db_lib.getBeamlineConfigParam(daq_utils.beamline,"vertRasterOn"))): #horizontal raster
####      startX = startX + (stepsize/2.0)      
####      endX = endX - (stepsize/2.0)      
      startY = startY + (stepsize/2.0)
      endY = startY
    else: #vertical raster
####      startY = startY + (stepsize/2.0)
####      endY = endY - (stepsize/2.0)
      startX = startX + (stepsize/2.0)
      endX = startX
      
    xRelativeMove = startX

    yzRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)
    xMotAbsoluteMove = rasterStartX+xRelativeMove #note we convert relative to absolute moves, using the raster center that was saved in x,y,z
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    zMotAbsoluteMove = rasterStartZ-yzRelativeMove
##      time.sleep(1)#cosmetic
#      yRelativeMove = -((numsteps-1)*stepsize)
    xRelativeMove = endX-startX
    yRelativeMove = endY-startY
##    yRelativeMove = -(endY-startY)    
    
    yyRelativeMove = yRelativeMove*cos(omegaRad)
    yzRelativeMove = yRelativeMove*sin(omegaRad)

    xEnd = xMotAbsoluteMove + xRelativeMove
    yEnd = yMotAbsoluteMove - yyRelativeMove
    zEnd = zMotAbsoluteMove - yzRelativeMove

    if (i%2 != 0): #this is to scan opposite direction for snaking
      xEndSave = xEnd
      yEndSave = yEnd
      zEndSave = zEnd
      xEnd = xMotAbsoluteMove
      yEnd = yMotAbsoluteMove
      zEnd = zMotAbsoluteMove
      xMotAbsoluteMove = xEndSave
      yMotAbsoluteMove = yEndSave
      zMotAbsoluteMove = zEndSave
    rasterFilePrefix = dataFilePrefix + "_Raster_" + str(i)
    scanWidth = float(numsteps)*img_width_per_cell
    if (procFlag):    
      if (daq_utils.detector_id == "EIGER-16"):
        seqNum = int(det_lib.detector_get_seqnum())
      else:
        seqNum = -1
      _thread.start_new_thread(runDialsThread,(data_directory_name,filePrefix+"_Raster",i,numsteps,-1)) #note the -1 last param. That eliminates rerun of eiger2cbf.
#I guess this starts the gather loop
  if (procFlag):
    rasterTimeout = 300
#  rasterTimeout = 900  
    timerCount = 0
    while (1):
      timerCount +=1
      if (daq_lib.abort_flag == 1):
        print("caught abort waiting for raster!")
        break
      if (timerCount>rasterTimeout):
        print("Raster timeout!")
        break
      time.sleep(1)
      print(str(processedRasterRowCount) + "/" + str(rowCount))      
#      print(processedRasterRowCount)
      if (processedRasterRowCount == rowCount):
        break
    if (0):
#  if (daq_utils.beamline == "amx"):                
      rasterResult = generateGridMap(rasterRequest,rasterEncoderMap) #I think rasterRequest is entire request, of raster type    
    else:
      rasterResult = generateGridMap(rasterRequest)     
    rasterRequest["request_obj"]["rasterDef"]["status"] = 2
    protocol = reqObj["protocol"]
    print("protocol = " + protocol)
    if (1):
      gotoMaxRaster(rasterResult)
  rasterRequestID = rasterRequest["uid"]
  db_lib.updateRequest(rasterRequest)
  db_lib.updatePriority(rasterRequestID,-1)
####  time.sleep(2.0)
####  if (procFlag):
####    set_field("xrecRasterFlag",rasterRequest["uid"])
#  time.sleep(2.0)
  if (procFlag):
    time.sleep(2.0)    
    set_field("xrecRasterFlag",rasterRequest["uid"])
  return 1


def snakeStepRaster(rasterReqID,grain=""): #12/19 - only tested recently, but apparently works. I'm not going to remove any commented lines.
  if not (daq_lib.setGovRobotDA()):
    return
  rasterRequest = db_lib.getRequestByID(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  sweep_start_angle = reqObj["sweep_start"]
  sweep_end_angle = reqObj["sweep_end"]
  range_degrees = sweep_end_angle-sweep_start_angle
  imgWidth = reqObj["img_width"]
  numImagesPerStep = int((sweep_end_angle - sweep_start_angle) / imgWidth)  
  data_directory_name = str(reqObj["directory"])
  os.system("mkdir -p " + data_directory_name)
  os.system("chmod -R 777 " + data_directory_name)  
  filePrefix = str(reqObj["file_prefix"])
  file_number_start = reqObj["file_number_start"]  
  dataFilePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]  
  exptimePerCell = reqObj["exposure_time"]
  img_width_per_cell = reqObj["img_width"]
#really should read these two from hardware  
  wave = reqObj["wavelength"]
  xbeam = beamline_support.getPvValFromDescriptor("beamCenterX")
  ybeam = beamline_support.getPvValFromDescriptor("beamCenterY")
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"]) #these are real sample motor positions
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
#  current_omega_mod = beamline_lib.get_epics_motor_pos(beamline_support.pvNameSuffix_from_descriptor("omega"))%360.0
  totalImages = 0
  for i in range(len(rasterDef["rowDefs"])): #just counting images here for single detector arm
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"]*numImagesPerStep)
    totalImages = totalImages+numsteps
  print("total images = " + str(totalImages))
  rasterFilePrefix = dataFilePrefix
  detector_dead_time = det_lib.detector_get_deadtime()  
  total_exposure_time = exptimePerCell*totalImages
  exposureTimePerImage =  exptimePerCell - detector_dead_time
  det_lib.detector_set_num_triggers(totalImages)
  detector_set_period(exptimePerCell)
  detector_set_exposure_time(exposureTimePerImage)
  det_lib.detector_set_trigger_mode(3)
#  det_lib.detector_set_trigger_exposure(exptimePerCell)  
  det_lib.detector_setImagesPerFile(numImagesPerStep)
  detectorArm(sweep_start_angle,img_width_per_cell,totalImages,exptimePerCell,filePrefix,data_directory_name,file_number_start) #this waits
###?  detectorArm(omega,img_width_per_cell,totalImages,exptimePerCell,rasterFilePrefix,data_directory_name,file_number_start) #this waits
#  zebraVecDaqSetup(omega,img_width_per_cell,exptimePerCell,numsteps,rasterFilePrefix,data_directory_name,file_number_start)  
  
  for i in range(len(rasterDef["rowDefs"])):
    if (daq_lib.abort_flag == 1):
      return 0
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    startX = rasterDef["rowDefs"][i]["start"]["x"]
    endX = rasterDef["rowDefs"][i]["end"]["x"]
    startY = rasterDef["rowDefs"][i]["start"]["y"]
    endY = rasterDef["rowDefs"][i]["end"]["y"]
    deltaX = abs(endX-startX)
    deltaY = abs(endY-startY)
    if (deltaX>deltaY): #horizontal raster - I think this was decided in the rasterDefine, and we're just checking
      startY = startY + (stepsize/2.0)
      endY = startY
    else: #vertical raster
      startX = startX + (stepsize/2.0)
      endX = startX
      
    xRelativeMove = startX

    yzRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)
    print("x rel move = " + str(xRelativeMove))
    xMotAbsoluteMove = rasterStartX+xRelativeMove #note we convert relative to absolute moves, using the raster center that was saved in x,y,z
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    zMotAbsoluteMove = rasterStartZ-yzRelativeMove
##      time.sleep(1)#cosmetic
#      yRelativeMove = -((numsteps-1)*stepsize)
    xRelativeMove = endX-startX
    yRelativeMove = endY-startY
##    yRelativeMove = -(endY-startY)    
    
    yyRelativeMove = yRelativeMove*cos(omegaRad)
    yzRelativeMove = yRelativeMove*sin(omegaRad)

    xEnd = xMotAbsoluteMove + xRelativeMove
    yEnd = yMotAbsoluteMove - yyRelativeMove
    zEnd = zMotAbsoluteMove - yzRelativeMove

    if (i%2 != 0): #this is to scan opposite direction for snaking
      xEndSave = xEnd
      yEndSave = yEnd
      zEndSave = zEnd
      xEnd = xMotAbsoluteMove
      yEnd = yMotAbsoluteMove
      zEnd = zMotAbsoluteMove
      xMotAbsoluteMove = xEndSave
      yMotAbsoluteMove = yEndSave
      zMotAbsoluteMove = zEndSave
    if (deltaX>deltaY): #horizontal raster - I think this was decided in the rasterDefine, and we're just checking      
      stepX = (xEnd-xMotAbsoluteMove)/numsteps
      stepY = (yEnd-yMotAbsoluteMove)/numsteps
      stepZ = (zEnd-zMotAbsoluteMove)/numsteps
    else:
      stepX = -(xEnd-xMotAbsoluteMove)/numsteps
      stepY = -(yEnd-yMotAbsoluteMove)/numsteps
      stepZ = -(zEnd-zMotAbsoluteMove)/numsteps
      
#    zebraVecDaqSetup(omega,img_width_per_cell,exptimePerCell,numImagesPerStep,rasterFilePrefix,data_directory_name,file_number_start)      
    for j in range (0,numsteps): #so maybe I have everything here and just need to bump the appropriate motors each step increment, not sure about signs
#???      beamline_support.setPvValFromDescriptor("zebraPulseMax",numImagesPerStep) #moved this            
#???      beamline_support.setPvValFromDescriptor("vectorStartOmega",omega)
#      beamline_support.setPvValFromDescriptor("vectorStartX",xMotAbsoluteMove+(j*stepX))
#      beamline_support.setPvValFromDescriptor("vectorStartY",yMotAbsoluteMove-(j*stepY))  
#      beamline_support.setPvValFromDescriptor("vectorStartZ",zMotAbsoluteMove-(j*stepZ))
      mvaDescriptor("sampleX",xMotAbsoluteMove+(j*stepX)+(stepX/2.0),"sampleY",yMotAbsoluteMove-(j*stepY)-(stepY/2.0),"sampleZ",zMotAbsoluteMove-(j*stepZ)-(stepZ/2.0))
#      beamline_support.setPvValFromDescriptor("vectorEndX",xMotAbsoluteMove+((j+1)*stepX))
#      beamline_support.setPvValFromDescriptor("vectorEndY",yMotAbsoluteMove-((j+1)*stepY))
#      beamline_support.setPvValFromDescriptor("vectorEndZ",zMotAbsoluteMove-((j+1)*stepZ))
      vectorSync()
      if (j == 0):
        zebraDaqNoDet(sweep_start_angle,range_degrees,img_width_per_cell,exptimePerCell,filePrefix,data_directory_name,file_number_start,3)
      else:
        angle_start = sweep_start_angle
        scanWidth = range_degrees
        angle_end = angle_start+scanWidth        
        beamline_support.setPvValFromDescriptor("vectorStartOmega",angle_start)
        beamline_support.setPvValFromDescriptor("vectorEndOmega",angle_end)
        
        beamline_support.setPvValFromDescriptor("vectorGo",1)
        vectorActiveWait()  
        vectorWait()
        zebraWait()
        beamline_support.setPvValFromDescriptor("vectorBufferTime",3)      

#      beamline_support.setPvValFromDescriptor("vectorframeExptime",exptimePerCell*1000.0)
#      beamline_support.setPvValFromDescriptor("vectorNumFrames",numImagesPerStep)
#      beamline_support.setPvValFromDescriptor("vectorGo",1)
#      vectorActiveWait()    
#      vectorWait()
#      zebraWait()
#      zebraWaitDownload(numsteps)

  det_lib.detector_stop_acquire()
  det_lib.detector_wait()
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)      
  
#  db_lib.updateRequest(rasterRequest) #not sure if this makes sense here
  db_lib.updatePriority(rasterReqID,-1)  
  if (lastOnSample()):  
    daq_lib.setGovRobotSA()      
  return 1


def snakeStepRasterSpec(rasterReqID,grain=""): #12/19 - only tested recently, but apparently works. I'm not going to remove any commented lines.
  rasterRequest = db_lib.getRequestByID(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  sweep_start_angle = reqObj["sweep_start"]
  sweep_end_angle = reqObj["sweep_end"]
  range_degrees = sweep_end_angle-sweep_start_angle
  imgWidth = reqObj["img_width"]
  numImagesPerStep = int((sweep_end_angle - sweep_start_angle) / imgWidth)  
  data_directory_name = str(reqObj["directory"])
  os.system("mkdir -p " + data_directory_name)
  os.system("chmod -R 777 " + data_directory_name)  
  filePrefix = str(reqObj["file_prefix"])
  file_number_start = reqObj["file_number_start"]  
  dataFilePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]  
  exptimePerCell = reqObj["exposure_time"]
  img_width_per_cell = reqObj["img_width"]
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"]) #these are real sample motor positions
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  rasterFilePrefix = dataFilePrefix
  for i in range(len(rasterDef["rowDefs"])):
    if (daq_lib.abort_flag == 1):
      return 0
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    startX = rasterDef["rowDefs"][i]["start"]["x"]
    endX = rasterDef["rowDefs"][i]["end"]["x"]
    startY = rasterDef["rowDefs"][i]["start"]["y"]
    endY = rasterDef["rowDefs"][i]["end"]["y"]
    deltaX = abs(endX-startX)
    deltaY = abs(endY-startY)
    if (deltaX>deltaY): #horizontal raster - I think this was decided in the rasterDefine, and we're just checking
      startY = startY + (stepsize/2.0)
      endY = startY
    else: #vertical raster
      startX = startX + (stepsize/2.0)
      endX = startX
    xRelativeMove = startX
    yzRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)
    print("x rel move = " + str(xRelativeMove))
    xMotAbsoluteMove = rasterStartX+xRelativeMove #note we convert relative to absolute moves, using the raster center that was saved in x,y,z
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    zMotAbsoluteMove = rasterStartZ-yzRelativeMove
#      yRelativeMove = -((numsteps-1)*stepsize)
    xRelativeMove = endX-startX
    yRelativeMove = endY-startY
##    yRelativeMove = -(endY-startY)    
    
    yyRelativeMove = yRelativeMove*cos(omegaRad)
    yzRelativeMove = yRelativeMove*sin(omegaRad)

    xEnd = xMotAbsoluteMove + xRelativeMove
    yEnd = yMotAbsoluteMove - yyRelativeMove
    zEnd = zMotAbsoluteMove - yzRelativeMove

    if (i%2 != 0): #this is to scan opposite direction for snaking
      xEndSave = xEnd
      yEndSave = yEnd
      zEndSave = zEnd
      xEnd = xMotAbsoluteMove
      yEnd = yMotAbsoluteMove
      zEnd = zMotAbsoluteMove
      xMotAbsoluteMove = xEndSave
      yMotAbsoluteMove = yEndSave
      zMotAbsoluteMove = zEndSave
    if (deltaX>deltaY): #horizontal raster - I think this was decided in the rasterDefine, and we're just checking      
      stepX = (xEnd-xMotAbsoluteMove)/numsteps
      stepY = (yEnd-yMotAbsoluteMove)/numsteps
      stepZ = (zEnd-zMotAbsoluteMove)/numsteps
    else:
      stepX = -(xEnd-xMotAbsoluteMove)/numsteps
      stepY = -(yEnd-yMotAbsoluteMove)/numsteps
      stepZ = -(zEnd-zMotAbsoluteMove)/numsteps
    for j in range (0,numsteps): #so maybe I have everything here and just need to bump the appropriate motors each step increment, not sure about signs
      mvaDescriptor("sampleX",xMotAbsoluteMove+(j*stepX)+(stepX/2.0),"sampleY",yMotAbsoluteMove-(j*stepY)-(stepY/2.0),"sampleZ",zMotAbsoluteMove-(j*stepZ)-(stepZ/2.0))
      collectSpec(data_directory_name+"/"+filePrefix+"_"+str(file_number_start),gotoSA=False)    
  db_lib.updatePriority(rasterReqID,-1)  
  if (lastOnSample()):  
    daq_lib.setGovRobotSA()      
  return 1

def setGridRasterParams(xsep,ysep,xstep,ystep,sizex,sizey,stepsize):
  """setGridRasterParams(xsep,ysep,xstep,ystep,sizex,sizey,stepsize)"""
  db_lib.setBeamlineConfigParam("fmx","gridRasterXSep",float(xsep))
  db_lib.setBeamlineConfigParam("fmx","gridRasterYSep",float(ysep))
  db_lib.setBeamlineConfigParam("fmx","gridRasterXStep",int(xstep))
  db_lib.setBeamlineConfigParam("fmx","gridRasterYStep",int(ystep))
  db_lib.setBeamlineConfigParam("fmx","gridRasterSizeX",float(sizex))
  db_lib.setBeamlineConfigParam("fmx","gridRasterSizeY",float(sizey))
  db_lib.setBeamlineConfigParam("fmx","gridRasterStepsize",float(stepsize))

def printGridRasterParams():
  """printGridRasterParams()"""

  print(db_lib.getBeamlineConfigParam("fmx","gridRasterXSep"))
  print(db_lib.getBeamlineConfigParam("fmx","gridRasterYSep"))
  print(db_lib.getBeamlineConfigParam("fmx","gridRasterXStep"))
  print(db_lib.getBeamlineConfigParam("fmx","gridRasterYStep"))
  print(db_lib.getBeamlineConfigParam("fmx","gridRasterSizeX"))
  print(db_lib.getBeamlineConfigParam("fmx","gridRasterSizeY"))
  print(db_lib.getBeamlineConfigParam("fmx","gridRasterStepsize"))
  

def gridRaster(currentRequest):
  if not (daq_lib.setGovRobotDA()):
    return
  
  sampleID = currentRequest["sample"]  
  reqObj = currentRequest["request_obj"]
#  rasterDef = reqObj["rasterDef"]
  omega = motorPosFromDescriptor("omega")
#  omega = float(rasterDef["omega"])
  omegaRad = math.radians(omega)
  xwells = int(db_lib.getBeamlineConfigParam("fmx","gridRasterXStep"))
  ywells = int(db_lib.getBeamlineConfigParam("fmx","gridRasterYStep"))        
  xsep = float(db_lib.getBeamlineConfigParam("fmx","gridRasterXSep"))
  ysep = float(db_lib.getBeamlineConfigParam("fmx","gridRasterYSep"))
  sizex = float(db_lib.getBeamlineConfigParam("fmx","gridRasterSizeX"))
  sizey = float(db_lib.getBeamlineConfigParam("fmx","gridRasterSizeY"))        
  stepsize = float(db_lib.getBeamlineConfigParam("fmx","gridRasterStepsize"))
#  rasterStartX = float(rasterDef["x"]) #these are real sample motor positions
#  rasterStartY = float(rasterDef["y"])
#  rasterStartZ = float(rasterDef["z"])  
  rasterStartX = motorPosFromDescriptor("sampleX") #these are real sample motor positions
  rasterStartY = motorPosFromDescriptor("sampleY")
  rasterStartZ = motorPosFromDescriptor("sampleZ")
  yzRelativeMove = ysep*sin(omegaRad)
  yyRelativeMove = ysep*cos(omegaRad)
  for i in range (0,ywells):
    for j in range (0,xwells):
      mvaDescriptor("sampleX",rasterStartX+(j*xsep),"sampleY",rasterStartY+(i*yyRelativeMove),"sampleZ",rasterStartZ+(i*yzRelativeMove))
      mvaDescriptor("omega",omega)      
#      rasterReqID = defineRectRaster(currentRequest,90,90,10,j*xsep,i*yyRelativeMove,i*yzRelativeMove)
      rasterReqID = defineRectRaster(currentRequest,sizex,sizey,stepsize)      
      snakeRaster(rasterReqID)


def runRasterScan(currentRequest,rasterType=""): #this actually defines and runs
  sampleID = currentRequest["sample"]
  if (rasterType=="Fine"):
    set_field("xrecRasterFlag","100")    
    rasterReqID = defineRectRaster(currentRequest,90,90,10)
#    rasterReqID = defineRectRaster(currentRequest,50,50,10)     
    snakeRaster(rasterReqID)
  elif (rasterType=="Coarse"):
    set_field("xrecRasterFlag","100")    
#    rasterReqID = defineRectRaster(currentRequest,330,210,30)
    rasterReqID = defineRectRaster(currentRequest,630,390,30)     
    snakeRaster(rasterReqID)
  elif (rasterType=="autoVector"):
    set_field("xrecRasterFlag","100")    
#    rasterReqID = defineRectRaster(currentRequest,330,210,30)
    rasterReqID = defineRectRaster(currentRequest,615,375,15)     
    snakeRaster(rasterReqID)
  elif (rasterType=="Line"):  
    set_field("xrecRasterFlag","100")    
    mvrDescriptor("omega",90)
#    rasterReqID = defineRectRaster(currentRequest,10,150,10)
    rasterReqID = defineRectRaster(currentRequest,10,290,10)    
    snakeRaster(rasterReqID)
    set_field("xrecRasterFlag","100")    
  else:
    rasterReqID = getXrecLoopShape(currentRequest)
    print("snake raster " + str(rasterReqID))
    time.sleep(1) #I think I really need this, not sure why
    snakeRaster(rasterReqID)
#    set_field("xrecRasterFlag",100)    

def gotoMaxRaster(rasterResult,multiColThreshold=-1):
  global autoVectorCoarseCoords,autoVectorFlag
#  print("raster result = ")
#  print(rasterResult)
  requestID = rasterResult["request"]
  if (rasterResult["result_obj"]["rasterCellResults"]['resultObj'] == None):
#  if (rasterResult["result_obj"]["rasterCellResults"]['resultObj']["data"] == None):    
    print("no raster result!!\n")
    return
  ceiling = 0.0
  floor = 100000000.0 #for resolution where small number means high score
  hotFile = ""
  scoreOption = ""
  print("in gotomax")
#  print(rasterResult)
  cellResults = rasterResult["result_obj"]["rasterCellResults"]['resultObj']
#  cellResults = rasterResult["result_obj"]["rasterCellResults"]['resultObj']["data"]["response"]    
  rasterMap = rasterResult["result_obj"]["rasterCellMap"]  
  rasterScoreFlag = int(db_lib.beamlineInfo(daq_utils.beamline,'rasterScoreFlag')["index"])
  if (rasterScoreFlag==0):
    scoreOption = "spot_count_no_ice"
  elif (rasterScoreFlag==1):
    scoreOption = "d_min"
  else:
    scoreOption = "total_intensity"
  for i in range (0,len(cellResults)):
#    print(cellResults[i])
#    print("\n")
    try:
      scoreVal = float(cellResults[i][scoreOption])
    except TypeError:
#      continue
      scoreVal = 0.0
    if (multiColThreshold>-1):
      print("doing multicol")
      if (scoreVal >= multiColThreshold):
        hitFile = cellResults[i]["image"]
###        hitFile = cellResults[i]["masterIndex"]                
        hitCoords = rasterMap[hitFile[:-4]]
#        sampID = rasterResult['result_obj']['sample_id']
        parentReqID = rasterResult['result_obj']["parentReqID"]
        if (parentReqID == -1):
          addMultiRequestLocation(requestID,hitCoords,i)
        else:
          addMultiRequestLocation(parentReqID,hitCoords,i)        
    if (scoreOption == "d_min"):
      if (scoreVal < floor and scoreVal != -1):
        floor = scoreVal
        hotFile = cellResults[i]["image"]        
#        hotFile = str(int(cellResults[i]["masterIndex"]))
    else:
      if (scoreVal > ceiling):
        ceiling = scoreVal
        hotFile = cellResults[i]["image"]        
#        hotFile = str(int(cellResults[i]["masterIndex"]))
  if (hotFile != ""):
    print(ceiling)
    print(floor)
    print(hotFile)
#    rasterMap = rasterResult["result_obj"]["rasterCellMap"]
#    hotCoords = rasterMap[hotFile]
    hotCoords = rasterMap[hotFile[:-4]]     
    x = hotCoords["x"]
    y = hotCoords["y"]
    z = hotCoords["z"]
    print("goto " + str(x) + " " + str(y) + " " + str(z))
    mvaDescriptor("sampleX",x,"sampleY",y,"sampleZ",z)
    if (autoVectorFlag): #if we found a hotspot, then look again at cellResults for coarse vector start and end
      xminColumn = [] #these are the "line rasters" of the ends of threshold points determined by the first pass on the raster results
      xmaxColumn = []
      vectorThreshold = 0.7*ceiling
      xmax = -1000000
      xmin = 1000000
      ymin = 0
      ymax = 0
      zmin = 0
      zmax = 0
      for i in range (0,len(cellResults)): #first find the xmin and xmax of threshold (left and right ends of vector)
        try:
          scoreVal = float(cellResults[i][scoreOption])
        except TypeError:
          scoreVal = 0.0
        if (scoreVal > vectorThreshold):
          hotFile = cellResults[i]["image"]
          hotCoords = rasterMap[hotFile[:-4]]             
          x = hotCoords["x"]
          if (x<xmin):
            xmin = x
          if (x>xmax):
            xmax = x
      for i in range (0,len(cellResults)): #now grab the columns of cells on xmin and xmax, like line scan results on the ends
        fileKey = cellResults[i]["image"]
        coords = rasterMap[fileKey[:-4]]
        x = coords["x"]
        if (x == xmin): #cell is in left column
          xEdgeCellResult = {"coords":coords,"processingResults":cellResults[i]}
          xminColumn.append(xEdgeCellResult)
        if (x == xmax):
          xEdgeCellResult = {"coords":coords,"processingResults":cellResults[i]}
          xmaxColumn.append(xEdgeCellResult)
      maxIndex = -10000
      minIndex = 10000
      for i in range (0,len(xminColumn)): #find the midpoint of the left column that is in the threshold range
        try:
          scoreVal = float(xminColumn[i]["processingResults"][scoreOption])
        except TypeError:
          scoreVal = 0.0
        if (scoreVal > vectorThreshold):
          if (minIndex<0): #you only need the first one that beats the threshold
            minIndex = i
          if (i>maxIndex):
            maxIndex = i
      middleIndex = int((minIndex+maxIndex)/2)
      xmin = xminColumn[middleIndex]["coords"]["x"]
      ymin = xminColumn[middleIndex]["coords"]["y"]
      zmin = xminColumn[middleIndex]["coords"]["z"]                            
      for i in range (0,len(xmaxColumn)): #do same as above for right column
        try:
          scoreVal = float(xmaxColumn[i]["processingResults"][scoreOption])
        except TypeError:
          scoreVal = 0.0
        if (scoreVal > vectorThreshold):
          if (minIndex<0):
            minIndex = i
          if (i>maxIndex):
            maxIndex = i
      middleIndex = int((minIndex+maxIndex)/2)
      xmax = xmaxColumn[middleIndex]["coords"]["x"]
      ymax = xmaxColumn[middleIndex]["coords"]["y"]
      zmax = xmaxColumn[middleIndex]["coords"]["z"]                            
          
      autoVectorCoarseCoords = {"start":{"x":xmin,"y":ymin,"z":zmin},"end":{"x":xmax,"y":ymax,"z":zmax}}

      
def addMultiRequestLocation(parentReqID,hitCoords,locIndex): #rough proto of what to pass here for details like how to organize data
  parentRequest = db_lib.getRequestByID(parentReqID)
  sampleID = parentRequest["sample"]

  print (str(sampleID))
  print (hitCoords)
  currentOmega = round(motorPosFromDescriptor("omega"),2)
#  runNum = db_lib.incrementSampleRequestCount(sampleID)
#  dataDirectory = parentRequest['directory']+"_"+str(locIndex)
  dataDirectory = parentRequest["request_obj"]['directory']+"multi_"+str(locIndex)
  runNum = parentRequest["request_obj"]['runNum']
  tempnewStratRequest = daq_utils.createDefaultRequest(sampleID)
  ss = parentRequest["request_obj"]["sweep_start"]
  sweepStart = ss - 2.5
  sweepEnd = ss + 2.5
  imgWidth = parentRequest["request_obj"]['img_width']
  exptime = parentRequest["request_obj"]['exposure_time']
  currentDetDist = parentRequest["request_obj"]['detDist']
  
  newReqObj = tempnewStratRequest["request_obj"]
  newReqObj["sweep_start"] = sweepStart
  newReqObj["sweep_end"] = sweepEnd
  newReqObj["img_width"] = imgWidth
  newReqObj["exposure_time"] = exptime
  newReqObj["detDist"] = currentDetDist
  newReqObj["directory"] = dataDirectory  
  newReqObj["pos_x"] = hitCoords['x']
  newReqObj["pos_y"] = hitCoords['y']
  newReqObj["pos_z"] = hitCoords['z']
  newReqObj["fastDP"] = False
  newReqObj["fastEP"] = False
  newReqObj["dimple"] = False    
  newReqObj["xia2"] = False
  newReqObj["runNum"] = runNum
  newRequestUID = db_lib.addRequesttoSample(sampleID,newReqObj["protocol"],daq_utils.owner,newReqObj,priority=6000,proposalID=daq_utils.getProposalID()) # a higher priority
  
    
#these next three differ a little from the gui. the gui uses isChecked, b/c it was too intense to keep hitting the pv, also screen pix vs image pix
#careful here, I'm hardcoding the view I think we'll use for definePolyRaster, which is only routine that uses this. 
def getCurrentFOV(): #used only by 4 routines below - BUT THIS IS A GUESS! 
  fov = {"x":0.0,"y":0.0}
  fov["x"] = daq_utils.lowMagFOVx/2.0 #low mag zoom for xrecloopfind
  fov["y"] = daq_utils.lowMagFOVy/2.0
  
  return fov


def screenXmicrons2pixels(microns):
  fov = getCurrentFOV()
  fovX = fov["x"]
  return int(round(microns*(daq_utils.lowMagPixX/fovX)))

def screenYmicrons2pixels(microns):
  fov = getCurrentFOV()
  fovY = fov["y"]
  return int(round(microns*(daq_utils.lowMagPixY/fovY)))  


def screenXPixels2microns(pixels):
  fov = getCurrentFOV()
  fovX = fov["x"]
  return float(pixels)*(fovX/daq_utils.lowMagPixX)

def screenYPixels2microns(pixels):
  fov = getCurrentFOV()
  fovY = fov["y"]
  return float(pixels)*(fovY/daq_utils.lowMagPixY)

def defineTiledRaster(rasterDef,numsteps_h,numsteps_v,origRasterCenterScreenX,origRasterCenterScreenY): #I need this to redefine composite for tiling. Much of the reqObf can stay same.
  
###  sampleID = currentRequest["sample"]
  rasterDef["rowDefs"] = []
  stepsize = rasterDef["stepsize"]
#  numsteps_h = int(raster_w/stepsize)
#  numsteps_v = int(raster_h/stepsize) #the numsteps is decided in code, so is already odd
  point_offset_x = origRasterCenterScreenX-(numsteps_h*stepsize)/2.0
  point_offset_y = origRasterCenterScreenY-(numsteps_v*stepsize)/2.0
###  point_offset_x = -(numsteps_h*stepsize)/2.0
###  point_offset_y = -(numsteps_v*stepsize)/2.0
  if (numsteps_v > numsteps_h): #vertical raster
    for i in range(numsteps_h):
      vectorStartX = point_offset_x+(i*stepsize)
      vectorEndX = vectorStartX
      vectorStartY = point_offset_y
      vectorEndY = vectorStartY + (numsteps_v*stepsize)
      newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":numsteps_v}
      rasterDef["rowDefs"].append(newRowDef)
  else: #horizontal raster
    for i in range(numsteps_v):
      vectorStartX = point_offset_x
      vectorEndX = vectorStartX + (numsteps_h*stepsize)
      vectorStartY = point_offset_y+(i*stepsize)
      vectorEndY = vectorStartY
      newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":numsteps_h}
      rasterDef["rowDefs"].append(newRowDef)
  rasterDef["status"] = 1 # this will tell clients that the raster should be displayed.      
  return rasterDef

def defineRectRaster(currentRequest,raster_w_s,raster_h_s,stepsizeMicrons_s,xoff=0.0,yoff=0.0,zoff=0.0): #maybe point_x and point_y are image center? #everything can come as microns, make this a horz vector scan, note this never deals with pixels.
  
  sampleID = currentRequest["sample"]
  sample = db_lib.getSampleByID(sampleID)
  try:
    propNum = sample["proposalID"]
  except KeyError:
    propNum = 999999
  raster_h = float(raster_h_s)
  raster_w = float(raster_w_s)
  stepsize = float(stepsizeMicrons_s)
  beamWidth = stepsize
  beamHeight = stepsize
  rasterDef = {"beamWidth":beamWidth,"beamHeight":beamHeight,"status":0,"x":motorPosFromDescriptor("sampleX")+xoff,"y":motorPosFromDescriptor("sampleY")+yoff,"z":motorPosFromDescriptor("sampleZ")+zoff,"omega":motorPosFromDescriptor("omega"),"stepsize":stepsize,"rowDefs":[]} 
  numsteps_h = int(raster_w/stepsize)
  numsteps_v = int(raster_h/stepsize) #the numsteps is decided in code, so is already odd
  point_offset_x = -(numsteps_h*stepsize)/2.0
  point_offset_y = -(numsteps_v*stepsize)/2.0
  if (numsteps_v > numsteps_h): #vertical raster
    for i in range(numsteps_h):
      vectorStartX = point_offset_x+(i*stepsize)
      vectorEndX = vectorStartX
      vectorStartY = point_offset_y
      vectorEndY = vectorStartY + (numsteps_v*stepsize)
      newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":numsteps_v}
      rasterDef["rowDefs"].append(newRowDef)
  else: #horizontal raster
    for i in range(numsteps_v):
      vectorStartX = point_offset_x
      vectorEndX = vectorStartX + (numsteps_h*stepsize)
      vectorStartY = point_offset_y+(i*stepsize)
      vectorEndY = vectorStartY
      newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":numsteps_h}
      rasterDef["rowDefs"].append(newRowDef)

  tempnewRasterRequest = daq_utils.createDefaultRequest(sampleID)
  reqObj = tempnewRasterRequest["request_obj"]
  reqObj["protocol"] = "raster"
#  reqObj["exposure_time"] = .05
#  reqObj["img_width"] = .05    
  reqObj["exposure_time"] = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultTime")
  reqObj["img_width"] = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultWidth")
  reqObj["attenuation"] = db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultTrans")
  reqObj["directory"] = reqObj["directory"]+"/rasterImages/"
  if (numsteps_h == 1): #column raster
    reqObj["file_prefix"] = reqObj["file_prefix"]+"_l"
    rasterDef["rasterType"] = "column"
  else:
    reqObj["file_prefix"] = reqObj["file_prefix"]+"_r"
    rasterDef["rasterType"] = "normal"
  reqObj["rasterDef"] = rasterDef #should this be something like self.currentRasterDef?
  reqObj["rasterDef"]["status"] = 1 # this will tell clients that the raster should be displayed.
  runNum = db_lib.incrementSampleRequestCount(sampleID)
  reqObj["runNum"] = runNum
  reqObj["parentReqID"] = currentRequest["uid"]
  newRasterRequestUID = db_lib.addRequesttoSample(sampleID,reqObj["protocol"],daq_utils.owner,reqObj,priority=5000,proposalID=propNum)
#  newRasterRequestUID = db_lib.addRequesttoSample(sampleID,reqObj["protocol"],daq_utils.owner,reqObj,priority=5000,proposalID=daq_utils.getProposalID())  
  set_field("xrecRasterFlag",newRasterRequestUID)
  time.sleep(1)
  return newRasterRequestUID



def collectSpec(filename,gotoSA=True):
  """collectSpec(filenamePrefix) : collect a spectrum, save to file"""  
  daq_lib.setGovRobotXF()      
  open_shutter()
  beamline_support.setPvValFromDescriptor("mercuryEraseStart",1)
  while (1):
    if (beamline_support.getPvValFromDescriptor("mercuryReadStat") == 0):
      break
    time.sleep(0.05)
  specArray = beamline_support.getPvValFromDescriptor("mercurySpectrum")
  plt.plot(specArray)
  plt.show(block=False)
  nowtime_s = str(int(time.time()))
  specFileName = filename + "_" + nowtime_s + ".txt"
  specFile = open(specFileName,"w+")
  channelCount = len(specArray)
  for i in range (0,channelCount):
    if (i == 0):
      specFile.write(str(specArray[i]))
    else:
      specFile.write("," + str(specArray[i]))
  specFile.close()
  close_shutter()
  if (gotoSA):
    daq_lib.setGovRobotSA()    

    
def eScan(energyScanRequest):
  plt.clf()
  sampleID = energyScanRequest["sample"]
  reqObj = energyScanRequest["request_obj"]
  exptime = reqObj['exposure_time']
  targetEnergy = reqObj['scanEnergy'] *1000.0
  stepsize = reqObj['stepsize']
  steps = reqObj['steps']
  left = -(steps*stepsize)/2
  right = (steps*stepsize)/2
  mcaRoiLo = reqObj['mcaRoiLo']
  mcaRoiHi = reqObj['mcaRoiHi']
  if (1):
#  if (daq_utils.beamline == "fmx"):                
    beamline_support.setPvValFromDescriptor("mcaRoiLo",mcaRoiLo)
    beamline_support.setPvValFromDescriptor("mcaRoiHi",mcaRoiHi)      
  
  print("energy scan for " + str(targetEnergy))
  scan_element = reqObj['element']
  mvaDescriptor("energy",targetEnergy)
#  if not (daq_lib.setGovRobotDA()):
  if not (daq_lib.setGovRobotXF()):    
    return
  open_shutter()
  scanID = RE(bp.rel_scan([mercury],vdcm.e,left,right,steps),[LivePlot("mercury_mca_rois_roi0_count")])
  close_shutter()
  if (lastOnSample()):  
    daq_lib.setGovRobotSA()  
  scanData = db[scanID[0]]
  for ev in scanData.events():
    if ('mercury_mca_spectrum' in ev['data']):
      print(ev['seq_num'], ev['data']['mercury_mca_spectrum'].sum())
      
  scanDataTable = scanData.table()
#these next lines only make sense for the mca
  nowtime_s = str(int(time.time()))
  specFileName = "spectrumData_" + nowtime_s + ".txt"
  specFile = open(specFileName,"w+")
#  specFile = open("spectrumData.txt","w+")  
  #mercury.mca.rois.roi0.count.value
##  for i in range (0,len(scanDataTable.mercury_mca_spectrum.values)):
##    for j in range (0,len(scanDataTable.mercury_mca_spectrum.values[i])):
#  specFile.write("From LSDC\n")
  specFile.write(str(len(scanDataTable.mercury_mca_rois_roi0_count)) + "\n")
  for i in range (0,len(scanDataTable.mercury_mca_rois_roi0_count)):
    specFile.write(str(scanDataTable.vdcm_e[i+1]) + " " + str(scanDataTable.mercury_mca_rois_roi0_count[i+1]))
    specFile.write("\n")
  specFile.close()
#  scanDataTable = get_table(scanData,["omega","cam_7_stats1_total"])  
  eScanResultObj = {}
  eScanResultObj["databrokerID"] = scanID
  eScanResultObj["sample_id"] = sampleID  
  eScanResultID = db_lib.addResultforRequest("eScanResult",energyScanRequest["uid"], daq_utils.owner,result_obj=eScanResultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline)
  eScanResult = db_lib.getResult(eScanResultID)
  print(scanDataTable)
  if (reqObj["runChooch"]):
    chooch_prefix = "choochData1_" + nowtime_s
#    chooch_prefix = "choochData1"    
    choochOutfileName = chooch_prefix+".efs"
    choochInputFileName = specFileName    
#    choochInputFileName = "spectrumData.txt"
#    choochInputFileName = "/nfs/skinner/temp/choochData1.raw"    
    comm_s = "chooch -e %s -o %s %s" % (scan_element, choochOutfileName,choochInputFileName)
#  comm_s = "chooch -e %s -o %s -p %s %s" % (scan_element,chooch_prefix+".efs",chooch_prefix+".ps",chooch_prefix+".raw")
    print(comm_s)
    choochInputData_x = []
    choochInputData_y = []
    infl = 0
    peak = 0
    f2prime_infl = 0
    fprime_infl = 0
    f2prime_peak = 0
    fprime_peak = 0
    choochInputFile = open(choochInputFileName,"r")
    for outputLine in choochInputFile.readlines():
      tokens = outputLine.split()
      if (len(tokens) == 2): #not a very elegant way to get past the first two lines that I don't need.    
        choochInputData_x.append(float(tokens[0]))
        choochInputData_y.append(float(tokens[1]))
    choochInputFile.close()
    for outputline in os.popen(comm_s).readlines():
      print(outputline)
      tokens = outputline.split()    
      if (len(tokens)>4):
        if (tokens[1] == "peak"):
          peak = float(tokens[3])
          fprime_peak = float(tokens[7])
          f2prime_peak = float(tokens[5])        
        elif (tokens[1] == "infl"):
          infl = float(tokens[3])
          fprime_infl = float(tokens[7])
          f2prime_infl = float(tokens[5])        
        else:
          pass
#  os.system("xmgrace spectrum.spec&")
#  os.system("gv.sh "+chooch_prefix+".ps") #kludged with a shell call to get around gv bug
#  os.system("ln -sf "+chooch_prefix+".ps latest_chooch_plot.ps")
    choochResultObj = {}
    choochResultObj["infl"] = infl
    choochResultObj["peak"] = peak
    choochResultObj["f2prime_infl"] = f2prime_infl
    choochResultObj["fprime_infl"] = fprime_infl
    choochResultObj["f2prime_peak"] = f2prime_peak
    choochResultObj["fprime_peak"] = fprime_peak
    choochResultObj["sample_id"] = sampleID
#    choochOutFile = open("/nfs/skinner/temp/choochData1.efs","r")
    if (not os.path.exists(choochOutfileName)):
      choochOutFile = open("/nfs/skinner/temp/choochData1.efs","r")
    else:
      choochOutFile = open(choochOutfileName,"r")    
    chooch_graph_x = []
    chooch_graph_y1 = []
    chooch_graph_y2 = []
    for outLine in choochOutFile.readlines():
      tokens = outLine.split()
      chooch_graph_x.append(float(tokens[0]))
      chooch_graph_y1.append(float(tokens[1]))
      chooch_graph_y2.append(float(tokens[2]))
    choochOutFile.close()
    choochResultObj["choochOutXAxis"] = chooch_graph_x
    choochResultObj["choochOutY1Axis"] = chooch_graph_y1
    choochResultObj["choochOutY2Axis"] = chooch_graph_y2
    choochResultObj["choochInXAxis"] = choochInputData_x
    choochResultObj["choochInYAxis"] = choochInputData_y  
#    plt.plot(chooch_graph_x,chooch_graph_y1)
#    plt.plot(chooch_graph_x,chooch_graph_y2)
#    plt.show()
#    print(choochResultObj)
    choochResultID = db_lib.addResultforRequest("choochResult",energyScanRequest["uid"], daq_utils.owner,result_obj=choochResultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline)
    choochResult = db_lib.getResult(choochResultID)
    set_field("choochResultFlag",choochResultID)

def vectorZebraScan(vecRequest):
  scannerType = db_lib.getBeamlineConfigParam(daq_utils.beamline,"scannerType")
  if (scannerType == "PI"):
    vectorZebraScanFine(vecRequest)
  else:
    vectorZebraScanNormal(vecRequest)

    
def vectorZebraScanFine(vecRequest):
  if not (daq_lib.setGovRobotDA()):
    return
  
  reqObj = vecRequest["request_obj"]
  file_prefix = str(reqObj["file_prefix"])
  data_directory_name = str(reqObj["directory"])
  file_number_start = reqObj["file_number_start"]
  
  sweep_start_angle = reqObj["sweep_start"]
  sweep_end_angle = reqObj["sweep_end"]
  imgWidth = reqObj["img_width"]
  expTime = reqObj["exposure_time"]
  numImages = int((sweep_end_angle - sweep_start_angle) / imgWidth)
  x_vec_start=reqObj["vectorParams"]["vecStart"]["x"]
  y_vec_start=reqObj["vectorParams"]["vecStart"]["y"]
  z_vec_start=reqObj["vectorParams"]["vecStart"]["z"]
  x_vec_end=reqObj["vectorParams"]["vecEnd"]["x"]
  y_vec_end=reqObj["vectorParams"]["vecEnd"]["y"]
  z_vec_end=reqObj["vectorParams"]["vecEnd"]["z"]

  xCenterCoarse = (x_vec_end+x_vec_start)/2.0
  yCenterCoarse = (y_vec_end+y_vec_start)/2.0
  zCenterCoarse = (z_vec_end+z_vec_start)/2.0
  mvaDescriptor("sampleX",xCenterCoarse,"sampleY",yCenterCoarse,"sampleZ",zCenterCoarse)
  xRelLen = x_vec_end-x_vec_start
  xRelStart = -xRelLen/2.0
  xRelEnd = -xRelStart
  yRelLen = y_vec_end-y_vec_start
  yRelStart = -yRelLen/2.0
  yRelEnd = -yRelStart
  zRelLen = z_vec_end-z_vec_start
  zRelStart = -zRelLen/2.0
  zRelEnd = -zRelStart

  det_lib.detector_set_num_triggers(numImages)
  det_lib.detector_set_trigger_mode(3)
  det_lib.detector_setImagesPerFile(1000)  
  detectorArm(sweep_start_angle,imgWidth,numImages,expTime,file_prefix,data_directory_name,file_number_start) #this waits

  zebraVecDaqSetup(sweep_start_angle,imgWidth,expTime,numImages,file_prefix,data_directory_name,file_number_start)  
  

  total_exposure_time=expTime*numImages
  trajPoints = int(total_exposure_time/.005)
  totalScanWidthX = xRelLen
  totalScanWidthY = yRelLen
  totalScanWidthZ = zRelLen
  xRelativeMoveFine = xRelStart
  yRelativeMoveFine = yRelStart
  zRelativeMoveFine = zRelStart
  mvaDescriptor("fineX",xRelativeMoveFine,"fineY",yRelativeMoveFine,"fineZ",zRelativeMoveFine)      
  beamline_support.setPvValFromDescriptor("fineXPoints",trajPoints)
  beamline_support.setPvValFromDescriptor("fineYPoints",trajPoints)
  beamline_support.setPvValFromDescriptor("fineZPoints",trajPoints)
  beamline_support.setPvValFromDescriptor("fineXAmp",totalScanWidthX)
  beamline_support.setPvValFromDescriptor("fineYAmp",totalScanWidthY)
  beamline_support.setPvValFromDescriptor("fineZAmp",totalScanWidthZ)
  beamline_support.setPvValFromDescriptor("fineXOffset",xRelativeMoveFine)
  beamline_support.setPvValFromDescriptor("fineYOffset",yRelativeMoveFine)
  beamline_support.setPvValFromDescriptor("fineZOffset",zRelativeMoveFine)
  beamline_support.setPvValFromDescriptor("fineXSendWave",1)
  time.sleep(0.1)    
  beamline_support.setPvValFromDescriptor("fineYSendWave",1)
  time.sleep(0.1)    
  beamline_support.setPvValFromDescriptor("fineZSendWave",1)
  time.sleep(0.1)    
  #move xyz fine mots to relative from centered raster
  beamline_support.setPvValFromDescriptor("fineXVecGo",1)
  time.sleep(0.1)            
  beamline_support.setPvValFromDescriptor("fineYVecGo",1)
  time.sleep(0.1)            
  beamline_support.setPvValFromDescriptor("fineZVecGo",1)    
  time.sleep(0.1)        
  beamline_support.setPvValFromDescriptor("zebraPulseMax",numImages) #moved this
  vectorSync()
  beamline_support.setPvValFromDescriptor("vectorStartOmega",sweep_start_angle)
  beamline_support.setPvValFromDescriptor("vectorEndOmega",sweep_end_angle)
  beamline_support.setPvValFromDescriptor("vectorframeExptime",expTime*1000.0)
  beamline_support.setPvValFromDescriptor("vectorNumFrames",numImages)
  beamline_support.setPvValFromDescriptor("vectorGo",1)
  vectorActiveWait()    
  vectorWait()
  zebraWait()
  zebraWaitDownload(numImages)
  time.sleep(2.0)
  det_lib.detector_stop_acquire()
  det_lib.detector_wait()
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)      
  
  #raster centered, now zero motors
  mvaDescriptor("fineX",0,"fineY",0,"fineZ",0)  
  
  if (lastOnSample()):  
    daq_lib.setGovRobotSA()    
    

def vectorZebraScanNormal(vecRequest): 
  reqObj = vecRequest["request_obj"]
  file_prefix = str(reqObj["file_prefix"])
  data_directory_name = str(reqObj["directory"])
  file_number_start = reqObj["file_number_start"]
  
  sweep_start_angle = reqObj["sweep_start"]
  sweep_end_angle = reqObj["sweep_end"]
  imgWidth = reqObj["img_width"]
  expTime = reqObj["exposure_time"]
  numImages = int((sweep_end_angle - sweep_start_angle) / imgWidth)
  x_vec_start=reqObj["vectorParams"]["vecStart"]["x"]
  y_vec_start=reqObj["vectorParams"]["vecStart"]["y"]
  z_vec_start=reqObj["vectorParams"]["vecStart"]["z"]
  x_vec_end=reqObj["vectorParams"]["vecEnd"]["x"]
  y_vec_end=reqObj["vectorParams"]["vecEnd"]["y"]
  z_vec_end=reqObj["vectorParams"]["vecEnd"]["z"]
  beamline_support.setPvValFromDescriptor("vectorStartOmega",sweep_start_angle)
#  beamline_support.setPvValFromDescriptor("vectorStepOmega",imgWidth)
  beamline_support.setPvValFromDescriptor("vectorEndOmega",sweep_end_angle)  
  beamline_support.setPvValFromDescriptor("vectorStartX",x_vec_start)
  beamline_support.setPvValFromDescriptor("vectorStartY",y_vec_start)  
  beamline_support.setPvValFromDescriptor("vectorStartZ",z_vec_start)  
  beamline_support.setPvValFromDescriptor("vectorEndX",x_vec_end)
  beamline_support.setPvValFromDescriptor("vectorEndY",y_vec_end)  
  beamline_support.setPvValFromDescriptor("vectorEndZ",z_vec_end)  
  beamline_support.setPvValFromDescriptor("vectorframeExptime",expTime*1000.0)
  beamline_support.setPvValFromDescriptor("vectorNumFrames",numImages)
#  beamline_support.setPvValFromDescriptor("vectorGo",1)
  scanWidth = float(numImages)*imgWidth
#  zebraVecDaq(sweep_start_angle,scanWidth,imgWidth,expTime,numImages,file_prefix,data_directory_name,file_number_start)
  zebraDaq(sweep_start_angle,scanWidth,imgWidth,expTime,file_prefix,data_directory_name,file_number_start)
  if (lastOnSample()):  
    daq_lib.setGovRobotSA()    
#  vectorWait()

def vectorZebraStepScan(vecRequest):
  if not (daq_lib.setGovRobotDA()):
    return
  
  reqObj = vecRequest["request_obj"]
  file_prefix = str(reqObj["file_prefix"])
  data_directory_name = str(reqObj["directory"])
  file_number_start = reqObj["file_number_start"]  
  sweep_start_angle = reqObj["sweep_start"]
  sweep_end_angle = reqObj["sweep_end"]
  imgWidth = reqObj["img_width"]
  expTime = reqObj["exposure_time"]
  numImages = int((sweep_end_angle - sweep_start_angle) / imgWidth)
  x_vec_start=reqObj["vectorParams"]["vecStart"]["x"]
  y_vec_start=reqObj["vectorParams"]["vecStart"]["y"]
  z_vec_start=reqObj["vectorParams"]["vecStart"]["z"]
  x_vec_end=reqObj["vectorParams"]["vecEnd"]["x"]
  y_vec_end=reqObj["vectorParams"]["vecEnd"]["y"]
  z_vec_end=reqObj["vectorParams"]["vecEnd"]["z"]
  x_vec = reqObj["vectorParams"]["x_vec"]
  y_vec = reqObj["vectorParams"]["y_vec"]
  z_vec = reqObj["vectorParams"]["z_vec"]  
  numVecSteps = reqObj["vectorParams"]["fpp"]
  scanWidthPerStep = (sweep_end_angle-sweep_start_angle)/float(numVecSteps)
  xvecStep = x_vec/float(numVecSteps)
  yvecStep = y_vec/float(numVecSteps)
  zvecStep = z_vec/float(numVecSteps)
  numImagesPerStep = numImages/float(numVecSteps)
  detector_dead_time = det_lib.detector_get_deadtime()
  exposureTimePerImage =  expTime - detector_dead_time  
  det_lib.detector_set_num_triggers(numImages)
  detector_set_period(expTime)
  detector_set_exposure_time(exposureTimePerImage)
  det_lib.detector_set_trigger_mode(3)
#  det_lib.detector_set_trigger_exposure(exposureTimePerImage)  
  det_lib.detector_setImagesPerFile(500)
  detectorArm(sweep_start_angle,imgWidth,numImages,expTime,file_prefix,data_directory_name,file_number_start) #this waits  
  for i in range (0,numVecSteps):
    beamline_support.setPvValFromDescriptor("vectorStartOmega",sweep_start_angle+(i*scanWidthPerStep))
    beamline_support.setPvValFromDescriptor("vectorEndOmega",sweep_end_angle+(i*scanWidthPerStep)+scanWidthPerStep)  
    beamline_support.setPvValFromDescriptor("vectorStartX",x_vec_start+(i*xvecStep)+(xvecStep/2.0))
    beamline_support.setPvValFromDescriptor("vectorStartY",y_vec_start+(i*yvecStep)+(yvecStep/2.0))  
    beamline_support.setPvValFromDescriptor("vectorStartZ",z_vec_start+(i*zvecStep)+(zvecStep/2.0))  
    beamline_support.setPvValFromDescriptor("vectorEndX",x_vec_start+(i*xvecStep)+(xvecStep/2.0))
    beamline_support.setPvValFromDescriptor("vectorEndY",y_vec_start+(i*yvecStep)+(yvecStep/2.0))  
    beamline_support.setPvValFromDescriptor("vectorEndZ",z_vec_start+(i*zvecStep)+(zvecStep/2.0))  
    beamline_support.setPvValFromDescriptor("vectorframeExptime",expTime*1000.0)
    beamline_support.setPvValFromDescriptor("vectorNumFrames",numImagesPerStep)
    zebraDaqNoDet(sweep_start_angle+(i*scanWidthPerStep),scanWidthPerStep,imgWidth,expTime,file_prefix,data_directory_name,file_number_start)
  if (lastOnSample()):  
    daq_lib.setGovRobotSA()    
  det_lib.detector_stop_acquire()
  det_lib.detector_wait()
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)      
  
  beamline_support.setPvValFromDescriptor("vectorBufferTime",3)      



def dna_execute_collection3(dna_startIgnore,dna_range,dna_number_of_images,dna_exptime,dna_directory,prefix,start_image_number,overlap,dna_run_num,charRequest):
  global collect_and_characterize_success,dna_have_strategy_results,dna_have_index_results,picture_taken
  global dna_strategy_exptime,dna_strategy_start,dna_strategy_range,dna_strategy_end,dna_strat_dist
  global screeningoutputid
  global ednaActiveFlag

  ednaActiveFlag = 1
  dna_start = charRequest["request_obj"]["sweep_start"]
  characterizationParams = charRequest["request_obj"]["characterizationParams"]
  dna_res = float(characterizationParams["aimed_resolution"])
  print("dna_res = " + str(dna_res))
  dna_filename_list = []
  print("number of images " + str(dna_number_of_images) + " overlap = " + str(overlap) + " dna_start " + str(dna_start) + " dna_range " + str(dna_range) + " prefix " + prefix + " start number " + str(start_image_number) + "\n")
  collect_and_characterize_success = 0
  dna_have_strategy_results = 0
  dna_have_index_results = 0  
  dg2rd = 3.14159265 / 180.0  
  if (daq_utils.detector_id == "ADSC-Q315"):
    det_radius = 157.5
  elif (daq_utils.detector_id == "ADSC-Q210"):
    det_radius = 105.0
  elif (daq_utils.detector_id == "PILATUS-6"):
    det_radius = 212.0
  else: #default Pilatus
    det_radius = 212.0
  theta_radians = 0.0
  wave = 12398.5/beamline_lib.get_mono_energy() #for now
  dx = det_radius/(tan(2.0*(asin(wave/(2.0*dna_res)))-theta_radians))
  print("distance = ",dx)
#skinner - could move distance and wave and scan axis here, leave wave alone for now
  print("skinner about to take reference images.")
  for i in range(0,int(dna_number_of_images)): # 7/17 no idea what this is
    print("skinner prefix7 = " + prefix[0:7] +  " " + str(start_image_number) + "\n")
    if (len(prefix)> 8):
      if ((prefix[0:7] == "postref") and (start_image_number == 1)):
        print("skinner postref bail\n")
        time.sleep(float(dna_number_of_images*float(dna_exptime)))        
        break
  #skinner roi - maybe I can measure and use that for dna_start so that first image is face on.
#    dna_start = motorPosFromDescriptor("omega")    
#    dna_start = daq_lib.get_field("datum_omega")    
    colstart = float(dna_start) + (i*(abs(overlap)+float(dna_range)))
    dna_prefix = "ref-"+prefix
    image_number = start_image_number+i
    dna_prefix_long = dna_directory+"/"+dna_prefix
    beamline_lib.mvaDescriptor("omega",float(colstart))
    charRequest["request_obj"]["sweep_start"] = colstart
    if (i == int(dna_number_of_images)-1): # a temporary crap kludge to keep the governor from SA when more images are needed.
      ednaActiveFlag = 0
    imagesAttempted = collect_detector_seq_hw(colstart,dna_range,dna_range,dna_exptime,dna_prefix,dna_directory,image_number,charRequest)
    seqNum = int(det_lib.detector_get_seqnum())
    hdfSampleDataPattern = dna_prefix_long
    filename = hdfSampleDataPattern + "_" + str(int(float(seqNum))) + "_master.h5"
    
    dna_filename_list.append(filename)
    picture_taken = 1
#                xml_from_file_list(flux,x_beamsize,y_beamsize,max_exptime_per_dc,aimed_completeness,file_list):
  edna_energy_ev = (12.3985/wave) * 1000.0
#  if (xbeam_size == 0.0 or ybeam_size == 0.0): #don't know where to get these from yet
  if (daq_utils.beamline == "fmx"):   # a kludge b/c edna wants a square beam, so where making a 4x4 micron beam be the sqrt(1*1.5) for x and y on fmx
    xbeam_size = .004
    ybeam_size = .004
  else:
    xbeam_size = .0089
    ybeam_size = .0089
  aimed_completeness = characterizationParams['aimed_completeness']
  aimed_multiplicity = characterizationParams['aimed_multiplicity']
  aimed_resolution = characterizationParams['aimed_resolution']
  aimed_ISig = characterizationParams['aimed_ISig']
  timeout_check = 0;
  while(not os.path.exists(dna_filename_list[len(dna_filename_list)-1])): #this waits for edna images
    timeout_check = timeout_check + 1
    time.sleep(1.0)
    if (timeout_check > 10):
      break
  flux = beamline_support.getPvValFromDescriptor("sampleFlux")    
#  if (daq_utils.beamline == "fmx"):                  
#    flux = beamline_support.getPvValFromDescriptor("flux")
#  else:
#    flux = beamline_support.getPvValFromDescriptor("flux") * beamline_support.getPvValFromDescriptor("transmissionRBV")


  cbfComm = db_lib.getBeamlineConfigParam(daq_utils.beamline,"cbfComm")
  node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode1")          
#  cbfDir = data_directory_name+"/cbf"
#  comm_s = "mkdir -p " + cbfDir
#  os.system(comm_s)
  cbfList = []
  print(dna_filename_list)
  for i in range (0,len(dna_filename_list)):
    hdfRowFilepattern = dna_filename_list[i]
#    print("filename = " + hdfRowFilepattern)
    CBF_conversion_pattern = dna_filename_list[i][0:len(dna_filename_list[i])-10]+"_"
#    print("cbf = " + CBF_conversion_pattern)
    cbfList.append(CBF_conversion_pattern+"000001.cbf")
    startIndex=1
    endIndex = 1
    comm_s = "ssh -q " + node + " \"" + cbfComm + " " + hdfRowFilepattern  + " " + str(startIndex) + ":" + str(endIndex) + " " + CBF_conversion_pattern + "\"&" 
    print(comm_s)
    os.system(comm_s)
  time.sleep(2.0)
  comm_s = "ssh -q xf17id2-ws10 \"source " + os.environ["PROJDIR"] + "wrappers/ednaWrap;cd " + dna_directory + ";" + os.environ["LSDCHOME"] + "/runEdna.py " + cbfList[0] + " " + cbfList[1] + " " + str(beamline_support.getPvValFromDescriptor("transmissionRBV")*100.0) + " " + str(flux) + " " + str(xbeam_size) + " " + str(ybeam_size) + " " + str(charRequest["uid"]) + " " + daq_utils.beamline + "\""    
#  comm_s = "ssh -q xf17id2-srv1 \"source " + os.environ["PROJDIR"] + "wrappers/ednaWrap;cd " + dna_directory + ";" + os.environ["LSDCHOME"] + "/runEdna.py " + dna_prefix_long + "_0001.h5 " + dna_prefix_long + "_0002.h5 " + str(aimed_ISig) + " " + str(flux) + " " + str(xbeam_size) + " " + str(ybeam_size) + " " + str(charRequest["uid"]) + "\""
  print(comm_s)
  os.system(comm_s)
  print("EDNA DONE\n")
#####  fEdnaLogFile = open(daq_lib.get_misc_dir_name() + "/edna.log", "r" )
  fEdnaLogFile = open(dna_directory+"/edna.log", "r" )
  ednaLogLines = fEdnaLogFile.readlines()
  fEdnaLogFile.close()
  collect_and_characterize_success = 0
  for outline in ednaLogLines:
    print(outline)
    if (outline.find("EdnaDir")!= -1):
      (param,dirname) = outline.split('=')
      strXMLFileName = dirname[0:len(dirname)-1]+"/ControlInterfacev1_2/Characterisation/ControlCharacterisationv1_3_dataOutput.xml"
#####    strXMLFileName = dirname[0:len(dirname)-1]+"/ControlInterfacev1_2/Characterisation/ControlCharacterisationv1_1_dataOutput.xml"
    if (outline.find("characterisation successful!")!= -1):
      collect_and_characterize_success = 1
  if (not collect_and_characterize_success):
    dna_comment =  "Characterize Failure"
    print(dna_comment)
#####  pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_comment)  
    return 0
  else:
    xsDataCharacterisation = XSDataResultCharacterisation.parseFile( strXMLFileName )
    xsDataIndexingResult = xsDataCharacterisation.getIndexingResult()
    xsDataIndexingSolutionSelected = xsDataIndexingResult.getSelectedSolution()
    xsDataStatisticsIndexing = xsDataIndexingSolutionSelected.getStatistics()
    numSpotsFound  = xsDataStatisticsIndexing.getSpotsTotal().getValue()
    numSpotsUsed  = xsDataStatisticsIndexing.getSpotsUsed().getValue()
    numSpotsRejected = numSpotsFound-numSpotsUsed
    beamShiftX = xsDataStatisticsIndexing.getBeamPositionShiftX().getValue()
    beamShiftY = xsDataStatisticsIndexing.getBeamPositionShiftY().getValue()
    spotDeviationR = xsDataStatisticsIndexing.getSpotDeviationPositional().getValue()
    try:
      spotDeviationTheta = xsDataStatisticsIndexing.getSpotDeviationAngular().getValue()
    except AttributeError:
      spotDeviationTheta = 0.0
    diffractionRings = 0 #for now, don't see this in xml except message string        
    reflections_used = 0 #for now
    reflections_used_in_indexing = 0 #for now
    rejectedReflections = 0 #for now
    xsDataOrientation = xsDataIndexingSolutionSelected.getOrientation()
    xsDataMatrixA = xsDataOrientation.getMatrixA()
    rawOrientationMatrix_a_x = xsDataMatrixA.getM11()
    rawOrientationMatrix_a_y = xsDataMatrixA.getM12()
    rawOrientationMatrix_a_z = xsDataMatrixA.getM13()
    rawOrientationMatrix_b_x = xsDataMatrixA.getM21()
    rawOrientationMatrix_b_y = xsDataMatrixA.getM22()
    rawOrientationMatrix_b_z = xsDataMatrixA.getM23()
    rawOrientationMatrix_c_x = xsDataMatrixA.getM31()
    rawOrientationMatrix_c_y = xsDataMatrixA.getM32()
    rawOrientationMatrix_c_z = xsDataMatrixA.getM33()
    xsDataCrystal = xsDataIndexingSolutionSelected.getCrystal()
    xsDataCell = xsDataCrystal.getCell()
    unitCell_alpha = xsDataCell.getAngle_alpha().getValue()
    unitCell_beta = xsDataCell.getAngle_beta().getValue()
    unitCell_gamma = xsDataCell.getAngle_gamma().getValue()
    unitCell_a = xsDataCell.getLength_a().getValue()
    unitCell_b = xsDataCell.getLength_b().getValue()
    unitCell_c = xsDataCell.getLength_c().getValue()
    mosaicity = xsDataCrystal.getMosaicity().getValue()
    xsSpaceGroup = xsDataCrystal.getSpaceGroup()
    spacegroup_name = xsSpaceGroup.getName().getValue()
    pointGroup = spacegroup_name #for now
    bravaisLattice = pointGroup #for now
    statusDescription = "ok" #for now
    try:
      spacegroup_number = xsSpaceGroup.getITNumber().getValue()
    except AttributeError:
      spacegroup_number = 0
    dna_comment =  "spacegroup = " + str(spacegroup_name) + " mosaicity = " + str(mosaicity) + " cell_a = " + str(unitCell_a) + " cell_b = " + str(unitCell_b) + " cell_c = " + str(unitCell_c) + " cell_alpha = " + str(unitCell_alpha) + " cell_beta = " + str(unitCell_beta) + " cell_gamma = " + str(unitCell_gamma) + " status = " + str(statusDescription)
###  print "\n\n skinner " + dna_comment + "\n" +str(daq_lib.sweep_seq_id) + "\n"
    print("\n\n skinner " + dna_comment + "\n") 
    xsStrategyResult = xsDataCharacterisation.getStrategyResult()
    resolutionObtained = -999
    if (xsStrategyResult != None):
      dna_have_strategy_results = 1
      xsCollectionPlan = xsStrategyResult.getCollectionPlan()
      xsStrategySummary = xsCollectionPlan[0].getStrategySummary()
      resolutionObtained = xsStrategySummary.getRankingResolution().getValue()
      xsCollectionStrategy = xsCollectionPlan[0].getCollectionStrategy()
      xsSubWedge = xsCollectionStrategy.getSubWedge()
      for i in range (0,len(xsSubWedge)):
        xsExperimentalCondition = xsSubWedge[i].getExperimentalCondition()
        xsGoniostat = xsExperimentalCondition.getGoniostat()
        xsDetector = xsExperimentalCondition.getDetector()
        xsBeam = xsExperimentalCondition.getBeam()
        newTrans_s = "%.2f" % (xsBeam.getTransmission().getValue()/100.0)
        newTrans = float(newTrans_s)
        print("\n new trans = " + str(newTrans) + "\n")
        dna_strategy_start = xsGoniostat.getRotationAxisStart().getValue()
        dna_strategy_start = dna_strategy_start-(dna_strategy_start%.1)
        dna_strategy_range = xsGoniostat.getOscillationWidth().getValue()
        dna_strategy_range = dna_strategy_range-(dna_strategy_range%.1)
        dna_strategy_end = xsGoniostat.getRotationAxisEnd().getValue()
        dna_strategy_end = (dna_strategy_end-(dna_strategy_end%.1)) + dna_strategy_range
        dna_strat_dist = xsDetector.getDistance().getValue()
        dna_strat_dist = dna_strat_dist-(dna_strat_dist%1)
        dna_strategy_exptime = xsBeam.getExposureTime().getValue()
#wtf?      dna_strategy_exptime = dna_strategy_exptime-(dna_strategy_exptime%.2)
    program = "edna-1.0" # for now
    dna_comment =  "spacegroup = " + str(spacegroup_name) + " mosaicity = " + str(mosaicity) + " resolutionHigh = " + str(resolutionObtained) + " cell_a = " + str(unitCell_a) + " cell_b = " + str(unitCell_b) + " cell_c = " + str(unitCell_c) + " cell_alpha = " + str(unitCell_alpha) + " cell_beta = " + str(unitCell_beta) + " cell_gamma = " + str(unitCell_gamma) + " status = " + str(statusDescription)
###  print "\n\n skinner " + dna_comment + "\n" +str(daq_lib.sweep_seq_id) + "\n"
    print("\n\n skinner " + dna_comment + "\n") 
    if (dna_have_strategy_results):
      dna_strat_comment = "\ndna Strategy results: Start=" + str(dna_strategy_start) + " End=" + str(dna_strategy_end) + " Width=" + str(dna_strategy_range) + " Time=" + str(dna_strategy_exptime) + " Dist=" + str(dna_strat_dist) + " Transmission= " + str(newTrans)
#    characterizationResult = {}
      characterizationResultObj = {}
#    characterizationResult["type"] = "characterizationStrategy"
 #   characterizationResult["timestamp"] = time.time()
      characterizationResultObj = {"strategy":{"start":dna_strategy_start,"end":dna_strategy_end,"width":dna_strategy_range,"exptime":dna_strategy_exptime,"detDist":dna_strat_dist,"transmission":newTrans}}
#    characterizationResult["resultObj"] = characterizationResultObj
      db_lib.addResultforRequest("characterizationStrategy",charRequest["uid"], daq_utils.owner,result_obj=characterizationResultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline)
      xsStrategyStatistics = xsCollectionPlan[0].getStatistics()
      xsStrategyResolutionBins = xsStrategyStatistics.getResolutionBin()
      now = time.time()
#  edna_isig_plot_filename = dirname[0:len(dirname)-1] + "/edna_isig_res_" + str(now) + ".txt"
      edna_isig_plot_filename = dirname[0:len(dirname)-1] + "/edna_isig_res.txt"
      isig_plot_file = open(edna_isig_plot_filename,"w")
      for i in range (0,len(xsStrategyResolutionBins)-1):
        i_over_sigma_bin = xsStrategyResolutionBins[i].getIOverSigma().getValue()
        maxResolution_bin = xsStrategyResolutionBins[i].getMaxResolution().getValue()
        print(str(maxResolution_bin) + " " + str(i_over_sigma_bin))
        isig_plot_file.write(str(maxResolution_bin) + " " + str(i_over_sigma_bin)+"\n")
      isig_plot_file.close()
    if (dna_have_strategy_results):
#    broadcast_output(dna_strat_comment)
      print(dna_strat_comment)      
  

  return 1

def setTrans(transmission): #where transmission = 0.0-1.0
  if (daq_utils.beamline == "fmx"):  
    if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"attenType") == "RI"):
      beamline_support.setPvValFromDescriptor("RIattenEnergySP",beamline_lib.motorPosFromDescriptor("energy"))
      beamline_support.setPvValFromDescriptor("RI_Atten_SP",transmission)      
      beamline_support.setPvValFromDescriptor("RI_Atten_SET",1)
      
    else:
      beamline_support.setPvValFromDescriptor("transmissionSet",transmission)
      beamline_support.setPvValFromDescriptor("transmissionGo",1)
      
  else:
    beamline_support.setPvValFromDescriptor("transmissionSet",transmission)
    beamline_support.setPvValFromDescriptor("transmissionGo",1)
  time.sleep(0.5)
  while (not beamline_support.getPvValFromDescriptor("transmissionDone")):
    time.sleep(0.1)
  
  
  

def setAttens(transmission): #where transmission = 0.0-1.0
  attenValList = []
  attenValList = attenCalc.RIfoils(beamline_lib.get_mono_energy(),transmission)
# attenValList = [0,1,0,1,0,1,0,1,0,1,0,1]
  for i in range (0,len(attenValList)):
    pvVal = attenValList[i]
    pvKeyName = "Atten%02d-%d" % (i+1,pvVal)    
    beamline_support.setPvValFromDescriptor(pvKeyName,1)
    print (pvKeyName)

def importSpreadsheet(fname):
  parseSheet.importSpreadsheet(fname,daq_utils.owner)


def zebraDaqPrep():

  if (1):
#  if (daq_utils.beamline == "fmx"):        
    beamline_support.setPvValFromDescriptor("zebraReset",1)
    time.sleep(2.0)      
  beamline_support.setPvValFromDescriptor("zebraTTlSel",31)

  beamline_support.setPvValFromDescriptor("zebraM1SetPosProc",1)
  beamline_support.setPvValFromDescriptor("zebraM2SetPosProc",1)
  beamline_support.setPvValFromDescriptor("zebraM3SetPosProc",1)
  beamline_support.setPvValFromDescriptor("zebraM4SetPosProc",1)
  beamline_support.setPvValFromDescriptor("zebraArmTrigSource",1)


def zebraArm():
  beamline_support.setPvValFromDescriptor("zebraArm",1)
  while(1):
    time.sleep(.1)
    if (beamline_support.getPvValFromDescriptor("zebraArmOut") == 1):
      break

def zebraWaitOld():
  while(1):
    time.sleep(.1)
    if (beamline_support.getPvValFromDescriptor("zebraDownloading") == 0):
      break

def zebraWait(timeoutCheck=True):
#  timeoutLimit = 5.0 #caused timeouts on long raster cell exposures
  timeoutLimit = 20.0
  downloadStart = time.time()  
  while(1):
    now = time.time()
    if (now > (downloadStart+timeoutLimit) and timeoutCheck):
      beamline_support.setPvValFromDescriptor("zebraReset",1)
      print("timeout in zebra wait!")
      daq_lib.gui_message("Timeout in Trigger Wait! Call Staff!!")
      break
    time.sleep(.1)
    if (beamline_support.getPvValFromDescriptor("zebraDownloading") == 0):
      break

def zebraWaitDownload(numsteps):

  timeoutLimit = 5.0  
  downloadStart = time.time()  
  while(1):
    now = time.time()
    if (now > (downloadStart+timeoutLimit)):
      beamline_support.setPvValFromDescriptor("zebraReset",1)
      print("timeout in zebra wait download!")      
      break
    time.sleep(.1)
    if (beamline_support.getPvValFromDescriptor("zebraDownloadCount") == numsteps):
      break
    
def loop_center_mask():
  os.system("cp $CONFIGDIR/bkgrnd.jpg .")
  mvrDescriptor("omega",90.0)
  daq_utils.take_crystal_picture(filename="findslice_0")
  comm_s = os.environ["PROJDIR"] + "/software/bin/c3d_search -p=$CONFIGDIR/find_loopslice.txt"
  os.system(comm_s)
  os.system("dos2unix res0.txt")
  os.system("echo \"\n\">>res0.txt")    
  c3d_out_file = open("res0.txt","r")
  line = c3d_out_file.readline()
  loop_line = c3d_out_file.readline()
  c3d_out_file.close()    
  loop_tokens = loop_line.split()
  print(loop_tokens)
  loop_found = int(loop_tokens[2])
#crash here if loop not found
  if (loop_found > 0):
    x = float(loop_tokens[9])
    y = float(loop_tokens[10])
    print("x = " + str(x) + " y = " + str(y))
    fovx = daq_utils.lowMagFOVx
    fovy = daq_utils.lowMagFOVy
    center_on_click(320.0,y,fovx,fovy,source="macro")
  mvrDescriptor("omega",-90.0)    

def getLoopSize():
  os.system("cp $CONFIGDIR/bkgrnd.jpg .")
  daq_utils.take_crystal_picture(filename="findsize_0")
  comm_s = os.environ["PROJDIR"] + "/software/bin/c3d_search -p=$CONFIGDIR/find_loopSize.txt"
  os.system(comm_s)
  os.system("dos2unix loopSizeOut0.txt")
  os.system("echo \"\n\">>loopSizeOut0.txt")    
  c3d_out_file = open("loopSizeOut0.txt","r")
  line = c3d_out_file.readline()
  loop_line = c3d_out_file.readline()
  c3d_out_file.close()    
  loop_tokens = loop_line.split()
  print(loop_tokens)
  loop_found = int(loop_tokens[2])
#crash here if loop not found
  if (loop_found > 0):
    v = float(loop_tokens[7])
    h = float(loop_tokens[8])
    print("v = " + str(v) + " h = " + str(h))
    return [v,h]
  return []

  
  

def loop_center_xrec():
  global face_on

  if (0):
#  if (daq_utils.beamline == "fmx"):                
    return loop_center_xrec_slow()
  daq_lib.abort_flag = 0    
  os.system("chmod 777 .")
  pic_prefix = "findloop"
#  zebraCamDaq(0,360,40,1,"xtalPic2","/GPFS/CENTRAL/XF17ID2/soares/Between_Users/skinner",1)
#  zebraCamDaq(0,360,40,.2,pic_prefix,os.getcwd(),0)
  zebraCamDaq(0,360,40,.4,pic_prefix,os.getcwd(),0)    
  comm_s = "xrec " + os.environ["CONFIGDIR"] + "/xrec_360_40Fast.txt xrec_result.txt"
  print(comm_s)
  os.system(comm_s)
  xrec_out_file = open("xrec_result.txt","r")
  target_angle = 0.0
  radius = 0
  x_centre = 0
  y_centre = 0
  reliability = 0
  for result_line in xrec_out_file.readlines():
    print(result_line)
    tokens = result_line.split()
    tag = tokens[0]
    val = tokens[1]
    if (tag == "TARGET_ANGLE"):
      target_angle = float(val )
    elif (tag == "RADIUS"):
      radius = float(val )
    elif (tag == "Y_CENTRE"):
      y_centre_xrec = float(val )
    elif (tag == "X_CENTRE"):
      x_centre_xrec = float(val )
    elif (tag == "RELIABILITY"):
      reliability = int(val )
    elif (tag == "FACE"):
      face_on = float(tokens[3])
  xrec_out_file.close()
  xrec_check_file = open("Xrec_check.txt","r")  
  check_result =  int(xrec_check_file.read(1))
  print("result = " + str(check_result))
  xrec_check_file.close()
  if (reliability < 70 or check_result == 0): #bail if xrec couldn't align loop
    return 0
  mvaDescriptor("omega",target_angle)
#  x_center = daq_utils.lowMagPixX/2
#  y_center = daq_utils.lowMagPixY/2
  x_center = beamline_support.getPvValFromDescriptor("lowMagCursorX")
  y_center = beamline_support.getPvValFromDescriptor("lowMagCursorY")
  
#  set_epics_pv("image_X_center","A",x_center)
#  set_epics_pv("image_Y_center","A",y_center)
  print("center on click " + str(x_center) + " " + str(y_center-radius))
  print("center on click " + str((x_center*2) - y_centre_xrec) + " " + str(x_centre_xrec))
#  fovx = daq_utils.highMagFOVx
#  fovy = daq_utils.highMagFOVy
  fovx = daq_utils.lowMagFOVx
  fovy = daq_utils.lowMagFOVy
  
  center_on_click(x_center,y_center-radius,fovx,fovy,source="macro")
  center_on_click((x_center*2) - y_centre_xrec,x_centre_xrec,fovx,fovy,source="macro")
#  center_on_click(y_centre_xrec,x_centre_xrec,source="macro")  
  mvaDescriptor("omega",face_on)
  #now try to get the loopshape starting from here
  return 1

  

def zebraCamDaq(angle_start,scanWidth,imgWidth,exposurePeriodPerImage,filePrefix,data_directory_name,file_number_start,scanEncoder=3): #scan encoder 0=x, 1=y,2=z,3=omega
#careful - there's total exposure time, exposure period, exposure time

#imgWidth will be something like 40 for xtalCenter
##?  det_lib.detector_setImagesPerFile(500)
  vectorSync()
  beamline_support.setPvValFromDescriptor("vectorExpose",0)  
  angle_end = angle_start+scanWidth
  numImages = int(round(scanWidth/imgWidth))
#  time.sleep(0.5)  
  beamline_support.setPvValFromDescriptor("vectorStartOmega",angle_start)
  beamline_support.setPvValFromDescriptor("vectorEndOmega",angle_end)
  beamline_support.setPvValFromDescriptor("vectorNumFrames",numImages)    
  beamline_support.setPvValFromDescriptor("vectorframeExptime",exposurePeriodPerImage*1000.0)
###  beamline_support.setPvValFromDescriptor("vectorGo",1)
  beamline_support.setPvValFromDescriptor("vectorHold",0)
###  vectorActiveWait()
###  vectorHoldWait()
  zebraDaqPrep()
  beamline_support.setPvValFromDescriptor("zebraEncoder",scanEncoder)
##  time.sleep(1.0)
  beamline_support.setPvValFromDescriptor("zebraDirection",0)  #direction 0 = positive
  beamline_support.setPvValFromDescriptor("zebraGateSelect",0)
  beamline_support.setPvValFromDescriptor("zebraGateStart",angle_start) #this will change for motors other than omega
  beamline_support.setPvValFromDescriptor("zebraGateWidth",imgWidth/2) #why divide by 2 here and not elsewhere?
  beamline_support.setPvValFromDescriptor("zebraGateStep",imgWidth)
#  beamline_support.setPvValFromDescriptor("zebraGateNumGates",1)
  beamline_support.setPvValFromDescriptor("zebraGateNumGates",numImages)  

  beamline_support.setPvValFromDescriptor("lowMagAcquire",0,wait=False)
  time.sleep(1.0) #this sleep definitely needed
  beamline_support.setPvValFromDescriptor("lowMagTrigMode",1)
  beamline_support.setPvValFromDescriptor("lowMagJpegNumImages",numImages)
  beamline_support.setPvValFromDescriptor("lowMagJpegFilePath",data_directory_name)
  beamline_support.setPvValFromDescriptor("lowMagJpegFileName",filePrefix)
  beamline_support.setPvValFromDescriptor("lowMagJpegFileNumber",1)
  beamline_support.setPvValFromDescriptor("lowMagJpegCapture",1,wait=False)
  beamline_support.setPvValFromDescriptor("lowMagAcquire",1,wait=False)
###  zebraArm()
  time.sleep(0.5)
  beamline_support.setPvValFromDescriptor("vectorGo",1)
  vectorActiveWait()    
  vectorWait()
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)      
  
##### needed???12/18  zebraWait()
  beamline_support.setPvValFromDescriptor("lowMagTrigMode",0)

def topViewSnap(filePrefix,data_directory_name,file_number_start,acquire=1): #if we don't need to stream, then this requires few steps
  os.system("mkdir -p " + data_directory_name)  
  os.system("chmod 777 " + data_directory_name)  
  beamline_support.setPvValFromDescriptor("topViewAcquire",0,wait=False)
  time.sleep(1.0) #this sleep definitely needed
  beamline_support.setPvValFromDescriptor("topViewTrigMode",5)
  beamline_support.setPvValFromDescriptor("topViewImMode",0)
  beamline_support.setPvValFromDescriptor("topViewDataType",0)    
#  beamline_support.setPvValFromDescriptor("lowMagJpegNumImages",numImages)
  beamline_support.setPvValFromDescriptor("topViewJpegFilePath",data_directory_name)
  beamline_support.setPvValFromDescriptor("topViewJpegFileName",filePrefix)
  beamline_support.setPvValFromDescriptor("topViewJpegFileNumber",file_number_start)
#  beamline_support.setPvValFromDescriptor("topViewJpegCapture",1,wait=False) # I don't know what this does.
  if (acquire):
    beamline_support.setPvValFromDescriptor("topViewAcquire",1)
    beamline_support.setPvValFromDescriptor("topViewWriteFile",1)
    beamline_support.setPvValFromDescriptor("topViewTrigMode",0)    
    beamline_support.setPvValFromDescriptor("topViewImMode",2)
    beamline_support.setPvValFromDescriptor("topViewDataType",1)
    beamline_support.setPvValFromDescriptor("topViewAcquire",1,wait=False)    

def topViewWrite():  
  beamline_support.setPvValFromDescriptor("topViewWriteFile",1)
  beamline_support.setPvValFromDescriptor("topViewTrigMode",0)    
  beamline_support.setPvValFromDescriptor("topViewImMode",2)
  beamline_support.setPvValFromDescriptor("topViewDataType",1)
  
  
  

def zebraDaq(angle_start,scanWidth,imgWidth,exposurePeriodPerImage,filePrefix,data_directory_name,file_number_start,scanEncoder=3,changeState=True): #scan encoder 0=x, 1=y,2=z,3=omega
#careful - there's total exposure time, exposure period, exposure time

  print("in Zebra Daq #1 " + str(time.time()))      
  det_lib.detector_setImagesPerFile(500)
  daq_lib.setRobotGovState("DA")  
  beamline_support.setPvValFromDescriptor("vectorExpose",1)

  if (imgWidth == 0):
    angle_end = angle_start
    numImages = scanWidth
  else:
    angle_end = angle_start+scanWidth    
    numImages = int(round(scanWidth/imgWidth))
  total_exposure_time = exposurePeriodPerImage*numImages
  if (total_exposure_time < 1.0):
    beamline_support.setPvValFromDescriptor("vectorBufferTime",1000)
  else:
    beamline_support.setPvValFromDescriptor("vectorBufferTime",3)
    pass
  print("in Zebra Daq #2 " + str(time.time()))        
  detector_set_exposure_time(exposurePeriodPerImage)  
  detector_set_period(exposurePeriodPerImage)
  detector_dead_time = detector_get_deadtime()
  exposureTimePerImage =  exposurePeriodPerImage - detector_dead_time  
  beamline_support.setPvValFromDescriptor("vectorNumFrames",numImages)  
  beamline_support.setPvValFromDescriptor("vectorStartOmega",angle_start)
  beamline_support.setPvValFromDescriptor("vectorEndOmega",angle_end)
  beamline_support.setPvValFromDescriptor("vectorframeExptime",exposurePeriodPerImage*1000.0)
  beamline_support.setPvValFromDescriptor("vectorHold",0)
  print("zebraDaqPrep " + str(time.time()))        
  zebraDaqPrep()
  print("done zebraDaqPrep " + str(time.time()))        
##  beamline_support.setPvValFromDescriptor("zebraEncoder",scanEncoder)
  time.sleep(1.0)
##  beamline_support.setPvValFromDescriptor("zebraDirection",0)  #direction 0 = positive
##  beamline_support.setPvValFromDescriptor("zebraGateSelect",0)
  beamline_support.setPvValFromDescriptor("zebraGateStart",angle_start) #this will change for motors other than omega
###  beamline_support.setPvValFromDescriptor("zebraGateWidth",0.9995*imgWidth)
  PW=(exposurePeriodPerImage-detector_dead_time)*1000.0
  PS=(exposurePeriodPerImage)*1000.0
  if (imgWidth != 0):  
    GW=scanWidth-(1.0-(PW/PS))*(imgWidth/2.0)
    beamline_support.setPvValFromDescriptor("zebraGateWidth",GW)
    beamline_support.setPvValFromDescriptor("zebraGateStep",scanWidth)
  beamline_support.setPvValFromDescriptor("zebraGateNumGates",1)
###  beamline_support.setPvValFromDescriptor("zebraGateNumGates",numImages)  
##  beamline_support.setPvValFromDescriptor("zebraPulseTriggerSource",1)
  beamline_support.setPvValFromDescriptor("zebraPulseStart",0)
###  beamline_support.setPvValFromDescriptor("zebraPulseWidth",(exposureTimePerImage-0.0005)*1000.0)
  beamline_support.setPvValFromDescriptor("zebraPulseWidth",PW)
  beamline_support.setPvValFromDescriptor("zebraPulseStep",PS)
###  beamline_support.setPvValFromDescriptor("zebraPulseStep",(exposurePeriodPerImage-0.0005)*1000.0)  
  beamline_support.setPvValFromDescriptor("zebraPulseDelay",((exposurePeriodPerImage)/2.0)*1000.0)
###  beamline_support.setPvValFromDescriptor("zebraPulseDelay",((exposurePeriodPerImage-0.0005)/2.0)*1000.0)    
  beamline_support.setPvValFromDescriptor("zebraPulseMax",numImages)
###  beamline_support.setPvValFromDescriptor("zebraPulseMax",1)    
##########  det_lib.detector_set_num_triggers(numImages)
  print("zebraDaq - setting and arming detector " + str(time.time()))      
  det_lib.detector_set_num_triggers(1)  
  det_lib.detector_set_trigger_mode(2)
  det_lib.detector_set_trigger_exposure(exposureTimePerImage)
  print("detector arm " + str(time.time()))        
  detectorArm(angle_start,imgWidth,numImages,exposurePeriodPerImage,filePrefix,data_directory_name,file_number_start) #this waits
  print("detector done arm, timed in zebraDaq " + str(time.time()))          
  startArm = time.time()
  if not (daq_lib.setGovRobotDA()):
    return
  endArm = time.time()
  armTime = endArm-startArm
  print("gov wait time = " + str(armTime) +"\n")
  
#  if not (daq_lib.setGovRobotDA()):
#    return
  print("vector Go " + str(time.time()))        
  beamline_support.setPvValFromDescriptor("vectorGo",1)
  vectorActiveWait()  
  vectorWait()
  zebraWait()
  print("vector Done " + str(time.time()))          
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)      
  
  if (lastOnSample() and changeState):
    if (0):
#    if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"queueCollect") == 1):      
      daq_lib.setGovRobotSE()
    else:
      daq_lib.setGovRobotSA_nowait()    
#    daq_lib.setGovRobotSA()
  print("stop det acquire")
  det_lib.detector_stop_acquire()
  det_lib.detector_wait()
  beamline_support.setPvValFromDescriptor("vectorBufferTime",3)
  print("zebraDaq Done " + str(time.time()))            


def zebraDaqNoDet(angle_start,scanWidth,imgWidth,exposurePeriodPerImage,filePrefix,data_directory_name,file_number_start,scanEncoder=3): #scan encoder 0=x, 1=y,2=z,3=omega
#careful - there's total exposure time, exposure period, exposure time


  beamline_support.setPvValFromDescriptor("vectorExpose",1)
  if (imgWidth == 0):
    angle_end = angle_start
    numImages = scanWidth
  else:
    angle_end = angle_start+scanWidth    
    numImages = int(round(scanWidth/imgWidth))
  total_exposure_time = exposurePeriodPerImage*numImages
  if (total_exposure_time < 1.0):
    beamline_support.setPvValFromDescriptor("vectorBufferTime",1000)
  else:
    beamline_support.setPvValFromDescriptor("vectorBufferTime",3)    
  detector_dead_time = detector_get_deadtime()
  exposureTimePerImage =  exposurePeriodPerImage - detector_dead_time  
  beamline_support.setPvValFromDescriptor("vectorNumFrames",numImages)  
  beamline_support.setPvValFromDescriptor("vectorStartOmega",angle_start)
  beamline_support.setPvValFromDescriptor("vectorEndOmega",angle_end)
  beamline_support.setPvValFromDescriptor("vectorframeExptime",exposurePeriodPerImage*1000.0)
  beamline_support.setPvValFromDescriptor("vectorHold",0)
  zebraDaqPrep()
  beamline_support.setPvValFromDescriptor("zebraEncoder",scanEncoder)
  time.sleep(1.0)
  beamline_support.setPvValFromDescriptor("zebraDirection",0)  #direction 0 = positive
  beamline_support.setPvValFromDescriptor("zebraGateSelect",0)
  beamline_support.setPvValFromDescriptor("zebraGateStart",angle_start) #this will change for motors other than omega
  if (imgWidth != 0):    
    beamline_support.setPvValFromDescriptor("zebraGateWidth",scanWidth)
    beamline_support.setPvValFromDescriptor("zebraGateStep",scanWidth+.01)
  beamline_support.setPvValFromDescriptor("zebraGateNumGates",1)
  beamline_support.setPvValFromDescriptor("zebraPulseTriggerSource",1)
  beamline_support.setPvValFromDescriptor("zebraPulseStart",0)
  beamline_support.setPvValFromDescriptor("zebraPulseWidth",(exposurePeriodPerImage-detector_dead_time)*1000.0)      
  beamline_support.setPvValFromDescriptor("zebraPulseStep",(exposurePeriodPerImage)*1000.0)
  beamline_support.setPvValFromDescriptor("zebraPulseDelay",((exposurePeriodPerImage)/2.0)*1000.0)
  beamline_support.setPvValFromDescriptor("zebraPulseMax",numImages)
  beamline_support.setPvValFromDescriptor("vectorGo",1)
  vectorActiveWait()  
  vectorWait()
  zebraWait()
  if (daq_utils.beamline == "amxz"):  
    beamline_support.setPvValFromDescriptor("zebraReset",1)      
  
  beamline_support.setPvValFromDescriptor("vectorBufferTime",3)      
  

def setAttenBCU():
  """setAttenBCU() : set attenuators to BCU (fmx only)"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"attenType","BCU")
  beamline_support.setPvValFromDescriptor("RI_Atten_SP",1.0)      
  beamline_support.setPvValFromDescriptor("RI_Atten_SET",1)
  daq_lib.gui_message("Attenuators set to BCU. Restart LSDC GUI!")  
  

def setAttenRI():
  """setAttenRI() : set attenuators to RI (fmx only)"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"attenType","RI")
  beamline_support.setPvValFromDescriptor("transmissionSet",1.0)
  beamline_support.setPvValFromDescriptor("transmissionGo",1)
  daq_lib.gui_message("Attenuators set to RI. Restart LSDC GUI!")    
  

  
def robotOn():
  """robotOn() : use the robot to mount samples"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"robot_online",1)


def robotOff():
  """robotOff() : fake mounting samples"""  
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"robot_online",0)


def zebraVecDaqSetup(angle_start,imgWidth,exposurePeriodPerImage,numImages,filePrefix,data_directory_name,file_number_start,scanEncoder=3): #scan encoder 0=x, 1=y,2=z,3=omega
#careful - there's total exposure time, exposure period, exposure time
#this is called in raster before the row processing loop

  beamline_support.setPvValFromDescriptor("vectorExpose",1)
  detector_dead_time = det_lib.detector_get_deadtime()
  total_exposure_time = exposurePeriodPerImage*numImages
  exposureTimePerImage =  exposurePeriodPerImage - detector_dead_time
  zebraDaqPrep()
  beamline_support.setPvValFromDescriptor("zebraEncoder",scanEncoder)
  time.sleep(1.0)
  beamline_support.setPvValFromDescriptor("zebraDirection",0)  #direction 0 = positive
  beamline_support.setPvValFromDescriptor("zebraGateSelect",0)
  beamline_support.setPvValFromDescriptor("zebraGateStart",angle_start) #this will change for motors other than omega
  if (imgWidth != 0):  
    beamline_support.setPvValFromDescriptor("zebraGateWidth",numImages*imgWidth)
    beamline_support.setPvValFromDescriptor("zebraGateStep",(numImages*imgWidth)+.001)
  beamline_support.setPvValFromDescriptor("zebraGateNumGates",1) #moved from loop
  beamline_support.setPvValFromDescriptor("zebraPulseTriggerSource",1)
  beamline_support.setPvValFromDescriptor("zebraPulseStart",0)
  beamline_support.setPvValFromDescriptor("zebraPulseWidth",(exposureTimePerImage-detector_dead_time)*1000.0)
###  beamline_support.setPvValFromDescriptor("zebraPulseWidth",(exposureTimePerImage-0.0005)*1000.0)      
  beamline_support.setPvValFromDescriptor("zebraPulseStep",(exposurePeriodPerImage)*1000.0)
###  beamline_support.setPvValFromDescriptor("zebraPulseStep",(exposurePeriodPerImage-0.0005)*1000.0)  
  beamline_support.setPvValFromDescriptor("zebraPulseDelay",((exposurePeriodPerImage)/2.0)*1000.0)
###  beamline_support.setPvValFromDescriptor("zebraPulseDelay",((exposurePeriodPerImage-0.0005)/2.0)*1000.0)    
  print("exp tim = " + str(exposureTimePerImage))  

###  beamline_support.setPvValFromDescriptor("zebraPulseMax",1) #moved this into the row loop
  beamline_support.setPvValFromDescriptor("vectorHold",0)  
##  zebraArm()
##  beamline_support.setPvValFromDescriptor("daqGo",1)
##  zebraWait()

  
def setProcRam():
  if (daq_utils.beamline == "amx"):
    db_lib.setBeamlineConfigParam("amx","spotNode1","xf17id2-srv1")
    db_lib.setBeamlineConfigParam("amx","spotNode2","xf17id2-srv1")
    db_lib.setBeamlineConfigParam("amx","cbfComm","/usr/local/MX-Soft/bin/eiger2cbfJohn")
    db_lib.setBeamlineConfigParam("amx","dialsComm","/usr/local/MX-Soft/Phenix/phenix-installer-dev-2666-intel-linux-2.6-x86_64-centos6/build/bin/dials.find_spots_client")        
  else:
    db_lib.setBeamlineConfigParam("fmx","spotNode1","xf17id2-ws3")
    db_lib.setBeamlineConfigParam("fmx","spotNode2","xf17id2-ws3")
    db_lib.setBeamlineConfigParam("fmx","cbfComm","/usr/local/MX-Soft/bin/eiger2cbfJohn")
    db_lib.setBeamlineConfigParam("fmx","dialsComm","/usr/local/MX-Soft/Phenix/phenix-installer-dev-2666-intel-linux-2.6-x86_64-centos6/build/bin/dials.find_spots_client")        
    

def setProcGPFS():
  if (daq_utils.beamline == "amx"):
    db_lib.setBeamlineConfigParam("amx","spotNode1","cpu-002")
    db_lib.setBeamlineConfigParam("amx","spotNode2","cpu-003")
    db_lib.setBeamlineConfigParam("amx","spotNode3","cpu-002")
    db_lib.setBeamlineConfigParam("amx","spotNode4","cpu-003")
    db_lib.setBeamlineConfigParam("amx","spotNode5","cpu-002")
    db_lib.setBeamlineConfigParam("amx","spotNode6","cpu-003")    
    db_lib.setBeamlineConfigParam("amx","cbfComm","/usr/local/crys-local/bin/eiger2cbf-linux")
    db_lib.setBeamlineConfigParam("amx","dialsComm","/usr/local/crys-local/phenix-1.12-2829/build/bin/dials.find_spots_client")        
    
  else:
    db_lib.setBeamlineConfigParam("fmx","spotNode1","cpu-007")
    db_lib.setBeamlineConfigParam("fmx","spotNode2","cpu-008")
    db_lib.setBeamlineConfigParam("fmx","spotNode3","cpu-009")
    db_lib.setBeamlineConfigParam("fmx","spotNode4","cpu-010")
    db_lib.setBeamlineConfigParam("fmx","spotNode5","cpu-008")
    db_lib.setBeamlineConfigParam("fmx","spotNode6","cpu-004")        
    db_lib.setBeamlineConfigParam("fmx","cbfComm","/usr/local/crys-local/bin/eiger2cbf-linux")
    db_lib.setBeamlineConfigParam("fmx","dialsComm","/usr/local/crys-prod/phenix-1.11rc2-2531/build/bin/dials.find_spots_client")
#    db_lib.setBeamlineConfigParam("fmx","dialsComm","/usr/local/crys-local/dials-v1-2-0/build/bin/dials.find_spots_client")            
    


def setFastDPNode(nodeName):
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"fastDPNode",nodeName)

def setDimpleNode(nodeName):
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"dimpleNode",nodeName)

def setDimpleCommand(commName):
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"dimpleComm",commName)
  

    
def lastOnSample():
  if (ednaActiveFlag == 1):
    return False
  r = db_lib.popNextRequest(daq_utils.beamline)
  if (r != {}):
    if (r["sample"] == db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample')['sampleID']):
      return False
  return True

def homePins():
  beamline_support.setPvValFromDescriptor("homePinY",1)
#  time.sleep(5)
  beamline_support.setPvValFromDescriptor("homePinZ",1)
  time.sleep(2)  
  beamline_support.setPvValFromDescriptor("syncPinY",1)
  beamline_support.setPvValFromDescriptor("syncPinZ",1)    
  
def restartEMBL():
#  os.system("ssh -q -X xf17id2-srv1 \"runEMBL>>/dev/null 2>&1\"")
  if (daq_utils.beamline == "amx"):      
    os.system("ssh -q -X xf17id2-srv1 \"runEMBL\"&")
  else:
    os.system("ssh -q -X xf17id1-srv1 \"runEMBL\"&")    


def queueCollectOn():
  """queueCollectOn() : allow for creating requests for samples that are not mounted"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"queueCollect",1)

def queueCollectOff():
  """queueCollectOff() : do not allow creating requests for samples that are not mounted"""  
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"queueCollect",0)

def guiLocal(): #monitor omega RBV
  """guiLocal() : show the readback of the Omega motor as it's moving. Can lead to lags when operating remotely with reduced bandwidth."""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"omegaMonitorPV","RBV")

def guiRemote(): #monitor omega VAL
  """guiRemote() : show the setpoint of the Omega motor, instead of the constant readback. This can be used to reduce video lags when operating remotely with reduced bandwidth"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"omegaMonitorPV","VAL")

def spotNodes(*args):
  """spotNodes(*args) : Set the dials spotfinding nodes. You must give 8 nodes. Example: spotNodes(4,5,7,8,12,13,14,15)"""
  if (len(args) != 8):
    print("C'mon, I need 8 nodes. No change. Try again.")
  else:
    for i in range (0,len(args)):
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"spotNode"+str(i+1),"cpu-%03d" % args[i])

def fastDPNodes(*args):
  """fastDPNodes(*args) : Set the fastDP nodes. You must give 4 nodes. Example: fastDPNodes(4,5,7,8)"""  
  if (len(args) != 4):
    print("C'mon, I need 4 nodes. No change. Try again.")
  else:
    for i in range (0,len(args)):
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"fastDPNode"+str(i+1),"cpu-%03d" % args[i])

def setVisitName(vname):
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"visitName",str(vname))

def setScannerType(s_type): #either "PI" or "Normal"
  """setScannerType(s_type): #either PI or Normal"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"scannerType",str(s_type))

def getVisitName(beamline):
  return db_lib.getBeamlineConfigParam(beamline,"visitName")


def setWarmupInterval(interval):
  """setWarmupInterval(interval) : set the number of mounts between automatic robot warmups"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"robotWarmupInterval",int(interval))

def setAutoRasterDelay(interval):
  """setAutoRasterDelay(delayTime) : set delay time before autoRaster in Q-collect"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"autoRasterDelay",float(interval))
  
def procOn():
  """procOn() : Turns on raster heatmap generation"""  
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterProcessFlag",1)

def procOff():
  """procOff() : Turns off raster heatmap generation"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterProcessFlag",0)

def backoffDetector():
  if (daq_utils.beamline == "amx"):
    beamline_lib.mvaDescriptor("detectorDist",700.0)
  else:
    beamline_lib.mvaDescriptor("detectorDist",1000.0)

def disableMount():
  """disableMount() : turn off robot mounting. Usually done in an error situation where we want staff intervention before resuming."""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"mountEnabled",0)

def enableMount():
  """enableMount() : allow robot mounting"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"mountEnabled",1)

def set_beamsize(sizeV, sizeH):
  if (sizeV == 'V0'):
    beamline_support.setPvValFromDescriptor("CRL_V2A_OUT",1)
    beamline_support.setPvValFromDescriptor("CRL_V1A_OUT",1)
    beamline_support.setPvValFromDescriptor("CRL_V1B_OUT",1)
    beamline_support.setPvValFromDescriptor("CRL_VS_OUT",1)        
  elif (sizeV == 'V1'):
    beamline_support.setPvValFromDescriptor("CRL_VS_IN",1)    
    beamline_support.setPvValFromDescriptor("CRL_V2A_OUT",1)
    beamline_support.setPvValFromDescriptor("CRL_V1A_IN",1)
    beamline_support.setPvValFromDescriptor("CRL_V1B_OUT",1)
  else:
    print("Error: Vertical size argument has to be \'V0\' or  \'V1\'")
  if (sizeH == 'H0'):  
    beamline_support.setPvValFromDescriptor("CRL_H4A_OUT",1)
    beamline_support.setPvValFromDescriptor("CRL_H2A_OUT",1)
    beamline_support.setPvValFromDescriptor("CRL_H1A_OUT",1)
    beamline_support.setPvValFromDescriptor("CRL_H1B_OUT",1)
  elif (sizeH == 'H1'):  
    beamline_support.setPvValFromDescriptor("CRL_H4A_OUT",1)
    beamline_support.setPvValFromDescriptor("CRL_H2A_IN",1)
    beamline_support.setPvValFromDescriptor("CRL_H1A_IN",1)
    beamline_support.setPvValFromDescriptor("CRL_H1B_IN",1)
  else:
    print("Error: Horizontal size argument has to be \'H0\' or  \'H1\'")
  if (sizeV == 'V0' and sizeH == 'H0'):
    set_field("size_mode",0)
  elif (sizeV == 'V0' and sizeH == 'H1'):
    set_field("size_mode",1)
  elif (sizeV == 'V1' and sizeH == 'H0'):
    set_field("size_mode",2)
  elif (sizeV == 'V1' and sizeH == 'H1'):
    set_field("size_mode",3)
  else:
    pass
  

  
def vertRasterOn():
  """vertRasterOn() : raster vertically when rasters are taller than they are wide"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"vertRasterOn",1)

def vertRasterOff():
  """vertRasterOff() : only raster vertically for single-column (line) rasters"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"vertRasterOn",0)

def newVisit():
  """newVisit() : Trick LSDC into creating a new visit on the next request creation"""
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"proposal",987654) #a kludge to cause the next collection to generate a new visit


def logMe():
  """logMe() : Edwin asked for this"""
  print(time.ctime())
  print("governor: " + str(beamline_support.getPvValFromDescriptor("governorMessage")))
  print("SampleX: " + str(motorPosFromDescriptor("sampleX")) + " SampleY: " + str(motorPosFromDescriptor("sampleY")) + "SampleZ: " + str(motorPosFromDescriptor("sampleZ")))
  print("CryoXY: " + str(motorPosFromDescriptor("cryoXY")))
  print("Gripper Temp: " + str(beamline_support.getPvValFromDescriptor("gripTemp")))
  print("Dewar Position: " + str(motorPosFromDescriptor("dewarRot")))
#  print("Gripper Status: " + str(beamline_support.getPvValFromDescriptor("gripTemp")))  
  print("Force Torque Sensor Status: " + str(beamline_support.getPvValFromDescriptor("robotFTSensorStat")))
  print("Force Torque X " + str(beamline_support.getPvValFromDescriptor("robotForceX")) + " Y: " + str(beamline_support.getPvValFromDescriptor("robotForceY")) + " Z: " + str(beamline_support.getPvValFromDescriptor("robotForceZ")))
  

def setSlit1X(mval):
  mvaDescriptor("slit1XGap",float(mval))

def setSlit1Y(mval):
  mvaDescriptor("slit1YGap",float(mval))
  
def emptyQueue():
  """emptyQueue() : Intended to recover from corrupted requests when GUI won't start"""
  reqList = list(db_lib.getQueue(daq_utils.beamline))
  for i in range (0,len(reqList)):
    db_lib.deleteRequest(reqList[i]["uid"])

def addPersonToProposal(personLogin,propNum):
  """addPersonToProposal(personLogin,propNum) : add person to ISPyB proposal - personLogin must be quoted, proposal number is a number (not quoted)"""    
  ispybLib.addPersonToProposal(personLogin,propNum)

def createPerson(firstName,lastName,loginName):
  """createPerson(firstName,lastName,loginName) : create person for ISPyB - be sure to quote all arguments"""  
  ispybLib.createPerson(firstName,lastName,loginName)

def createProposal(propNum,PI_login="boaty"):
  """createProposal(propNum,PI_login) : create proposal for ISPyB - be sure to quote the login name, Proposal number is a number (not quoted)"""    
  ispybLib.createProposal(propNum,PI_login)
  

def topViewCheckOn():
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"topViewCheck",1)

def anneal(annealTime):
  robotGovState = (beamline_support.getPvValFromDescriptor("robotSaActive") or beamline_support.getPvValFromDescriptor("humanSaActive"))
  if (robotGovState):
#        beamline_support.setPvValFromDescriptor("robotGovActive",0)          
    beamline_support.setPvValFromDescriptor("annealIn",1)
    while (beamline_support.getPvValFromDescriptor("annealStatus") != 1):
      time.sleep(0.01)      
    time.sleep(float(annealTime))
    beamline_support.setPvValFromDescriptor("annealIn",0)
#        beamline_support.setPvValFromDescriptor("robotGovActive",1)          
  else:
    daq_lib.gui_message("Anneal only in SA state!!")    

  
def topViewCheckOff():
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"topViewCheck",0)

def fmx_expTime_to_10MGy(beamsizeV = 3.0, beamsizeH = 5.0, vectorL = 100, energy = 12.7, wedge = 180, flux = 1e12, verbose = True):
  if (not os.path.exists("2vb1.pdb")):
    os.system("ln -s $CONFIGDIR/2vb1.pdb .")
    os.system("mkdir rd3d")
  raddoseLib.fmx_expTime_to_10MGy(beamsizeV = beamsizeV, beamsizeH = beamsizeH, vectorL = vectorL, energy = energy, wedge = wedge, flux = flux, verbose = verbose)
#  why doesn't this work? raddoseLib.fmx_expTime_to_10MGy(beamsizeV, beamsizeH, vectorL, energy, wedge, flux, verbose)

def unlockGUI():
  """unlockGUI() : unlock lsdcGui"""
  
  daq_lib.unlockGUI()

def lockGUI():
  """lockGUI() : lock lsdcGui"""
  
  daq_lib.lockGUI()
  
def beamCheckOn():
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"beamCheck",1)

def beamCheckOff():
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"beamCheck",0)

def HePathOff():
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"HePath",0)

def HePathOn():
  db_lib.setBeamlineConfigParam(daq_utils.beamline,"HePath",1)
  

def lsdcHelp():
  print(setGridRasterParams.__doc__)
  print(printGridRasterParams.__doc__)                   
  print(robotOn.__doc__)
  print(robotOff.__doc__)
  print(procOn.__doc__)
  print(procOff.__doc__)
  print(queueCollectOn.__doc__)
  print(queueCollectOff.__doc__)
  print(spotNodes.__doc__)
  print(fastDPNodes.__doc__)
  print(setWarmupInterval.__doc__)
  print(setAutoRasterDelay.__doc__)  
  print(disableMount.__doc__)
  print(enableMount.__doc__)
  print(vertRasterOn.__doc__)
  print(vertRasterOff.__doc__)
  print(newVisit.__doc__)
  print(emptyQueue.__doc__)
  print(logMe.__doc__)
  print(addPersonToProposal.__doc__)
  print(createPerson.__doc__)
  print(createProposal.__doc__)
  print(setAttenBCU.__doc__)
  print(setAttenRI.__doc__)
  print(unlockGUI.__doc__)
  print(collectSpec.__doc__)
  print(setScannerType.__doc__)            
  print("recoverRobot()")
  print("setFastDPNode(nodeName)")
  print("setDimpleNode(nodeName)")
  print("setDimpleCommand(commandString)")
  print("beamCheckOn()")
  print("beamCheckOff()")
  print("HePathOn()")
  print("HePathOff()")  
  print("homePins()")
  
  



  
  