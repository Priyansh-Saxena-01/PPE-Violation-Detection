'''
A modified version of hubconf.py  

Modifications:
1. Added a function to detect PPE violation in a video file or video stream
2. Added a function to send email alert with attached image

'''

import threading
import time
import cv2
import torch
import numpy as np

from models.experimental import attempt_load
from utils.general import check_img_size, non_max_suppression, scale_coords, letterbox
from utils.plots import plot_one_box
from utils.torch_utils import select_device

#send mail alert
from send_mail import prepare_and_send_email

#Global Variabless
is_email_allowed = False #when user checks the email checkbox, this variable will be set to True
send_next_email = True #We have to wait for 10 minutes before sending another email
# NEXT TWO STATEMENTS NEED TO BE CHANGED TO MATCH YOUR SETUP!!!
#set the default email sender and recipient 
email_sender = 'support.ai@giindia.com'
email_recipient = 'support.ai@giindia.com'
# detections_summary will be used to store the detections summary report
detections_summary = ''

classes_to_filter = None  #You can give list of classes to filter by name, Be happy you don't have to put class number. ['train','person' ]

# ----------------VERY IMPORTANT - CONFIGURATION PARAMETERS----------------
# a dictionary to store options for inference
opt  = {
    "weights": "best.pt", # Path to weights file default weights are for nano model
    "yaml"   : "data/custom_data.yaml",
    "img-size": 640, # default image size
    "conf-thres": 0.25, # confidence threshold for inference.
    "iou-thres" : 0.45, # NMS IoU threshold for inference.
    "device" : 'cpu',  # device to run our model i.e. 0 or 0,1,2,3 or cpu
    "classes" : classes_to_filter  # list of classes to filter or None
}


def violation_alert_generator(im0, subject='PPE Violation Detected', message_text='A PPE violation is detected'):
    '''This function will send an email with attached alert image and then wait for 10 minutes before sending another email
    
    Parameters:
      im0 (numpy.ndarray): The image to be attached in the email
      subject (str): The subject of the email
      message_text (str): The message text of the email

    Returns:
      None
    '''
    global send_next_email, email_recipient
    send_next_email = False #set flag to False so that another email is not sent
    print('Sending email alert to ', email_recipient)
    prepare_and_send_email(email_sender, email_recipient, subject, message_text, im0)
    # wait for 10 minutes before sending another email
    time.sleep(600)
    send_next_email = True


def video_detection(conf_=0.25, frames_buffer=[]):
  '''This function will detect violations in a video file or a live stream 

  Parameters:
    conf_ (float): Confidence threshold for inference
    frames_buffer (list): A list of frames to be processed

  Returns:
    None
  '''    
  # Declare global variables to be used in this function
  global send_next_email
  global is_email_allowed
  global email_recipient
  global detections_summary

  violation_frames = 0 # Number of frames with violation
 
  #pop first frame from frames_buffer to get the first frame
  # We encountered a bug in which the first frame was not getting properly processed so we are popping it out
  while True:
    if len(frames_buffer) > 0:
      _ = frames_buffer.pop(0)
      break

  # empty the GPU cache to free up memory for inference
  torch.cuda.empty_cache()
  # Initializing model and setting it for inference
  # no_grad() is used to speed up inference by disabling gradient calculation
  with torch.no_grad():
    weights, imgsz = opt['weights'], opt['img-size']
    device = select_device(opt['device'])
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size
    
    # if device is not cpu i.e, it is gpu, convert model to half precision
    half = device.type != 'cpu'
    if half:
      model.half() # convert model to FP16

    # find names of classes in the model
    names = model.module.names if hasattr(model, 'module') else model.names
    
    # Run inference one time to initialize the model on a tensor of zeros
    if device.type != 'cpu':
      model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))

    # classes to filter out from the detections
    # We will not be filtering out any class and use all four - safe, unsafe, no-helmet and no-jacket
    classes = None
    if opt['classes']:
      classes = []
      for class_name in opt['classes']:
        classes.append(opt['classes'].index(class_name))

    try:
      # Contously run inference on the frames in the buffer
      while True:
        # if the frames_buffer is not empty, pop the first frame from the buffer
        if len(frames_buffer) > 0:
          #pop first frame from frames_buffer 
          img0 = frames_buffer.pop(0)
          # if the popped frame is None, continue to the next iteration
          if img0 is None:
            continue
          #clear the buffer if it has more than 10 frames to avoid memory overflow
          if len(frames_buffer) >= 10:
            frames_buffer.clear() 
        else:
          # buffer is empty, nothing to do
          continue

        img = letterbox(img0, imgsz, stride=stride)[0] # resize and pad image
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB
        img = np.ascontiguousarray(img) # convert to contiguous array
        img = torch.from_numpy(img).to(device) # place the image on the device (cpu or gpu)
        img = img.half() if half else img.float()  # convert to FP16 if device is gpu
        img /= 255.0  # Normalize to [0, 1] range
        
        # add a dimension to the image if it is a single image
        if img.ndimension() == 3:
          img = img.unsqueeze(0)

        # Do the Inference (Prediction)
        pred = model(img, augment= False)[0]

        # Do the non-maximum suppression to remove the redundant bounding boxes
        total_detections = 0
        pred = non_max_suppression(pred, conf_, opt['iou-thres'], classes= classes, agnostic= False)
        
        # Process all the predictions and draw the bounding boxes
        for i, det in enumerate(pred):
          classwise_summary = ''

          # if there is a detection
          if len(det):
            # Rescale boxes from img_size (predicted image) to im0 (actual image) size and round the coordinates
            det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()

            # Consider that the frame is safe
            unsafe = False # Flag to indicate if the frame is unsafe

            # Write the detections to the frame
            for c in det[:, -1].unique():
              n = (det[:, -1] == c).sum()  # detections per class
              total_detections += int(n)
              c = int(c)

              #we need to make sure at there is violation in atleast 5 continous frames
              # Check if the frame is unsafe
              # c == 0 means no helmet, c == 1 means no jacket, c == 3 means unsafe
              # c == 2 means safe
              if unsafe == False and (c == 0 or c == 1 or c == 3) and n > 0:
                unsafe = True
              
              # add the number of detections per class to the string
              classwise_summary += f"{n} {names[c]}{'s' * (n > 1)}, "  # add to string

            #code to send email on five continous violations
            if unsafe == True and is_email_allowed == True:
              violation_frames += 1
              if violation_frames >= 5 and send_next_email == True:
              # reset the violation_frames since violation is detected
                violation_frames = 0
                # create a thread for sending email
                t = threading.Thread(target=violation_alert_generator, args=(img0,))
                t.start()
            elif unsafe == False:
              # reset the number of violation_frames if current frame is safe
              violation_frames = 0

            # Store the detections summary in a string
            #get current time in hh:mm:ss format
            current_time = time.strftime("%H:%M:%S", time.localtime())
            detections_summary += f"\n {current_time}\n Total Detections: {total_detections}\n Detections per class: {classwise_summary}\n###########\n"
            
            # Plot the bounding boxes on the frame
            for *xyxy, conf, cls in det:
              label = f'{names[int(cls)]} {conf:.2f}'
              if label.startswith('safe'):
                color = (0,255,0) #Green in BGR
              else:
                color = (0,0,255) #Red in BGR

              plot_one_box(xyxy, img0, label=label, color=color, line_thickness=3)

          yield img0, total_detections

    except Exception as e:
      print(e)
    
