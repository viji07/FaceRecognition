import cv2 as cv
import math
import time
import argparse
from fer import FER

def getFaceBox(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)
    net.setInput(blob)
    detections = net.forward()
    bboxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            bboxes.append([x1, y1, x2, y2])
            cv.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight/150)), 8)
    return frameOpencvDnn, bboxes

parser = argparse.ArgumentParser()
parser.add_argument('--input')
args = parser.parse_args()

fPro = "opencv_face_detector.pbtxt"
fModel = "opencv_face_detector_uint8.pb"
aPro = "age_deploy.prototxt"
aModel = "age_net.caffemodel"
gPro = "gender_deploy.prototxt"
gModel = "gender_net.caffemodel"

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = ['(0-5)', '(6-10)', '(11-15)', '(16-20)', '(21-25)', '(26-30)', '(31-35)', '(36-40)','(41-50)','(51-55)','(56-60)','(61-65)','(66-70)','(71-75)','(76-80)','(81-85)','(86-90)','(91-95)','(96-100)']
genderList = ['Male', 'Female']

aNet = cv.dnn.readNet(aModel, aPro)
gNet = cv.dnn.readNet(gModel, gPro)
fNet = cv.dnn.readNet(fModel, fPro)

cap = cv.VideoCapture(args.input if args.input else 0)
padding = 20
while cv.waitKey(1) < 0:
    t = time.time()
    hasFrame, frame = cap.read()
    if not hasFrame:
        cv.waitKey()
        break

    frameFace, bboxes = getFaceBox(fNet, frame)
    if not bboxes:
        print("No face Detected, Checking next frame")
        continue
    
    for bbox in bboxes:
            face = frame[max(0,bbox[1]-padding):min(bbox[3]+padding,frame.shape[0]-1),max(0,bbox[0]-padding):min(bbox[2]+padding, frame.shape[1]-1)]
            blob = cv.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            gNet.setInput(blob)
            genderPreds = gNet.forward()
            gender = genderList[genderPreds[0].argmax()]
            print("Gender : {}, conf = {:.3f}".format(gender, genderPreds[0].max()))
            aNet.setInput(blob)
            agePreds = aNet.forward()
            age = ageList[agePreds[0].argmax()]
            print("Age : {}, conf = {:.3f}".format(age, agePreds[0].max()))
            detector = FER()
            emotion=detector.top_emotion(face)
            print(emotion[0])
            label = "{},{},{}".format(gender, age,emotion[0])
            cv.putText(frameFace, label, (bbox[0], bbox[1]-10), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv.LINE_AA)
            cv.imshow("Prediction", frameFace)
    print("time : {:.3f}".format(time.time() - t))
    