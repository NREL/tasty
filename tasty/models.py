import tasty.templates as tt


class Model:
    def __init__(self, ontology):
        self.ontology = ontology
        self.things = []

    def create_from_template(self, template):
        thing = Thing(template)
        self.things.append(thing)


class Thing:
    def __init__(self, template: tt.EntityTemplate):
        pass
