class Project(object):
    def __init__(self, id, name, address_line_1, city, state, zip, created_on, estimator, tech, passedSteps):
        self.id = id
        self.name = name
        self.address_line_1 = address_line_1
        self.city = city
        self.state = state
        self.zip = zip
        self.created_on = created_on
        self.estimator = estimator
        self.tech = tech
        self.passedSteps = passedSteps
