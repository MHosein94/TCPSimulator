from QDWindow import Ui_MainWindow
from QDProperties import Ui_Prp_Window
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog
from TCPMachine import TCPMachine
from Segment import segment
from time import sleep, time
from random import randint
from math import ceil
import sys, os.path

#Global Variables
#Default Values
RTT = 1 #Seconds
chunk_size = 40 #bits
FileName = "Example.png"
data = ['']
chunks = ['']
chunks_bin = ['']
rcvd_data = []
fsm_client = TCPMachine()
fsm_server = TCPMachine()
paused = False #Clicked on Pause button or not
lost = False #Packet hasn't been lost
TCB = []
MaxSeg = 0 #number of sending segment in a pipeline
Height = 900

AllFrames = []
AllAnims = []
AllSeqN = []
AllAckN = []
AllAck = []
AllSyn = []
AllFin = []
init_time = 0

init_seq_client  = 0
init_seq_server  = 1000
seq_client = init_seq_client
seq_server = init_seq_server

Damaged = False

anim_fin = 0
def Fin_Tick():
	global anim_fin
	anim_fin -= 1


def MoveSegment(seg_number,t, dir):
	#Move TCP Segment Vertically
	#t = movement time (in seconds)
	#direction = 'up' or 'down'
	frame = AllFrames[seg_number]
	AllAnims[seg_number] = QtCore.QPropertyAnimation(frame, b"geometry")
	x = frame.x()
	y = frame.y()
	h = frame.height()
	w = frame.width()
	AllAnims[seg_number].setDuration(t*1000)
	AllAnims[seg_number].setStartValue(QtCore.QRect(x, y, w, h))
	AllAnims[seg_number].finished.connect(Fin_Tick)
	if dir == 'down':
		FinalY = Height-300
		AllAnims[seg_number].setEndValue(QtCore.QRect(x, FinalY, w, h))
	elif dir == 'up':
		if seg_number < 16:
			FinalY = 120
		else:
			FinalY = 20
		AllAnims[seg_number].setEndValue(QtCore.QRect(x, FinalY, w, h))
	AllAnims[seg_number].start()


def Browse():
	# Show browse dialog window with clicking on "...""
	global FileName
	fileName = QFileDialog.getOpenFileName(ui_prp, "Choose your data file", "",
		"Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*.*);;Text Files (*.txt)")
	FileName = fileName[0]
	ui_prp.LE_DataAddr.setText(FileName)

def PrpOk():
	#Clicking on "OK" Button in Properties window will run this
	global RTT, chunk_size, data
	RTT = int(ui_prp.LE_RTT.text())
	chunk_size = int(ui_prp.LE_ChunkSize.text())
	try:
		fHandler_read = open(FileName, 'rb')
		data = fHandler_read.read() # each cell: one Byte
		fHandler_read.close()
	except:
		pass

	chunkation(data)
	Prp_Window.close()

def BinRep(chunk):
	# Binary reperesentation of a chunk
	hex_rep = bytes.hex(chunk)
	bin_rep = bin(int(hex_rep, 16))[2:].zfill(8*chunk_size)
	return bin_rep

def chunkation(data):
	# Take the data into smaller pieces
	global chunk_size, chunks, chunks_bin 
	chunk_number = ceil(len(data) / chunk_size)
	chunks = [""] * chunk_number
	chunks_bin = [""] * chunk_number
	for i in range(chunk_number - 1): #last chunk size is not "chunk_size" bytes necessarily!
		chunks[i] = data[chunk_size*i : chunk_size*(i+1)]
		chunks_bin[i] = BinRep(chunks[i])
	
	chunks[chunk_number - 1] = data[chunk_size*(chunk_number - 1):]
	last_size = (len(data) % chunk_size) * 8
	last_hex = bytes.hex(chunks[chunk_number - 1])
	last_bin = bin(int(last_hex,16))[2:].zfill(last_size)
	chunks_bin[chunk_number - 1] = last_bin

def wait_and_check(seg_range_wac):
	global anim_fin
	init_anim_fin = anim_fin
	while(init_anim_fin == anim_fin):
		QtWidgets.QApplication.processEvents()
		current_time = time() - init_time
		ui_mw.lbl_Time_Interval_show.setText(str(current_time))
		if paused == True:
			for i in seg_range_wac:
				AllAnims[i].stop()
				while (paused == True):
					QtWidgets.QApplication.processEvents()


def Start_Transmission():
	# Starting FSM is here!
	global fsm_client, fsm_server, paused, seq_server, seq_client, TCB, lost, init_time, anim_fin, MaxSeg, Damaged
	paused = False
	lost = False

	ui_mw.pb_Start_Trans.setEnabled(False)

	################### Step 1
	#FSM Transition
	client_action = fsm_client.transition('client')
	server_action = fsm_server.transition('server')	
	#Syn packet no. 1
	TCB = []
	MaxSeg = 1
	TCB.append(segment(client_action, init_seq_client, 0, '0'))
	segs = range(0, MaxSeg)
	Fill_segment(TCB, 0)
	anim_fin += 1
	MoveSegment(0, RTT, 'down')
	init_time = time()
	wait_and_check(segs)
	seq_client = seq_client + 1
	while (paused == True):
		QtWidgets.QApplication.processEvents()
	################### Step 2
	#FSM Transition
	server_action = fsm_server.transition('server')	
	#Syn packet no. 2
	TCB = []
	MaxSeg = 1
	TCB.append(segment(server_action, seq_server, seq_client, '0'))
	segs = range(0, MaxSeg)
	Fill_segment(TCB, 0)
	sleep(1)
	anim_fin += 1
	MoveSegment(0, RTT, 'up')
	init_time = time()
	wait_and_check(segs)
	seq_server = seq_server + 1
	while (paused == True):
		QtWidgets.QApplication.processEvents()

	################### Step 3
	#FSM Transition
	client_action = fsm_client.transition('client')	
	#Syn packet no. 3
	TCB = []
	MaxSeg = 1
	TCB.append(segment(client_action, seq_client, seq_server, '0'))
	segs = range(0, MaxSeg)
	Fill_segment(TCB, 0)
	sleep(1)
	anim_fin += 1
	MoveSegment(0, RTT, 'down')
	init_time = time()
	wait_and_check(segs)
	seq_client = seq_client + 1

	while (paused == True):
		QtWidgets.QApplication.processEvents()

	server_action = fsm_server.transition('server')
	ui_mw.lbl_Server_state.setText(fsm_server.get_state())

	#Now Synced
	sleep(1)
	AllFrames[0].move(AllFrames[0].x(), 120)
	if (paused == True):
		return 0

	#######################
	# Now it's time to send data!
	data_length = len(chunks_bin)
	MaxSeg = 1
	sent_data = 0
	while(seq_client - init_seq_client - 2 < data_length and paused == False):

		TCB = []
		segs = range(0, MaxSeg)
		init_time = time()
		damaged_flag = False
		#sending loop
		for k in segs:
			data_i = seq_client - init_seq_client - 2
			TCB.append(segment('data', seq_client, seq_server, chunks_bin[data_i]))
			Fill_segment(TCB, k)
			anim_fin += 1
			sent_data += 1
			MoveSegment(k, RTT, 'down')
			seq_client = seq_client + 1
			if (k != MaxSeg):
				i_t = time()
				c_t = time() - i_t
				while (c_t < RTT/(MaxSeg+5)):
					QtWidgets.QApplication.processEvents()
					c_t = time() - i_t
					current_time = time() - init_time
					ui_mw.lbl_Time_Interval_show.setText(str(current_time))
		#return loop
		init_time = time()
		anim_fin = MaxSeg
		for k in segs:
			wait_and_check(segs)
			Collect_data(k)
			if (Damaged == True):
				Seq_Damaged = seq_client - (MaxSeg - k)
				Seg_Damaged = k
				damaged_flag = True
			TCB.append(segment('data', seq_server, seq_client - (MaxSeg-k), '0'))
			Fill_segment(TCB[MaxSeg:], k)
			MoveSegment(k, RTT, 'up')
			seq_server = seq_server + 1
		anim_fin = MaxSeg
		init_time = time()
		for k in segs:
			wait_and_check(segs)

		tmp_MaxSeg = MaxSeg
		if (damaged_flag == True):
			TCB = []
			for m in range(0,Seg_Damaged):
				TCB.append('')
			MaxSeg = Seg_Damaged
			TCB.append(segment(client_action, Seq_Damaged, seq_server, chunks_bin[Seq_Damaged-2]))
			segs = range(Seg_Damaged-1, Seg_Damaged)
			Fill_segment(TCB, Seg_Damaged)
			sleep(1)
			anim_fin += 1
			MoveSegment(Seg_Damaged, RTT, 'down')
			init_time = time()
			wait_and_check(segs)
			Collect_data(Seg_Damaged)

			TCB = []
			for m in range(0,Seg_Damaged):
				TCB.append('')
			MaxSeg = Seg_Damaged
			TCB.append(segment(client_action, seq_server, Seq_Damaged, '0'))
			segs = range(Seg_Damaged-1, Seg_Damaged)
			Fill_segment(TCB, Seg_Damaged)
			sleep(1)
			anim_fin += 1
			MoveSegment(Seg_Damaged, RTT, 'up')
			init_time = time()
			wait_and_check(segs)

			AllSeqN[Seg_Damaged].setStyleSheet('color: black')
			AllAckN[Seg_Damaged].setStyleSheet('color: black')
			AllAck[Seg_Damaged].setStyleSheet('color: black')
			AllSyn[Seg_Damaged].setStyleSheet('color: black')
			AllFin[Seg_Damaged].setStyleSheet('color: black')
			ui_mw.lbl_Error.hide()
			# Congestion Control
			tmp_MaxSeg /= 4

		MaxSeg = ceil(tmp_MaxSeg)
		MaxSeg = min(MaxSeg*2, data_length - sent_data, 32)
		sleep(1)

	
	while (paused == True):
		QtWidgets.QApplication.processEvents()

	# Closing the connection
	################### Step 1
	#FSM Transition
	client_action = fsm_client.transition('client')	
	#Fin packet no. 1
	TCB = []
	MaxSeg = 1
	TCB.append(segment(client_action, seq_client, seq_server, '0'))
	segs = range(0, MaxSeg)
	Fill_segment(TCB, 0)
	sleep(1)
	anim_fin += 1
	MoveSegment(0, RTT, 'down')
	init_time = time()
	wait_and_check(segs)
	seq_client = seq_client + 1

	while (paused == True):
		QtWidgets.QApplication.processEvents()

	################### Step 2
	#FSM Transition
	server_action = fsm_server.transition('server')	
	#Fin packet no. 2

	TCB = []
	MaxSeg = 1
	TCB.append(segment(server_action, seq_server, seq_client, '0'))
	segs = range(0, MaxSeg)
	Fill_segment(TCB, 0)
	sleep(1)
	anim_fin += 1
	MoveSegment(0, RTT, 'up')
	init_time = time()
	wait_and_check(segs)
	seq_server = seq_server + 1

	while (paused == True):
		QtWidgets.QApplication.processEvents()

	client_action = fsm_client.transition('client')
	ui_mw.lbl_Client_state.setText(fsm_client.get_state())	
	
	sleep(1)
	AllFrames[0].move(AllFrames[0].x(), Height-300)
	while (paused == True):
		QtWidgets.QApplication.processEvents()

	################### Step 3
	#FSM Transition
	server_action = fsm_server.transition('server')	
	#Fin packet no. 3
	TCB = []
	MaxSeg = 1
	TCB.append(segment(server_action, seq_server, seq_client, '0'))
	segs = range(0, MaxSeg)
	Fill_segment(TCB, 0)
	sleep(1)
	anim_fin += 1
	MoveSegment(0, RTT, 'up')
	init_time = time()
	wait_and_check(segs)
	seq_server = seq_server + 1

	while (paused == True):
		QtWidgets.QApplication.processEvents()

	################### Step 4
	#FSM Transition
	client_action = fsm_client.transition('client')	
	#Fin packet no. 4
	TCB = []
	MaxSeg = 1
	TCB.append(segment(client_action, seq_client, seq_server, '0'))
	segs = range(0, MaxSeg)
	Fill_segment(TCB, 0)
	sleep(1)
	anim_fin += 1
	MoveSegment(0, RTT, 'down')
	init_time = time()
	wait_and_check(segs)
	seq_server = seq_server + 1

	while (paused == True):
		QtWidgets.QApplication.processEvents()

	server_action = fsm_server.transition('server')
	ui_mw.lbl_Server_state.setText(fsm_server.get_state())
	#Server is closed

	init_time = time()
	current_time = time() - init_time
	time_wait_and_check = 2.5 * RTT
	ui_mw.lbl_Time_show.show()
	ui_mw.lbl_Timeout.show()
	while (current_time < time_wait_and_check and (paused == False or lost == False)):
		QtWidgets.QApplication.processEvents()
		current_time = time() - init_time
		ui_mw.lbl_Time_show.setText(str(current_time))

	client_action = fsm_client.transition('client')	
	ui_mw.lbl_Client_state.setText(fsm_client.get_state())
	#Client is closed
	SaveAll()

def Fill_segment(tcb, seg_number):
	global AllFrames, AllAnims, AllSeqN, AllAckN, AllSyn, AllAck, AllFin
	ui_mw.lbl_Client_state.setText(fsm_client.get_state())
	ui_mw.lbl_Server_state.setText(fsm_server.get_state())
	AllSeqN[seg_number].setText(str(tcb[seg_number].seq_num))
	AllAckN[seg_number].setText(str(tcb[seg_number].ack_num))
	AllAck[seg_number].setText(tcb[seg_number].ack)
	AllSyn[seg_number].setText(tcb[seg_number].syn)
	AllFin[seg_number].setText(tcb[seg_number].fin)


def Pause():
	global paused
	paused = not paused

def Change_Randomly():
	global TCB
	which_seg = randint(0, MaxSeg-1) # which segment will be changed
	data_changed = TCB[which_seg].data
	l = len(data_changed)
	bit_chng_num = randint(1,l-1) #how many bits will be changed in seq_num
	for i in range(bit_chng_num):
		bit_num = randint(0,l-1) # which bit will be changed in this loop
		data_changed = bin(int(data_changed,2)^(2**bit_num))[2:].zfill(l)
	TCB[which_seg].data = data_changed
	frame = which_seg
	AllSeqN[frame].setStyleSheet('color: red')
	AllAckN[frame].setStyleSheet('color: red')
	AllAck[frame].setStyleSheet('color: red')
	AllSyn[frame].setStyleSheet('color: red')
	AllFin[frame].setStyleSheet('color: red')

def Collect_data(seg_num):
	global rcvd_data, seq_nums_list, seq_client, lost, Damaged
	
	seq_rcvd = TCB[seg_num].seq_num - 2
	data_rcvd = TCB[seg_num].data
	chk_sum = TCB[seg_num].checksum
	chk_calced = CheckSum_func(data_rcvd)
	if (chk_calced - chk_sum) != 0:
		Damaged = True
	else:
		Damaged = False

	rcvd_data.append(data_rcvd)
	if (Damaged == False and seq_rcvd < len(rcvd_data)): #this is a new segment
		rcvd_data[seq_rcvd] = data_rcvd
	elif (Damaged == True and lost == False):
		ui_mw.lbl_Error.show()

def Lose_Packet():
	global lost
	lost = True

def CheckSum_func(data):
	sumn = 0
	datalen = len(data)
	data_list_num = int(datalen/16)
	data_list = [0]*data_list_num
	for i in range(data_list_num):
		data_list[i] = data[16*i:16*(i+1)]
	for data_16b in data_list:
		p = int(data_16b, 2)
		sumn = sumn + p
	sumn = sumn%(2**16)
	chk = ((sumn ^ 0xFFFF) + 1)
	return chk

def Exit_App():
	sys.exit()

def SaveAll():
	global rcvd_data
	received_data = ''
	for d in rcvd_data:
		received_data += d

	try:
		hexed = hex(int(received_data,2))[2:]
		received_data = bytes.fromhex(hexed)

		NewFileName = os.path.splitext(FileName)[0] + "_Transimtted"
		File_Extenstion = os.path.splitext(FileName)[1]
		fHandler_write = open(NewFileName + File_Extenstion, 'wb')
		fHandler_write.write(received_data)
		fHandler_write.close()

		ui_mw.pb_Start_Trans.setEnabled(True)
		#resetting
	except:
		print('Nothing is here!')

def Fill_Arrays():
	global AllFrames, AllAnims, AllSeqN, AllAckN, AllSyn, AllAck, AllFin
	AllFrames = [ui_mw.SegmentFrame_1, ui_mw.SegmentFrame_2, ui_mw.SegmentFrame_3, ui_mw.SegmentFrame_4, ui_mw.SegmentFrame_5, ui_mw.SegmentFrame_6, 
	ui_mw.SegmentFrame_7, ui_mw.SegmentFrame_8, ui_mw.SegmentFrame_9, ui_mw.SegmentFrame_10, ui_mw.SegmentFrame_11, ui_mw.SegmentFrame_12, 
	ui_mw.SegmentFrame_13, ui_mw.SegmentFrame_14, ui_mw.SegmentFrame_15, ui_mw.SegmentFrame_16, ui_mw.SegmentFrame_17, ui_mw.SegmentFrame_18,
	ui_mw.SegmentFrame_19, ui_mw.SegmentFrame_20, ui_mw.SegmentFrame_21, ui_mw.SegmentFrame_22, ui_mw.SegmentFrame_23, ui_mw.SegmentFrame_24, 
	ui_mw.SegmentFrame_25, ui_mw.SegmentFrame_26, ui_mw.SegmentFrame_27, ui_mw.SegmentFrame_28, ui_mw.SegmentFrame_29, ui_mw.SegmentFrame_30,
	ui_mw.SegmentFrame_31, ui_mw.SegmentFrame_32]

	ui_mw.anim1 = ui_mw.anim2 = ui_mw.anim3 = ui_mw.anim4 = ui_mw.anim5 = ui_mw.anim6 = ui_mw.anim7 = ui_mw.anim8 = [QtCore.QPropertyAnimation()]*8
	ui_mw.anim9 = ui_mw.anim10 = ui_mw.anim11 = ui_mw.anim12 = ui_mw.anim13 = ui_mw.anim14 = ui_mw.anim15 = ui_mw.anim16 = [QtCore.QPropertyAnimation()]*8
	ui_mw.anim17 = ui_mw.anim18 = ui_mw.anim19 = ui_mw.anim20 = ui_mw.anim21 = ui_mw.anim22 = ui_mw.anim23 = ui_mw.anim24 = [QtCore.QPropertyAnimation()]*8
	ui_mw.anim25 = ui_mw.anim26 = ui_mw.anim27 = ui_mw.anim28 = ui_mw.anim29 = ui_mw.anim30 = ui_mw.anim31 = ui_mw.anim32 = [QtCore.QPropertyAnimation()]*8

	AllAnims = [ui_mw.anim1, ui_mw.anim2, ui_mw.anim3, ui_mw.anim4, ui_mw.anim5, ui_mw.anim6, ui_mw.anim7, ui_mw.anim8, 
	ui_mw.anim9, ui_mw.anim10, ui_mw.anim11, ui_mw.anim12, ui_mw.anim13, ui_mw.anim14, ui_mw.anim15, ui_mw.anim16, ui_mw.anim17, 
	ui_mw.anim18, ui_mw.anim19, ui_mw.anim20, ui_mw.anim21, ui_mw.anim22, ui_mw.anim23, ui_mw.anim24, ui_mw.anim25, ui_mw.anim26, 
	ui_mw.anim27, ui_mw.anim28, ui_mw.anim29, ui_mw.anim30, ui_mw.anim31, ui_mw.anim32]

	AllSeqN = [ui_mw.lbl_seqN_1, ui_mw.lbl_seqN_2, ui_mw.lbl_seqN_3, ui_mw.lbl_seqN_4, ui_mw.lbl_seqN_5, ui_mw.lbl_seqN_6, ui_mw.lbl_seqN_7, 
	ui_mw.lbl_seqN_8, ui_mw.lbl_seqN_9, ui_mw.lbl_seqN_10, ui_mw.lbl_seqN_11, ui_mw.lbl_seqN_12, ui_mw.lbl_seqN_13, ui_mw.lbl_seqN_14, 
	ui_mw.lbl_seqN_15, ui_mw.lbl_seqN_16, ui_mw.lbl_seqN_17, ui_mw.lbl_seqN_18, ui_mw.lbl_seqN_19, ui_mw.lbl_seqN_20, ui_mw.lbl_seqN_21, 
	ui_mw.lbl_seqN_22, ui_mw.lbl_seqN_23, ui_mw.lbl_seqN_24, ui_mw.lbl_seqN_25, ui_mw.lbl_seqN_26, ui_mw.lbl_seqN_27, ui_mw.lbl_seqN_28, 
	ui_mw.lbl_seqN_29, ui_mw.lbl_seqN_30, ui_mw.lbl_seqN_31, ui_mw.lbl_seqN_32]

	AllAckN = [ui_mw.lbl_AckN_1, ui_mw.lbl_AckN_2, ui_mw.lbl_AckN_3, ui_mw.lbl_AckN_4, ui_mw.lbl_AckN_5, ui_mw.lbl_AckN_6, ui_mw.lbl_AckN_7, 
	ui_mw.lbl_AckN_8, ui_mw.lbl_AckN_9, ui_mw.lbl_AckN_10, ui_mw.lbl_AckN_11, ui_mw.lbl_AckN_12, ui_mw.lbl_AckN_13, ui_mw.lbl_AckN_14, 
	ui_mw.lbl_AckN_15, ui_mw.lbl_AckN_16, ui_mw.lbl_AckN_17, ui_mw.lbl_AckN_18, ui_mw.lbl_AckN_19, ui_mw.lbl_AckN_20, ui_mw.lbl_AckN_21, 
	ui_mw.lbl_AckN_22, ui_mw.lbl_AckN_23, ui_mw.lbl_AckN_24, ui_mw.lbl_AckN_25, ui_mw.lbl_AckN_26, ui_mw.lbl_AckN_27, ui_mw.lbl_AckN_28, 
	ui_mw.lbl_AckN_29, ui_mw.lbl_AckN_30, ui_mw.lbl_AckN_31, ui_mw.lbl_AckN_32]

	AllAck = [ui_mw.lbl_ACK_1, ui_mw.lbl_ACK_2, ui_mw.lbl_ACK_3, ui_mw.lbl_ACK_4, ui_mw.lbl_ACK_5, ui_mw.lbl_ACK_6, ui_mw.lbl_ACK_7, 
	ui_mw.lbl_ACK_8, ui_mw.lbl_ACK_9, ui_mw.lbl_ACK_10, ui_mw.lbl_ACK_11, ui_mw.lbl_ACK_12, ui_mw.lbl_ACK_13, ui_mw.lbl_ACK_14, 
	ui_mw.lbl_ACK_15, ui_mw.lbl_ACK_16, ui_mw.lbl_ACK_17, ui_mw.lbl_ACK_18, ui_mw.lbl_ACK_19, ui_mw.lbl_ACK_20, ui_mw.lbl_ACK_21, 
	ui_mw.lbl_ACK_22, ui_mw.lbl_ACK_23, ui_mw.lbl_ACK_24, ui_mw.lbl_ACK_25, ui_mw.lbl_ACK_26, ui_mw.lbl_ACK_27, ui_mw.lbl_ACK_28, 
	ui_mw.lbl_ACK_29, ui_mw.lbl_ACK_30, ui_mw.lbl_ACK_31, ui_mw.lbl_ACK_32]

	AllSyn = [ui_mw.lbl_SYN_1, ui_mw.lbl_SYN_2, ui_mw.lbl_SYN_3, ui_mw.lbl_SYN_4, ui_mw.lbl_SYN_5, ui_mw.lbl_SYN_6, ui_mw.lbl_SYN_7, 
	ui_mw.lbl_SYN_8, ui_mw.lbl_SYN_9, ui_mw.lbl_SYN_10, ui_mw.lbl_SYN_11, ui_mw.lbl_SYN_12, ui_mw.lbl_SYN_13, ui_mw.lbl_SYN_14, 
	ui_mw.lbl_SYN_15, ui_mw.lbl_SYN_16, ui_mw.lbl_SYN_17, ui_mw.lbl_SYN_18, ui_mw.lbl_SYN_19, ui_mw.lbl_SYN_20, ui_mw.lbl_SYN_21, 
	ui_mw.lbl_SYN_22, ui_mw.lbl_SYN_23, ui_mw.lbl_SYN_24, ui_mw.lbl_SYN_25, ui_mw.lbl_SYN_26, ui_mw.lbl_SYN_27, ui_mw.lbl_SYN_28, 
	ui_mw.lbl_SYN_29, ui_mw.lbl_SYN_30, ui_mw.lbl_SYN_31, ui_mw.lbl_SYN_32]

	AllFin = [ui_mw.lbl_FIN_1, ui_mw.lbl_FIN_2, ui_mw.lbl_FIN_3, ui_mw.lbl_FIN_4, ui_mw.lbl_FIN_5, ui_mw.lbl_FIN_6, ui_mw.lbl_FIN_7, 
	ui_mw.lbl_FIN_8, ui_mw.lbl_FIN_9, ui_mw.lbl_FIN_10, ui_mw.lbl_FIN_11, ui_mw.lbl_FIN_12, ui_mw.lbl_FIN_13, ui_mw.lbl_FIN_14, 
	ui_mw.lbl_FIN_15, ui_mw.lbl_FIN_16, ui_mw.lbl_FIN_17, ui_mw.lbl_FIN_18, ui_mw.lbl_FIN_19, ui_mw.lbl_FIN_20, ui_mw.lbl_FIN_21, 
	ui_mw.lbl_FIN_22, ui_mw.lbl_FIN_23, ui_mw.lbl_FIN_24, ui_mw.lbl_FIN_25, ui_mw.lbl_FIN_26, ui_mw.lbl_FIN_27, ui_mw.lbl_FIN_28, 
	ui_mw.lbl_FIN_29, ui_mw.lbl_FIN_30, ui_mw.lbl_FIN_31, ui_mw.lbl_FIN_32]


if __name__ == "__main__":

	#Show Properties Window
	app_prp = QtWidgets.QApplication(sys.argv)
	Prp_Window = QtWidgets.QMainWindow()
	ui_prp = Ui_Prp_Window()
	ui_prp.setupUi(Prp_Window)
	Prp_Window.show()
	################################################
	################ Functinalities ################
	################################################
	ui_prp.Btn_Browse.clicked.connect(Browse)
	ui_prp.PB_OK.clicked.connect(PrpOk)
	ui_prp.LE_ChunkSize.setText(str(chunk_size))
	ui_prp.LE_RTT.setText(str(RTT))
	ui_prp.LE_DataAddr.setText(FileName)

	##############################################
	#Run
	app_prp.exec_()

	###############################################################################################################################
	################ Start Program ##############
	#Show Main Window
	app_mw = QtWidgets.QApplication(sys.argv)
	MainWindow = QtWidgets.QMainWindow()
	ui_mw = Ui_MainWindow()
	ui_mw.setupUi(MainWindow)
	MainWindow.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint|QtCore.Qt.WindowCloseButtonHint)
	MainWindow.show()

	Fill_Arrays()
	##############################################
	################ Functinalities ##############
	##############################################
	ui_mw.actionStart_Transmission.triggered.connect(Start_Transmission)
	ui_mw.pb_Start_Trans.clicked.connect(Start_Transmission)
	ui_mw.actionPause.triggered.connect(Pause)
	ui_mw.pb_Pause.clicked.connect(Pause)
	ui_mw.actionCorrupt.triggered.connect(Change_Randomly)
	ui_mw.pb_Corrupt.clicked.connect(Change_Randomly)
	ui_mw.actionExit_2.triggered.connect(Exit_App)
	ui_mw.pb_Exit.clicked.connect(Exit_App)

	ui_mw.lbl_Time_show.hide()
	ui_mw.lbl_Timeout.hide()
	ui_mw.lbl_Error.hide()
	ui_mw.lbl_Lost.hide()

	ui_mw.lbl_Client_state.setText(fsm_client.get_state())
	ui_mw.lbl_Server_state.setText(fsm_server.get_state())

	##############################################
	#Run

	sys.exit(app_mw.exec_())