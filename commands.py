from twisted.protocols import amp

class CommandOne(amp.Command):
	arguments = []
	response = [('offset', amp.Integer()), ('value', amp.Integer()), ('stop', amp.Boolean())]

class LogResults(amp.Command):
	arguments = [('results', amp.String())]
	response = []

class GetOriginalFile(amp.Command):
	arguments = []
	response = [('original_file', amp.String())]

class GetMutationTypes(amp.Command):
	arguments = []
	response = [('mutation_types', amp.AmpList([ ('value',amp.String()), ('offset',amp.Integer()), ('type',amp.String()), ('size',amp.Integer()) ]))]
