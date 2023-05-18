from FSM import FSM
class TCPMachine(FSM):
	def __init__(self):
		self.def_states(['Closed', 'Listen', 'Syn_sent', 'Syn_rcvd', 'Established', 'Close_wait', 'Last_ack', 'Fin_wait1', 'Fin_wait2', 'Closing', 'Time_wait'])
		self.reset_state()

	def transition(self, side):
		Action = ''
		st = self.get_state()
		if side == 'client':
			if st == 'Closed':
				Action = 'syn'
				self.set_state('Syn_sent')

			elif st == 'Syn_sent':
				Action = 'synced'
				self.set_state('Established')

			elif st == 'Established':
				Action = 'fin_client'
				self.set_state('Fin_wait1')

			elif st == 'Fin_wait1':
				Action = ''
				self.set_state('Fin_wait2')

			elif st == 'Fin_wait2':
				Action = 'fin_ack_client'
				self.set_state('Time_wait')

			elif st == 'Time_wait':
				Action = ''
				self.set_state('Closed')

		elif side == 'server':
			if st == 'Closed':
				Action = ''
				self.set_state('Listen')

			elif st == 'Listen':
				Action = 'syn_ack'
				self.set_state('Syn_rcvd')

			elif st == 'Syn_rcvd':
				Action = ''
				self.set_state('Established')

			elif st == 'Established':
				Action = 'fin_ack_server'
				self.set_state('Close_wait')

			elif st == 'Close_wait':
				Action = 'fin_server'
				self.set_state('Last_ack')

			elif st == 'Last_ack':
				Action = ''
				self.set_state('Closed')
		return Action