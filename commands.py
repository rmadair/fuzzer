from twisted.protocols import amp

class GetNextMutation(amp.Command):
	arguments = []
	response = [('offset', amp.Integer()), ('mutation_index', amp.Integer()), ('stop', amp.Boolean())]

class LogResults(amp.Command):
	arguments = [('results', amp.String())]
	response = []

class GetOriginalFile(amp.Command):
	arguments = []
	response = [('original_file', amp.String()), ('original_file_name', amp.String())]

class GetProgram(amp.Command):
	arguments = []
	response = [('program', amp.String())]

class GetMutationTypes(amp.Command):
	arguments = []
	response = [('mutation_types', amp.AmpList([ ('value',amp.String()), ('type',amp.String()), ('size',amp.Integer()) ]))]
