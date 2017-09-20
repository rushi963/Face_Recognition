"""Raspberry Pi Face Recognition for door unlocking
Copyright 2013 Tony DiCola
"""

import cv2
import config
import face
#import hardware

#for email sending

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from PIL import Image


#for servo motor
import RPi.GPIO as GPIO
import time
import lcd1


#GPIO.setmode(GPIO.BOARD)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False);
GPIO.setup(4,GPIO.OUT)				#Servo PWM

p = GPIO.PWM(4,50)


MATRIX = [[1,2,3,'A'],
     [4,5,6,'B'],
     [7,8,9,'C'],
     ['*',0,'#','D']]

ROW = [14,10,9,11]
COL = [8,25,7,3]

password = '1234'     #with which we will compare

push_button_pin = 15
GPIO.setup(push_button_pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)

def unlockf():
	#p.start(7.5);#unlock
	#time.sleep(0.1);
	#p.stop();
	p.ChangeDutyCycle(2.5);	
	time.sleep(10)
        print_lcd1('locking door')
        time.sleep(1);
        lockf();	

def lockf():
	#p.start(2.5);#lock	
	#time.sleep(0.1);
	#p.stop();
	p.ChangeDutyCycle(7.5);

def sendEmail():
	fromaddr = "ehddaiict@gmail.com"
        toaddr = "sidsinh2011@gmail.com"
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "POSSIBLE INTRUSION : CHECK PHOTO"
        body = "A possible breach in security system. Unauthorized person is trying to enter your home."
        msg.attach(MIMEText(body, 'plain'))
	im = Image.open('capture.pgm')
      	im.convert('RGB').save('capture.jpg','JPEG')
        filename = "capture.jpg"
        attachment = open("/home/pi/ehdproject/pi-facerec-box/capture.jpg", "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)
        #server = smtplib.SMTP('smtp.gmail.com', 587)
        server = smtplib.SMTP_SSL('smtp.gmail.com')
        server.ehlo()
        #server.starttls()
        server.login(fromaddr, "haarorlbp")
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
	

def tryKeypad():

	input = ''
	k=0

	for j in range(4):
		GPIO.setup(COL[j], GPIO.OUT)
    		GPIO.output(COL[j], 1)

	for i in range(4):
    		GPIO.setup(ROW[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

	print_lcd2('');
	try:
    		while(len(input)<4):
			for j in range(4):
            			GPIO.output(COL[j],0)
				for i in range(4):
    					if GPIO.input(ROW[i]) == 0:
       						input += str(MATRIX[i][j])
						print MATRIX[i][j]
       						
						#show * in lcd
						p_str = ""
						
						for k in range(len(input)):
							p_str = p_str + "*";
						print_lcd1(p_str);
																		
						#time.sleep(0.2)
       						while(GPIO.input(ROW[i]) == 0):
       							pass


		    	    	GPIO.output(COL[j],1)

		print input 
    		if(password==input):
			print 'Correct'
    			return True;
		else:
			print 'Cancel'
			return False;
	except KeyboardInterupt:
    		GPIO.cleanup()


def print_lcd1(st):
	lcd1.lcd_string(st,lcd1.LCD_LINE_1,2);

def print_lcd2(st):
	lcd1.lcd_string(st,lcd1.LCD_LINE_2,2);


if __name__ == '__main__':
	

	lcd1.lcd_init();
        
	print_lcd1("Loading training");
	print_lcd2('data');
	# Load training data into model
	print 'Loading training data...'
	model = cv2.createEigenFaceRecognizer()
	model.load(config.TRAINING_FILE)
	print_lcd1('Training model');
	print_lcd2('loaded!');
	time.sleep(2);
	# Initialize camer and box.
	camera = config.get_camera()

	# Move box to locked position.
	p.start(7.5);

	#lock variabel
	lock = 1 
	
	attempt=1; 		# number of current attempt
	
	#confidence sum used for calculating average
	conf_sum = 0;



	print 'Running box...'
	print 'Press button to lock (if unlocked), or unlock if the correct face is detected.'
	print 'Press Ctrl-C to quit.'
	print_lcd1('press button')
	print_lcd2('to capture')
	time.sleep(2);	

	while True:
		
		
		# Check if capture should be made.
		# TODO: Check if button is pressed.
		#input = raw_input()
		push_input = GPIO.input(push_button_pin);
		#if box.is_button_up():
		#if input == 'c':
		if push_input == True:
			#if not box.is_locked:
			if lock==0:
				# Lock the box if it is unlocked
				lock=1
				lockf();
				print 'Box is now locked.'
			else:			
				print 'Button pressed, looking for face...'
				print_lcd1('looking for face')	
				print_lcd2('');
				# Check for the positive face and unlock if found.
				i=0;
				conf_sum = 0;
				while i<1:
					i=i+1;
					image = camera.read()
					# Convert image to grayscale.
					image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
					# Get coordinates of single face in captured image.
					result = face.detect_single(image)
					if result is None:
						print_lcd1('No single face')
						print_lcd2('Try again')
						print 'Could not detect single face!  Check the image in capture.pgm' \
						  ' to see what was captured and try again with only one face visible.'
						i=i-1;
						continue
					x, y, w, h = result
					# Crop and resize image to face.
					crop = face.resize(face.crop(image, x, y, w, h))
					# Test face against model.
					label, confidence = model.predict(crop)
					print_lcd1(str(i) + ' image captured')
					time.sleep(1);			
					print 'Predicted {0} face with confidence {1} (lower is more confident).'.format(
						'POSITIVE' if label == config.POSITIVE_LABEL else 'NEGATIVE', 
					confidence)
					
					conf_sum = conf_sum + confidence;	
		
				conf_avg = conf_sum;

				if label == config.POSITIVE_LABEL and conf_avg < config.POSITIVE_THRESHOLD:
					print 'Recognized face!'
					print_lcd1('Face recognised!')
					print_lcd2('');
					lock = 0
					unlockf();				
					lock=1
					#time.sleep();			#door will be locked when 
					#lock();
				else:
					print 'Did not recognize face!'
					print_lcd1('could not')
					print_lcd2('recognise face')
					#time.sleep(3);
					sendEmail();		
					print 'now try keypad'
					print_lcd1('enter password')
					print_lcd2('in keypad')
					#write code for keypad 
					correctKey = tryKeypad();					
					if correctKey :	
						print_lcd1('correct password')
						print_lcd2('');
						time.sleep(2)
						lock=0;
						unlockf();
						lock=1
					else:
						print 'try once more'
						print_lcd1('wrong password');
						print_lcd2('try once more');
						time.sleep(2);
						correctKey = tryKeypad();
						if correctKey:
							print_lcd1('correct password')
							print_lcd2('')
							time.sleep(2)
							lock = 0;
							unlockf();
							lock=1	
						else:
							print 'Unauthorised person trying to open door';
							print_lcd1('you seem to be')
							print_lcd2('an intruder')	
							time.sleep(2);
							print_lcd1('owner informed')
							print_lcd2('')
							time.sleep(2);
