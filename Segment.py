class segment():
    def __init__(self, seg_name = '', seq_num = 0, ack_num = 0, chunk = 0):
        self.header_length = bin(5)[2:].zfill(4) #4-bit binary representation of 5
        self.urg =  '0'
        self.psh = '0'
        self.rst = '0'
        self.reserved = '0'.zfill(6)
        self.urgent_pointer = '0'.zfill(16)

        if seg_name == 'syn':
            self.syn = '1'
            self.seq_num = seq_num
            self.ack_num = ack_num
            self.ack = '0'
            self.rcv_wnd = '0'
            self.data = chunk
            self.fin = '0'
            self.checksum  = self.CheckSum_func()
            
        elif seg_name == 'syn_ack':
            self.syn = '1'
            self.seq_num = seq_num
            self.ack_num = ack_num
            self.ack = '1'
            self.rcv_wnd = '0'
            self.data = chunk
            self.fin = '0'
            self.checksum  = self.CheckSum_func()

        elif seg_name == 'synced':
            self.syn = '0'
            self.seq_num = seq_num
            self.ack_num = ack_num
            self.ack = '1'
            self.rcv_wnd = '0'
            self.data = chunk
            self.fin = '0'
            self.checksum  = self.CheckSum_func()

        elif seg_name == 'fin_client':
            self.syn = '0'
            self.seq_num = seq_num
            self.ack_num = ack_num
            self.ack = '0'
            self.rcv_wnd = '0'
            self.data = chunk
            self.fin = '1'
            self.checksum  = self.CheckSum_func()

        elif seg_name == 'fin_ack_server':
            self.syn = '0'
            self.seq_num = seq_num
            self.ack_num = ack_num
            self.ack = '1'
            self.rcv_wnd = '0'
            self.data = chunk
            self.fin = '0'
            self.checksum  = self.CheckSum_func()

        elif seg_name == 'fin_server':
            self.syn = '0'
            self.seq_num = seq_num
            self.ack_num = ack_num
            self.ack = '0'
            self.rcv_wnd = '0'
            self.data = chunk
            self.fin = '1'
            self.checksum  = self.CheckSum_func()

        elif seg_name == 'fin_ack_client':
            self.syn = '0'
            self.seq_num = seq_num
            self.ack_num = ack_num
            self.ack = '1'
            self.rcv_wnd = '0'
            self.data = chunk
            self.fin = '0'
            self.checksum  = self.CheckSum_func()

        elif seg_name == 'data':
            self.syn = '0'
            self.seq_num = seq_num
            self.ack_num = ack_num
            self.ack = '1'
            self.rcv_wnd = '0'
            self.data = chunk
            self.fin = '0'
            self.checksum = self.CheckSum_func()
            

    def CheckSum_func(self):
        sumn  = 0
        datalen  = len(self.data)
        data_list_num = int(datalen/16)
        data_list = [0]*data_list_num
        for i in range(data_list_num):
            data_list[i]  = self.data[16*i:16*(i+1)]
        for data_16b in data_list:
            p  = int(data_16b,2)
            sumn  = sumn + p
        sumn  = sumn%(2**16) # seprate last 16 bits
        chk  = ((sumn ^ 0xFFFF) + 1) # Two's Comlpement of sumn
        return chk

    






    
