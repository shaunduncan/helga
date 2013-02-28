import random
import re

from helga.extensions.base import ContextualExtension


class LOLJavaExtension(ContextualExtension):

    context = r'(lol)?java(?!script)'
    allow_many = False
    response_fmt = '%(response)s'

    descriptors = (
        'Abstract',
        'Base',
        'Lazy',
        'Mutable',
        'Composite',
        'Recursive',
        'Asynchronous',
        'Shared',
        'Runnable',
        'Secure',
        'Generic',
        'Internal',
        'External',
        'Prioritized',
    )

    frameworks = (
        'Swing',
        'Hibernate',
        'JDBC',
        'Spring',
        'Struts',
        'Android',
        'AWT',

        # Give some weight
        '',
        '',
        '',
        '',
    )

    things = (
        'Printer',
        'Internet',
        'Synergy',
        'IRC',
        'Window',
        'Network',
        'TCP',
        'Protocol',
        'Data',
        'Web',
        'Script',
        'Command',
        'Television',
        'UML',
        'Null',
        'Scheduler',
        'Bandwidth',
        'Bot',
        'Computation',
        'Event'
        'Color',
        'Font',
        'Logger',
        'Hash',
        'SOAP',
        'XML',
        'JSON',
        'HTTP',
        'REST',
        'Layout',
        'Cache',
        'List',
        'Enum',
        'Device',
        'Statement',
        'Memory',
        'Timestamp',
        'Graph',
        'Result',
        'Grid',
        'Category',
        'Story',
        'Article',
        'Model',
        'Tokenizer',
    )

    actions = (
        'Extraction',
        'Mutation',
        'Automation',
        'Interpolation',
        'Instantiation',
        'Translation',
        'Iteration',

        # Give some weight
        '',
        '',
        '',
        '',
    )

    oop = (
        'Thread',
        'Bean',
        'Command',
        'Prototype',
        'Factory',
        'Builder',
        'Singleton',
        'Client',
        'Exception',
        'Error',
        'Pool',
        'Decorator',
        'Controller',
        'Proxy',
        'Module',
        'Adapter',
        'Bridge',
        'Wrapper',
        'Iterator',
        'Observer',
        'Interpreter',
        'Applet',
        'Action',
        'Map',
        'Queue',
        'Configuration',
        'Encoder',
        'Tokenizer',
    )

    def make_bullshit_java_thing(self):
        # This method isn't really needed, but I like the name
        return (random.choice(self.descriptors) +
                random.choice(self.frameworks) +
                random.choice(self.things + self.oop) +
                random.choice(self.actions) +
                random.choice(self.oop))

    def transform_match(self, *args):
        return self.make_bullshit_java_thing()
