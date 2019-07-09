import tensorflow as tf
from align import detect_face
import facenet
import cv2
import imutils
import numpy as np
import argparse
import csv
import time
import mysql.connector


parser = argparse.ArgumentParser()
parser.add_argument("--img", type = str, required=True)
args = parser.parse_args()
print "FACE DETECTION \n----------------------------------------------------------------"
# some constants kept as default from facenet
minsize = 20
threshold = [0.6, 0.7, 0.7]
factor = 0.709
margin = 44
input_image_size = 160

sess = tf.Session()
# read pnet, rnet, onet models from align directory and files are det1.npy, det2.npy, det3.npy
pnet, rnet, onet = detect_face.create_mtcnn(sess, 'align')

# read 20170512-110547 model file downloaded from https://drive.google.com/file/d/0B5MzpY9kBtDVZ2RpVDYwWmxoSUk
facenet.load_model("20170512-110547/20170512-110547.pb")

# Get input and output tensors
images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
embedding_size = embeddings.get_shape()[1]

def getFace(img):
    faces = []
    img_size = np.asarray(img.shape)[0:2]
    bounding_boxes, points = detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold, factor)
    if not len(bounding_boxes) == 0:
        for face in bounding_boxes:
            if face[4] > 0.50:
                det = np.squeeze(face[0:4])
                bb = np.zeros(4, dtype=np.int32)
                bb[0] = np.maximum(det[0] - margin / 2, 0)
                bb[1] = np.maximum(det[1] - margin / 2, 0)
                bb[2] = np.minimum(det[2] + margin / 2, img_size[1])
                bb[3] = np.minimum(det[3] + margin / 2, img_size[0])
                cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]
                resized = cv2.resize(cropped, (input_image_size,input_image_size),interpolation=cv2.INTER_CUBIC)
                prewhitened = facenet.prewhiten(resized)
                faces.append({'face':resized,'rect':[bb[0],bb[1],bb[2],bb[3]],'embedding':getEmbedding(prewhitened)})
    return faces

def getEmbedding(resized):
    reshaped = resized.reshape(-1,input_image_size,input_image_size,3)
    feed_dict = {images_placeholder: reshaped, phase_train_placeholder: False}
    # print(feed_dict)
    embedding = sess.run(embeddings, feed_dict=feed_dict)
    return embedding

def write_to_file(d):
    with open('data.csv','a') as f:
        for j in d:
            p = [j]
            j = p + list(d[j])
            print len(j)
            wrt = csv.writer(f)
            wrt.writerows([j])
        f.close
    print "Finished storing"


def store_to_database(myId,name,Roll,mail):
    mydb = mysql.connector.connect(host='localhost',user="byte-rider",passwd='23155878',database='reFace')     
    mycursor = mydb.cursor()
    val = (myId,name,Roll,mail)
    mycursor.execute("INSERT INTO perData(myID,Name,Roll,email) VALUES(%s,%s,%s,%s)",val)
    print "Came here"
    mydb.commit()
    mydb.close()
    print 'Data Stored Successfully'

######################################################################################




img = cv2.imread(args.img)
img = imutils.resize(img,width=1000)
faces = getFace(img)
d = {}
for face in faces:
    y = raw_input("Do you want to store (Y/N) : ")
    if(y == 'Y' or y == 'y'):
        na = raw_input("Please give your name : ")
        iD = raw_input("Please give your Roll Number : ")
        mal = raw_input("Please provide your email ID : ")
        myId = int(time.time())
        #also create a user in the database
        d[myId] = face['embedding'][0]
        store_to_database(myId,na,iD,mal)
        print iD,d[myId]
write_to_file(d)
   



cv2.waitKey(0)
cv2.destroyAllWindows()
