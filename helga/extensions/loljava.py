import random
import re

from helga.extensions.base import HelgaExtension


class LOLJavaExtension(HelgaExtension):

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
        return (random.choice(self.descriptors) +
                random.choice(self.frameworks) +
                random.choice(self.things + self.oop) +
                random.choice(self.actions) +
                random.choice(self.oop))

    def dispatch(self, nick, channel, message, is_public):
        if re.match(r'(^|.+)(lol)?java($|[^s]+)', message, re.I):
            return self.make_bullshit_java_thing()
