class FSM():
	def __init__(self):
		self.states = []
		self.current_state = ''

	def def_states(self, state_list):
		self.states = state_list

	def set_state(self, state):
		self.current_state = state

	def get_state(self):
		return self.current_state

	def reset_state(self):
		self.current_state = self.states[0]